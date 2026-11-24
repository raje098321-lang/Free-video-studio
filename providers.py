"""
Agnes AI video provider + optional Gradio/Hugging Face fallback.

Render backend environment variables:
  AGNES_API_KEY                Required for Agnes
  AGNES_BASE_URL               Optional
  AGNES_VIDEO_MODEL            Optional
  AGNES_VIDEO_SECONDS          Optional: 4 to 12 seconds
  AGNES_VIDEO_SIZE              Optional: default 720P
  AGNES_VIDEO_ASPECT_RATIO      Optional: default 9:16
  AGNES_VIDEO_MAX_WAIT_SECONDS  Optional: default 300
  HF_TOKEN                     Optional for private Hugging Face Spaces

Never put API keys in frontend code or GitHub.
"""

import base64
import mimetypes
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

AGNES_BASE_URL = os.getenv(
    "AGNES_BASE_URL",
    "https://apihub.agnes-ai.com",
).rstrip("/")

SUPPORTED_AGNES_MODELS = {
    "agnes-video-2.5-flash",
    "agnes-video-2.5",
}


def configured_providers():
    providers = []

    api_key = os.getenv("AGNES_API_KEY", "").strip()

    if api_key:
        model = os.getenv(
            "AGNES_VIDEO_MODEL",
            "agnes-video-2.5-flash",
        ).strip()

        if model not in SUPPORTED_AGNES_MODELS:
            raise ValueError(
                "AGNES_VIDEO_MODEL must be "
                "agnes-video-2.5-flash or agnes-video-2.5."
            )

        providers.append({
            "kind": "agnes",
            "name": "Agnes AI Video",
            "model": model,
        })

    # Optional Gradio / Hugging Face Spaces.
    # Each Space must have its own correct API input schema.
    for i in range(1, 10):
        url = os.getenv(
            f"PROVIDER_{i}_URL",
            "",
        ).strip()

        enabled = (
            os.getenv(
                f"PROVIDER_{i}_ENABLED",
                "false",
            ).strip().lower() == "true"
        )

        if url and enabled:
            providers.append({
                "kind": "gradio",
                "name": os.getenv(
                    f"PROVIDER_{i}_NAME",
                    f"Provider {i}",
                ),
                "url": url,
                "api_name": os.getenv(
                    f"PROVIDER_{i}_API_NAME",
                    "/generate",
                ),
            })

    return providers


def request_json(
    method,
    url,
    *,
    headers,
    timeout=60,
    **kwargs,
):
    """Request JSON with retries for temporary network/API errors."""

    retryable_statuses = {
        408, 429, 500, 502, 503, 504,
    }

    for attempt in range(4):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )

            if (
                response.status_code in retryable_statuses
                and attempt < 3
            ):
                time.sleep(min(2 ** attempt, 8))
                continue

            response.raise_for_status()
            return response.json()

        except (
            requests.Timeout,
            requests.ConnectionError,
        ):
            if attempt < 3:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise

    raise RuntimeError("API request failed after retries.")


def call_agnes(provider, prompt, image_path=None):
    api_key = os.getenv(
        "AGNES_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "AGNES_API_KEY is missing in Render."
        )

    model = provider["model"]

    try:
        seconds = int(
            os.getenv("AGNES_VIDEO_SECONDS", "5")
        )
    except ValueError:
        raise ValueError(
            "AGNES_VIDEO_SECONDS must be a number from 4 to 12."
        )

    if not 4 <= seconds <= 12:
        raise ValueError(
            "AGNES_VIDEO_SECONDS must be between 4 and 12."
        )

    size = os.getenv(
        "AGNES_VIDEO_SIZE",
        "720P",
    ).strip().upper()

    if (
        model == "agnes-video-2.5-flash"
        and size != "720P"
    ):
        raise ValueError(
            "Agnes Video 2.5 Flash supports 720P only. "
            "Set AGNES_VIDEO_SIZE to 720P."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "mode": "text",
        "seconds": str(seconds),
        "size": size,
        "aspect_ratio": os.getenv(
            "AGNES_VIDEO_ASPECT_RATIO",
            "9:16",
        ).strip(),
        "n": 1,
    }

    # Image-to-video uses keyframe mode and first_frame.
    if image_path:
        path = Path(image_path)

        if not path.is_file():
            raise FileNotFoundError(
                "Uploaded image file was not found."
            )

        mime = (
            mimetypes.guess_type(path.name)[0]
            or "image/jpeg"
        )

        encoded = base64.b64encode(
            path.read_bytes()
        ).decode("ascii")

        payload["mode"] = "keyframe"
        payload["first_frame"] = (
            f"data:{mime};base64,{encoded}"
        )

    # Create the video generation task.
    created = request_json(
        "POST",
        f"{AGNES_BASE_URL}/v1/videos",
        headers=headers,
        timeout=60,
        json=payload,
    )

    video_id = created.get("video_id")

    if not video_id:
        raise RuntimeError(
            "Agnes did not return video_id: "
            + str(created)[:350]
        )

    # Poll for the completed video.
    poll_url = f"{AGNES_BASE_URL}/agnesapi"

    try:
        max_wait = int(
            os.getenv(
                "AGNES_VIDEO_MAX_WAIT_SECONDS",
                "300",
            )
        )
    except ValueError:
        max_wait = 300

    deadline = time.monotonic() + max_wait

    while time.monotonic() < deadline:
        time.sleep(5)

        result = request_json(
            "GET",
            poll_url,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=30,
            params={
                "video_id": video_id,
                "model_name": model,
            },
        )

        status = str(
            result.get("status", "")
        ).strip().lower()

        if status in {
            "completed",
            "succeeded",
            "success",
            "done",
        }:
            video_url = (
                result.get("url")
                or result.get("video_url")
                or (result.get("data") or {}).get("url")
            )

            if not video_url:
                raise RuntimeError(
                    "Agnes completed but returned no video URL: "
                    + str(result)[:350]
                )

            return video_url

        if status in {
            "failed",
            "error",
            "cancelled",
            "canceled",
        }:
            raise RuntimeError(
                "Agnes video generation failed: "
                + str(result.get("error", result))[:350]
            )

    raise TimeoutError(
        "Agnes is still processing this video. "
        "Try again later."
    )


def call_gradio_space(
    provider,
    prompt,
    image_path=None,
):
    token = os.getenv("HF_TOKEN") or None

    client = Client(
        provider["url"],
        hf_token=token,
    )

    if image_path:
        result = client.predict(
            prompt,
            image_path,
            api_name=provider["api_name"],
        )
    else:
        result = client.predict(
            prompt,
            api_name=provider["api_name"],
        )

    return result


def generate_with_fallback(
    prompt,
    image_path=None,
):
    providers = configured_providers()

    if not providers:
        raise RuntimeError(
            "No provider configured. Add AGNES_API_KEY "
            "to the Render backend environment."
        )

    errors = []

    start = int(time.time()) % len(providers)

    ordered = (
        providers[start:]
        + providers[:start]
    )

    for provider in ordered:
        try:
            if provider.get("kind") == "agnes":
                output = call_agnes(
                    provider,
                    prompt,
                    image_path,
                )
            else:
                output = call_gradio_space(
                    provider,
                    prompt,
                    image_path,
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

