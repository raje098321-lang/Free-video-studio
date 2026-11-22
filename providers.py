"""Provider rotation scaffold. Space APIs are not standardized; map each Space's schema."""
import os, time
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

def configured_providers():
    providers=[]
    for i in range(1, 10):
        url=os.getenv(f"PROVIDER_{i}_URL","").strip()
        enabled=os.getenv(f"PROVIDER_{i}_ENABLED","false").lower()=="true"
        if url and enabled:
            providers.append({
                "name": os.getenv(f"PROVIDER_{i}_NAME",f"Provider {i}"),
                "url": url,
                "api_name": os.getenv(f"PROVIDER_{i}_API_NAME","/generate"),
            })
    return providers

def call_gradio_space(provider, prompt, image_path=None):
    """Default contract assumes a Space accepts a prompt string.
    Edit this function for the chosen Space's documented API inputs.
    Never put secrets in frontend code.
    """
    token=os.getenv("HF_TOKEN") or None
    client=Client(provider["url"], hf_token=token)
    # Many Spaces require additional args (duration, image, seed, etc.).
    # Use the Space's 'Use via API' docs to adapt this call.
    if image_path:
        # Space-specific input order may differ; adapt to that Space's API docs.
        result=client.predict(prompt, image_path, api_name=provider["api_name"])
    else:
        result=client.predict(prompt, api_name=provider["api_name"])
    return result

def generate_with_fallback(prompt, image_path=None):
    providers=configured_providers()
    if not providers:
        raise RuntimeError("No enabled provider. Configure at least one provider in backend/.env.")
    errors=[]
    # Rotate starting provider between requests to spread use.
    start=int(time.time()) % len(providers)
    ordered=providers[start:]+providers[:start]
    for provider in ordered:
        try:
            output=call_gradio_space(provider, prompt, image_path)
            return {"provider":provider["name"],"output":output}
        except Exception as exc:
            errors.append(f'{provider["name"]}: {str(exc)[:220]}')
            # On quota/rate limit/network errors, attempt the next configured provider.
            continue
    raise RuntimeError("All configured providers failed: " + " | ".join(errors))
