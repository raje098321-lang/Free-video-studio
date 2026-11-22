import os, uuid, subprocess, tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from providers import configured_providers, generate_with_fallback
from quota import status as quota_status, consume_credit
from rewarded_ads import reward_provider_status, verify_completion

app=FastAPI(title="Free Video Studio API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
JOBS={}

class PlanRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=5000)
    duration_seconds: int = Field(default=30, ge=5, le=240)
    scene_seconds: int = Field(default=5, ge=5, le=10)

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=5000)

@app.get("/")
def root():
    return {"app":"Free Video Studio","status":"starter","configured_providers":len(configured_providers())}

@app.get("/api/quota")
def quota():
    return quota_status("demo-user")

@app.get("/api/rewarded-ads")
def rewarded_ads():
    return reward_provider_status()

@app.post("/api/rewarded-ads/verify")
def rewarded_ads_verify(body: dict):
    return verify_completion(body)

@app.get("/api/providers")
def providers():
    return {"providers":[{"name":p["name"],"configured":True} for p in configured_providers()]}

@app.post("/api/plan")
def plan(req: PlanRequest):
    count=(req.duration_seconds + req.scene_seconds - 1)//req.scene_seconds
    scenes=[]
    for i in range(count):
        scenes.append({"scene":i+1,"duration_seconds":min(req.scene_seconds,req.duration_seconds-i*req.scene_seconds),
                      "prompt":f'{req.prompt}. Scene {i+1} of {count}; cinematic composition, coherent visual style, no text overlay.'})
    return {"duration_seconds":req.duration_seconds,"scene_count":count,"scenes":scenes,
            "note":"A 4-minute output is assembled from short clips; provider limits may require generation over multiple sessions."}

@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        credit_type=consume_credit("demo-user")
    except ValueError as exc:
        raise HTTPException(429, detail=str(exc))
    job_id=str(uuid.uuid4())
    JOBS[job_id]={"status":"running","prompt":req.prompt,"credit_type":credit_type}
    try:
        result=generate_with_fallback(req.prompt)
        JOBS[job_id]={"status":"completed","provider":result["provider"],"output":str(result["output"]),"credit_type":credit_type}
        return {"job_id":job_id,**JOBS[job_id],"quota":quota_status("demo-user")}
    except Exception as exc:
        JOBS[job_id]={"status":"failed","error":str(exc),"credit_type":credit_type}
        raise HTTPException(503, detail=str(exc))

@app.post("/api/generate-image")
async def generate_image(prompt: str = Form(...), image: UploadFile = File(...)):
    """Image-to-video upload route; the selected model must support image input."""
    if image.content_type not in ("image/png", "image/jpeg", "image/webp"):
        raise HTTPException(400, "Upload a PNG, JPEG, or WEBP image.")
    suffix={"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}[image.content_type]
    temp=Path(tempfile.mkdtemp(prefix="fvs-image-"))
    image_path=temp/("reference"+suffix)
    image_path.write_bytes(await image.read())
    try:
        credit_type=consume_credit("demo-user")
    except ValueError as exc:
        raise HTTPException(429, detail=str(exc))
    try:
        result=generate_with_fallback(prompt, str(image_path))
        return {"status":"completed","provider":result["provider"],"output":str(result["output"]),
                "mode":"image-to-video","quota":quota_status("demo-user")}
    except Exception as exc:
        raise HTTPException(503, detail=str(exc))

@app.get("/api/jobs/{job_id}")
def get_job(job_id:str):
    if job_id not in JOBS: raise HTTPException(404,"Unknown job")
    return {"job_id":job_id,**JOBS[job_id]}

@app.post("/api/assemble")
def assemble(body: dict):
    clips=body.get("clips",[])
    if not clips: raise HTTPException(400,"clips is required")
    for clip in clips:
        if not os.path.isfile(clip): raise HTTPException(400,f"Missing clip: {clip}")
    out_dir=Path(tempfile.mkdtemp(prefix="fvs-"))
    listfile=out_dir/"concat.txt"
    with listfile.open("w",encoding="utf-8") as f:
        for clip in clips:
            safe_path=os.path.abspath(clip).replace("'","'\\''")
            f.write("file '"+safe_path+"'\\n")
    output=out_dir/"final.mp4"
    try:
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(listfile),"-c","copy",str(output)],
                       check=True,capture_output=True,text=True,timeout=180)
    except Exception:
        raise HTTPException(500,"FFmpeg assembly failed. Check that clips have compatible codecs and dimensions.")
    return {"status":"assembled","file":str(output),"note":"Add secure download/storage handling before public deployment."}
