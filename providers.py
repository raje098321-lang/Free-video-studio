
import os
import time
import base64
import mimetypes
from pathlib import Path

import requests
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

AGNES_BASE_URL = os.getenv(
    "AGNES_BASE_URL",
    "https://apihub.agnes-ai.com"
).rstrip("/")


def configured_providers():
    providers = []

    # Agnes AI video provider
    if os.getenv("AGNES_API_KEY", "").strip():
        providers.append({
            "kind": "agnes",
            "name": "Agnes AI Video",
            "model": os.getenv(
                "AGNES_VIDEO_MODEL",
                "agnes-video-2.5-flash"
            ),
        })

    # Optional Gradio / Hugging Face providers
    for i in range(1, 10):
        url = os.getenv(f"PROVIDER_{i}_URL", "").strip()
        enabled = (
            os.getenv(
                f"PROVIDER_{i}_ENABLED",
                "false"
            ).lower() == "true"
        )

        if url and enabled:
            providers.append({
                "kind": "gradio",
                "name": os.getenv(
                    f"PROVIDER_{i}_NAME",
                    f"Provider {i}"
                ),
                "url": url,
                "api_name": os.getenv(
                    f"PROVIDER_{i}_API_NAME",
                    "/generate"
                ),
            })

    return providers


def call_agnes(provider, prompt, image_path=None):
    api_key = os.getenv("AGNES_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("AGNES_API_KEY is missing.")

    model = provider["model"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Agnes Video 2.5 Flash settings
    payload = {
        "model": model,
        "prompt": prompt,
        "mode": "text",
        "seconds": os.getenv("AGNES_VIDEO_SECONDS", "5"),
        "size": "720P",
        "aspect_ratio": "9:16",
    }

    # Image-to-video input
    if image_path:
        path = Path(image_path)

        mime = mimetypes.guess_type(path.name)[0]
        if not mime:
            mime = "image/jpeg"

        encoded = base64.b64encode(
            path.read_bytes()
        ).decode("ascii")

        payload["mode"] = "img2video"
        payload["first_frame"] = (
            f"data:{mime};base64,{encoded}"
        )

    # Create video generation task
    response = requests.post(
        f"{AGNES_BASE_URL}/v1/videos",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    video_id = data.get("video_id")

    if not video_id:
        raise RuntimeError(
            "Agnes did not return a video_id: "
            + str(data)[:400]
        )

    # Poll for completed video
    for attempt in range(22):
        time.sleep(5)

        result_response = requests.get(
            f"{AGNES_BASE_URL}/agnesapi",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            params={
                "video_id": video_id,
                "model_name": model,
            },
            timeout=30,
        )
        result_response.raise_for_status()

        result = result_response.json()
        status = str(
            result.get("status", "")
        ).lower()

        if status == "completed":
            video_url = result.get("url")

            if not video_url:
                raise RuntimeError(
                    "Agnes completed but returned no video URL."
                )

            return video_url

        if status == "failed":
            raise RuntimeError(
                "Agnes video generation failed: "
                + str(result.get("error", result))[:400]
            )

    raise TimeoutError(
        "Agnes is still processing this video. "
        "Try again later."
    )


def call_gradio_space(provider, prompt, image_path=None):
    token = os.getenv("HF_TOKEN") or None

    client = Client(
        provider["url"],
        hf_token=token
    )

    if image_path:
        result = client.predict(
            prompt,
            image_path,
            api_name=provider["api_name"]
        )
    else:
        result = client.predict(
            prompt,
            api_name=provider["api_name"]
        )

    return result


def generate_with_fallback(prompt, image_path=None):
    providers = configured_providers()

    if not providers:
        raise RuntimeError(
            "No provider configured. Add AGNES_API_KEY "
            "in the Render backend environment."
        )

    errors = []

    start = int(time.time()) % len(providers)
    ordered = providers[start:] + providers[:start]

    for provider in ordered:
        try:
            if provider.get("kind") == "agnes":
                output = call_agnes(
                    provider,
                    prompt,
                    image_path
                )
            else:
                output = call_gradio_space(
                    provider,
                    prompt,
                    image_path
                )

            return {
                "provider": provider["name"],
                "output": output,
            }

        except Exception as exc:
            errors.append(
                f'{provider["name"]}: {str(exc)[:220]}'
            )

    raise RuntimeError(
        "All configured providers failed: "
        + " | ".join(errors)
    )
