"""LLM clients. make_llm() picks the provider from T2S_PROVIDER; ScriptedLLM is used only to test the pipeline offline."""
import os
import time
from dataclasses import dataclass

from . import config


@dataclass
class LLMReply:
    text: str
    seconds: float
    input_tokens: int = 0
    output_tokens: int = 0


def _backoff_sleep(attempt: int, err) -> float:
    """Seconds to wait after a rate-limit error: honour Retry-After if present, else exponential."""
    try:
        ra = err.response.headers.get("retry-after")
        if ra:
            return min(float(ra) + 1, 120)
    except Exception:
        pass
    return min(2 ** attempt * 5, 120)


class AnthropicLLM:
    def __init__(self):
        import anthropic  # imported here so tests run without the package or a key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("Set ANTHROPIC_API_KEY before running real experiments.")
        self.client = anthropic.Anthropic()
        self.model = config.MODEL_ID
        self._last = 0.0

    def complete(self, system: str, user: str) -> LLMReply:
        _pace(self)
        t0 = time.perf_counter()
        msg = self.client.messages.create(
            model=self.model, max_tokens=config.MAX_TOKENS, temperature=config.TEMPERATURE,
            system=system, messages=[{"role": "user", "content": user}],
        )
        dt = time.perf_counter() - t0
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return LLMReply(text, dt, msg.usage.input_tokens, msg.usage.output_tokens)


class OpenAICompatLLM:
    """Any provider with an OpenAI-style chat endpoint (GitHub Models, Groq, Cerebras, Gemini, ...)."""
    def __init__(self):
        from openai import OpenAI  # imported here so tests run without the package or a key
        spec = config.PROVIDERS[config.PROVIDER]
        key = os.environ.get(spec["key_env"])
        if not key:
            raise RuntimeError(f"Set {spec['key_env']} before running real experiments with provider '{config.PROVIDER}'.")
        if not config.MODEL_ID:
            raise RuntimeError("Set T2S_MODEL to the provider's model id.")
        self.client = OpenAI(api_key=key, base_url=spec["base_url"], max_retries=0, timeout=config.TIMEOUT_S)
        self.model = config.MODEL_ID
        self._last = 0.0

    def complete(self, system: str, user: str) -> LLMReply:
        from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
        for attempt in range(config.MAX_RETRIES_429 + 1):
            _pace(self)
            t0 = time.perf_counter()
            try:
                extra = {"reasoning_effort": config.REASONING_EFFORT} if config.REASONING_EFFORT else {}
                r = self.client.chat.completions.create(
                    model=self.model, max_tokens=config.MAX_TOKENS, temperature=config.TEMPERATURE,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    extra_body=extra or None,
                )
            except (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError) as e:
                # free tiers: rate limits, dropped connections, timeouts and server errors are waited out and retried
                if attempt == config.MAX_RETRIES_429:
                    raise
                wait = _backoff_sleep(attempt, e)
                why = "rate limit reached" if isinstance(e, RateLimitError) else f"connection problem ({type(e).__name__})"
                print(f"  {why}, waiting {wait:.0f}s (retry {attempt + 1}/{config.MAX_RETRIES_429})", flush=True)
                time.sleep(wait)
                continue
            dt = time.perf_counter() - t0      # time of the successful call only
            if isinstance(r, (str, bytes)) or not getattr(r, "choices", None):
                raise RuntimeError(f"Unexpected reply from {config.PROVIDER} (model {self.model}); first 400 characters: "
                                   f"{str(r)[:400]!r}. Check T2S_MODEL, the token's permissions and the endpoint.")
            u = r.usage
            text = r.choices[0].message.content or ""
            if not text.strip():
                raise RuntimeError(f"Empty answer from {self.model} (finish_reason={r.choices[0].finish_reason}). A reasoning model "
                                   "may have used all its tokens thinking: set T2S_REASONING_EFFORT=low and/or T2S_MAX_TOKENS=3000.")
            return LLMReply(text, dt,
                            getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0)


def _pace(obj):
    """Optional minimum gap between calls (T2S_MIN_INTERVAL seconds) to respect free-tier per-minute limits."""
    wait = config.MIN_INTERVAL_S - (time.perf_counter() - obj._last)
    if wait > 0:
        time.sleep(wait)
    obj._last = time.perf_counter()


def make_llm():
    return AnthropicLLM() if config.PROVIDER == "anthropic" else OpenAICompatLLM()


class ScriptedLLM:
    """Test double: returns the next scripted answer for each call. Never used for results."""
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def complete(self, system: str, user: str) -> LLMReply:
        self.calls.append((system, user))
        return LLMReply(self.answers.pop(0), 0.0)