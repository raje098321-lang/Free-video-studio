# Free Video Studio — Start Here (Android)

This project is a starter, not a live website yet. You do not need to understand the code to follow the plan.

## The simplest path

1. **Try a free video model first:** open https://huggingface.co/spaces?category=video-generation
   and choose a Space marked as running. Try one short clip. Community Spaces can be busy, change, or stop.
2. **Keep the website itself free:** use Cloudflare Pages for the static website: https://pages.cloudflare.com/
3. **For user accounts and monthly limits later:** use Supabase Free: https://supabase.com/pricing
4. **For AI generation:** connect a model provider only after testing its API and quota. The starter's provider adapter is not plug-and-play because each Hugging Face Space has its own input/output API.
5. **Do not publish this prototype as a public paid generator yet.** It currently uses demo quota logic and needs real sign-in, persistent quota records, secure job/file storage, provider integration, and verified ad completion before public launch.

## What to do right now

Open the Hugging Face video Spaces page in step 1 and test one short generation. This confirms which free model is actually available on your account today.

## What the website is designed to do

- Create a story plan up to 4 minutes.
- Break it into short scenes.
- Send one scene at a time to a configured provider.
- Try another configured provider if the first one fails.
- Assemble compatible clips into one MP4 after a real video file is returned.

**A 4-minute project is a sequence of short clips, not a single free 4-minute AI generation.**

## Both creation modes
The website interface now offers:
- Text to video: describe the scene.
- Image to video: upload a picture and describe its motion.

Image-to-video only works with a model that accepts image input. The upload route is included, but the chosen Space's exact API still needs to be matched.
