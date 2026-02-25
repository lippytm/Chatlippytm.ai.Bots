"""
modules/python/tests/test_ai_integration.py
--------------------------------------------
Unit tests for modules/python/ai_integration.py.

These tests use ``unittest.mock`` to avoid making real network calls, so they
can run in CI without an API key.
"""

from __future__ import annotations

import importlib
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Ensure repo root is on the path so imports resolve correctly
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, _REPO_ROOT)


class TestGetAiConfig(unittest.TestCase):
    """Tests for get_ai_config()."""

    def test_returns_dict(self):
        from modules.python.ai_integration import get_ai_config
        config = get_ai_config()
        self.assertIsInstance(config, dict)

    def test_contains_default_provider(self):
        from modules.python.ai_integration import get_ai_config
        config = get_ai_config()
        # The global config YAML defines ai.default_provider
        self.assertIn("default_provider", config)


class TestChatDispatch(unittest.TestCase):
    """Tests for the chat() dispatch logic."""

    def test_unsupported_provider_raises(self):
        from modules.python.ai_integration import chat
        with self.assertRaises(ValueError):
            chat("hello", provider="unsupported_provider_xyz")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_openai_provider_called(self):
        """chat() with provider='openai' should delegate to _call_openai."""
        import modules.python.ai_integration as module
        with patch.object(module, "_call_openai", return_value="mocked response") as mock_fn:
            result = module.chat("test prompt", provider="openai")
        mock_fn.assert_called_once()
        self.assertEqual(result, "mocked response")

    def test_local_provider_called(self):
        """chat() with provider='local' should delegate to _call_local."""
        import modules.python.ai_integration as module
        with patch.object(module, "_call_local", return_value="local response") as mock_fn:
            result = module.chat("test prompt", provider="local")
        mock_fn.assert_called_once()
        self.assertEqual(result, "local response")


class TestCallOpenAI(unittest.TestCase):
    """Tests for _call_openai()."""

    def test_missing_api_key_raises(self):
        import modules.python.ai_integration as module
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(EnvironmentError):
                module._call_openai("hello", {})

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_returns_response_content(self):
        """_call_openai should return the message content from the API response."""
        import modules.python.ai_integration as module

        # Build a minimal mock that mimics the openai SDK response structure
        mock_message = MagicMock()
        mock_message.content = "  Hello from OpenAI!  "
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        mock_sdk = MagicMock()
        mock_sdk.OpenAI.return_value = mock_client

        with patch.object(module, "_openai_sdk", mock_sdk), \
             patch.object(module, "_OPENAI_AVAILABLE", True):
            result = module._call_openai("test", {})

        self.assertEqual(result, "Hello from OpenAI!")


class TestCallLocal(unittest.TestCase):
    """Tests for _call_local()."""

    def test_returns_response_field(self):
        """_call_local should extract the 'response' key from JSON."""
        import json
        import modules.python.ai_integration as module

        mock_resp_body = json.dumps({"response": "local llm answer"}).encode()
        mock_urlopen = MagicMock()
        mock_urlopen.__enter__ = lambda s: s
        mock_urlopen.__exit__ = MagicMock(return_value=False)
        mock_urlopen.read.return_value = mock_resp_body

        with patch("urllib.request.urlopen", return_value=mock_urlopen):
            result = module._call_local("hello", {})

        self.assertEqual(result, "local llm answer")


class TestConfigLoader(unittest.TestCase):
    """Tests for shared/utils/config_loader.py."""

    def test_load_config_returns_dict(self):
        from shared.utils.config_loader import load_config
        config = load_config()
        self.assertIsInstance(config, dict)

    def test_load_config_has_app_section(self):
        from shared.utils.config_loader import load_config
        config = load_config()
        self.assertIn("app", config)
        self.assertEqual(config["app"]["name"], "Chatlippytm.ai.Bots")

    def test_load_extensions_returns_list(self):
        from shared.utils.config_loader import load_extensions
        extensions = load_extensions()
        self.assertIsInstance(extensions, list)
        self.assertGreater(len(extensions), 0)

    def test_get_enabled_extensions_only_enabled(self):
        from shared.utils.config_loader import get_enabled_extensions
        enabled = get_enabled_extensions()
        for ext in enabled:
            self.assertTrue(ext["enabled"])

    def test_load_config_file_not_found(self):
        from shared.utils.config_loader import load_config
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_extensions_file_not_found(self):
        from shared.utils.config_loader import load_extensions
        with self.assertRaises(FileNotFoundError):
            load_extensions("/nonexistent/path/extensions.json")


if __name__ == "__main__":
    unittest.main()
