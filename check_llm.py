"""One test call to the configured provider. Prints the raw HTTP status and body if something is wrong.

  python check_llm.py
"""
import json
import os
import sys

from t2s import config


def main():
    spec = config.PROVIDERS[config.PROVIDER]
    print("provider:", config.PROVIDER, "| model:", config.MODEL_ID, "| endpoint:", spec["base_url"])
    if config.PROVIDER == "anthropic":
        from t2s.llm import make_llm
        print(make_llm().complete("Answer with one word.", "Say OK."))
        return
    key = os.environ.get(spec["key_env"])
    if not key:
        sys.exit(f"{spec['key_env']} is not set in this terminal")
    import httpx
    url = spec["base_url"].rstrip("/") + "/chat/completions"
    body = {"model": config.MODEL_ID, "temperature": config.TEMPERATURE, "max_tokens": 20,
            "messages": [{"role": "user", "content": "Reply with the single word OK."}]}
    r = httpx.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=body, timeout=60)
    print("HTTP", r.status_code, "| content-type:", r.headers.get("content-type"))
    print(r.text[:600])
    if r.status_code == 200:
        try:
            print("parsed reply:", json.loads(r.text)["choices"][0]["message"]["content"])
        except Exception as e:
            print("could not parse the reply as an OpenAI-style answer:", e)


if __name__ == "__main__":
    main()
