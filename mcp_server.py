"""Optional MCP tools example. Install mcp and adapt/deploy over HTTPS to connect to ChatGPT."""
from mcp.server.fastmcp import FastMCP
import requests, os
mcp=FastMCP("Free Video Studio")
API=os.getenv("VIDEO_STUDIO_API","http://localhost:8000")

@mcp.tool()
def plan_video(prompt:str, duration_seconds:int=60, scene_seconds:int=5)->dict:
    """Create a scene plan for a video up to four minutes."""
    r=requests.post(API+"/api/plan",json={"prompt":prompt,"duration_seconds":duration_seconds,"scene_seconds":scene_seconds},timeout=30)
    r.raise_for_status(); return r.json()

@mcp.tool()
def start_video_generation(prompt:str)->dict:
    """Submit one short clip to the configured provider with automatic provider fallback."""
    r=requests.post(API+"/api/generate",json={"prompt":prompt},timeout=180)
    r.raise_for_status(); return r.json()

if __name__=="__main__":
    mcp.run()
