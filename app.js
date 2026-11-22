const $=id=>document.getElementById(id);
function api(){return $("api").value.trim().replace(/\\/$/,"")}
$("plan").onclick=async()=>{
 const prompt=$("prompt").value.trim(); if(!prompt){$("status").textContent="Enter a prompt first.";return}
 $("status").textContent="Planning scenes…";
 try{
  const r=await fetch(api()+"/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt,duration_seconds:+$("duration").value,scene_seconds:+$("scene").value})});
  const data=await r.json();if(!r.ok)throw Error(data.detail||"Plan failed");
  $("count").textContent=`${data.scene_count} scenes • ${data.duration_seconds}s`;
  $("scenes").innerHTML=data.scenes.map(s=>`<article class="scene"><strong>Scene ${s.scene} · ${s.duration_seconds}s</strong><p>${escapeHtml(s.prompt)}</p></article>`).join("");
  $("status").textContent=data.note;
 }catch(e){$("status").textContent="Could not reach backend: "+e.message}
};
function currentMode(){return document.querySelector('input[name="mode"]:checked').value}
document.querySelectorAll('input[name="mode"]').forEach(el=>el.addEventListener("change",()=>{
 $("image-upload").hidden=currentMode()!=="image";
}));
$("generate").onclick=async()=>{
 const prompt=$("prompt").value.trim();if(!prompt){$("status").textContent="Enter a prompt first.";return}
 const mode=currentMode();
 if(mode==="image"&&!$("image").files[0]){$("status").textContent="Choose a picture first.";return}
 $("status").textContent="Submitting test clip…";
 try{
  let r;
  if(mode==="image"){
   const form=new FormData();form.append("prompt",prompt);form.append("image",$("image").files[0]);
   r=await fetch(api()+"/api/generate-image",{method:"POST",body:form});
  }else{
   r=await fetch(api()+"/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt})});
  }
  const d=await r.json();if(!r.ok)throw Error(d.detail||"Generation failed");
  $("status").textContent=`Generation ${d.status} via ${d.provider}. Result: ${d.output}`;
 }catch(e){$("status").textContent="Generation unavailable: "+e.message}
};
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}

async function loadQuota(){
 try{
  const r=await fetch(api()+"/api/quota");const q=await r.json();
  $("credits").textContent=`${q.credits} ad credits • ${q.free_credits_remaining} free`;
  $("quota-note").textContent=`Rewarded ads remaining today: ${q.rewarded_ads_remaining_today}. Each credit is ${q.seconds_per_credit}s of scene request.`;
  const ads=await fetch(api()+"/api/rewarded-ads").then(x=>x.json());
  $("reward").disabled=!ads.ready;
  $("reward").textContent=ads.ready?"Watch ad for 1 scene credit":"Rewarded ads not configured";
 }catch(e){$("credits").textContent="Backend offline"}
}
$("reward").onclick=()=>{$("status").textContent="Rewarded ad provider and server-side verification must be configured before credits can be granted."};
$("api").addEventListener("change",loadQuota);loadQuota();
