"""Central settings. Edit DSNs for your own PostgreSQL; everything else is frozen for the experiment."""
import os

# LLM backend. Choose with environment variables (nothing else changes between providers):
#   T2S_PROVIDER = anthropic | groq | cerebras | gemini | openai_compatible
#   T2S_MODEL    = exact model id of the provider (record it, with the date, in the dissertation)
# Free options use the provider's OpenAI-compatible endpoint and need only an API key in an environment variable.
PROVIDERS = {
    "anthropic": {"base_url": None, "key_env": "ANTHROPIC_API_KEY", "default_model": "claude-sonnet-5-5"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY", "default_model": "llama-3.3-70b-versatile"},
    "cerebras": {"base_url": "https://api.cerebras.ai/v1", "key_env": "CEREBRAS_API_KEY", "default_model": "llama-3.3-70b"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "key_env": "GEMINI_API_KEY",
               "default_model": "gemini-flash-lite-latest"},
    "openai_compatible": {"base_url": os.environ.get("T2S_BASE_URL"), "key_env": os.environ.get("T2S_KEY_ENV", "T2S_API_KEY"),
                          "default_model": None},
}
PROVIDER = os.environ.get("T2S_PROVIDER", "anthropic")
MODEL_ID = os.environ.get("T2S_MODEL") or PROVIDERS[PROVIDER]["default_model"]
REASONING_EFFORT = os.environ.get("T2S_REASONING_EFFORT")          # low | medium | high, for reasoning models such as gpt-oss
MIN_INTERVAL_S = float(os.environ.get("T2S_MIN_INTERVAL", "0"))   # pause between calls, to stay inside free-tier limits
TIMEOUT_S = float(os.environ.get("T2S_TIMEOUT", "120"))                 # seconds to wait for one model answer; raise (e.g. 600) for slow local models
MAX_RETRIES_429 = 6                                                # waits and retries on rate-limit errors (not counted in latency)
TEMPERATURE = 0
MAX_TOKENS = int(os.environ.get("T2S_MAX_TOKENS", "1024"))   # raise (e.g. 3000) if a reasoning model's answers come back empty

# One DSN per database. Defaults are a local PostgreSQL; override with T2S_DSN_NORTHWIND / T2S_DSN_SHOPDB
# (add password=... if your server needs one).
DSNS = {
    "northwind": os.environ.get("T2S_DSN_NORTHWIND", "host=localhost port=5432 dbname=northwind user=postgres"),
    "shopdb": os.environ.get("T2S_DSN_SHOPDB", "host=localhost port=5432 dbname=shopdb user=postgres"),
}

STATEMENT_TIMEOUT_MS = 10_000   # read-only execution time limit
MAX_ROWS = 5_000                # rows fetched per query (gold results are far smaller)
TOP_K_TABLES = 4                # tables chosen by keyword schema selection (before join-path expansion)
N_RUNS = 3