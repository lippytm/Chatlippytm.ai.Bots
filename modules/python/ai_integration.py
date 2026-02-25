"""
modules/python/ai_integration.py
---------------------------------
Starter template for Python-based AI integrations.

This module demonstrates how to send a prompt to an AI provider (defaulting
to OpenAI) using settings drawn from the global configuration file.  Swap out
the ``_call_openai`` function for any other provider to extend the module.

Environment Variables
---------------------
OPENAI_API_KEY
    Your OpenAI API key.  Required when using the ``openai`` provider.

Example
-------
    $ python modules/python/ai_integration.py "What is artificial intelligence?"
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Optional dependency: openai SDK
# ---------------------------------------------------------------------------
try:
    import openai as _openai_sdk
    _OPENAI_AVAILABLE = True
except ImportError:
    _openai_sdk = None  # type: ignore[assignment]
    _OPENAI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional dependency: PyYAML (needed for config_loader)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from shared.utils.config_loader import load_config
    _CONFIG: Dict[str, Any] = load_config()
except Exception:  # pragma: no cover
    _CONFIG = {}


def get_ai_config() -> Dict[str, Any]:
    """Return the AI provider configuration from the global config."""
    return _CONFIG.get("ai", {})


def chat(prompt: str, provider: str | None = None) -> str:
    """Send *prompt* to an AI provider and return the response text.

    Parameters
    ----------
    prompt:
        The user's input message.
    provider:
        AI provider name (``"openai"``, ``"local"``, …).  Falls back to
        ``ai.default_provider`` from ``config/config.yaml``.

    Returns
    -------
    str
        The AI's response text.

    Raises
    ------
    ValueError
        If no provider is configured or the provider is unsupported.
    RuntimeError
        If the underlying API call fails.
    """
    ai_cfg = get_ai_config()
    resolved_provider = provider or ai_cfg.get("default_provider", "openai")

    if resolved_provider == "openai":
        return _call_openai(prompt, ai_cfg)
    if resolved_provider == "local":
        return _call_local(prompt, ai_cfg)

    raise ValueError(
        f"Unsupported AI provider: '{resolved_provider}'. "
        "Add a handler in ai_integration.py or update config/config.yaml."
    )


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _call_openai(prompt: str, ai_cfg: Dict[str, Any]) -> str:
    """Call the OpenAI Chat Completions API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set."
        )
    if not _OPENAI_AVAILABLE:
        raise ImportError(
            "openai package is not installed. Run: pip install openai"
        )
    provider_cfg = ai_cfg.get("providers", {}).get("openai", {})
    client = _openai_sdk.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=provider_cfg.get("model", "gpt-4o-mini"),
        max_tokens=provider_cfg.get("max_tokens", 1024),
        temperature=provider_cfg.get("temperature", 0.7),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _call_local(prompt: str, ai_cfg: Dict[str, Any]) -> str:
    """Call a local Ollama-compatible endpoint."""
    import json
    import urllib.request

    provider_cfg = ai_cfg.get("providers", {}).get("local", {})
    endpoint = provider_cfg.get("endpoint", "http://localhost:11434/api/generate")
    model = provider_cfg.get("model", "llama3")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data.get("response", "").strip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) < 2:
        print("Usage: python ai_integration.py \"<your prompt>\"")
        sys.exit(1)
    user_prompt = " ".join(sys.argv[1:])
    try:
        reply = chat(user_prompt)
        print(f"AI Response: {reply}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
