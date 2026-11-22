# Free Video Studio — free-first starter

This is a mobile-friendly starter for a video prompt planner and provider-connected video workflow. It is not a hosted, fully configured generator yet.

## First
Read `START_HERE_ANDROID.md` before touching the code.

## Included\n- Text-to-video and image-to-video choices\n- Image upload endpoint (requires a compatible image-input model and its API mapping)
- Mobile-friendly prompt UI
- 4-minute project planner (short scenes)
- Provider fallback scaffold for configured Hugging Face/Gradio Spaces
- FastAPI backend
- Quota and rewarded-ad integration scaffolds
- FFmpeg assembly endpoint scaffold
- PWA shell

## Honest limitations
The provider adapter assumes a generic prompt-only Gradio API; many video Spaces need different inputs and return different file formats. Configure and test the exact Space API. The current demo quota uses a demo user and is not suitable for public deployment. Rewarded ads are disabled until a real ad provider and server-side verification are implemented. Add authentication, persistent per-user quota, secure storage, job queue, rate limits and provider budget controls before public launch.

Read `FREE_STACK_AND_REAL_LIMITS.md` for the recommended free hosting stack and realistic quota policy.
