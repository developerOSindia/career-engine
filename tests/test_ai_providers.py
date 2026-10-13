"""
Unit tests for CareerEngine Multi-Provider LLM Integration (OpenAI, Claude, Gemini, NVIDIA, Ollama).
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from core.config_loader import Config
from ai.ai_solver import UnifiedAISolver

class TestAIProviders(unittest.TestCase):

    def test_config_provider_properties(self):
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-openai-12345",
            "OPENAI_MODEL": "gpt-4o-mini",
            "ANTHROPIC_API_KEY": "sk-ant-test-67890",
            "ANTHROPIC_MODEL": "claude-3-5-haiku-20241022"
        }):
            config = Config()
            self.assertEqual(config.openai_api_key, "sk-test-openai-12345")
            self.assertEqual(config.openai_model, "gpt-4o-mini")
            self.assertEqual(config.anthropic_api_key, "sk-ant-test-67890")
            self.assertEqual(config.anthropic_model, "claude-3-5-haiku-20241022")

    def test_claude_api_call_success(self):
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-valid-key",
            "ANTHROPIC_MODEL": "claude-3-5-haiku-20241022"
        }):
            config = Config()
            solver = UnifiedAISolver(config=config)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"text": "5 years"}]
            }

            with patch("requests.post", return_value=mock_response) as mock_post:
                ans, model = solver._call_claude("How many years of Python experience do you have?")
                self.assertEqual(ans, "5 years")
                self.assertIn("Claude", model)
                mock_post.assert_called_once()
                self.assertIn("api.anthropic.com", mock_post.call_args[0][0])

    def test_openai_api_call_success(self):
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-valid-openai-key",
            "OPENAI_MODEL": "gpt-4o-mini"
        }):
            config = Config()
            solver = UnifiedAISolver(config=config)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": "30 days"}
                }]
            }

            with patch("requests.post", return_value=mock_response) as mock_post:
                ans, model = solver._call_openai("What is your notice period?")
                self.assertEqual(ans, "30 days")
                self.assertIn("OpenAI", model)
                mock_post.assert_called_once()
                self.assertIn("api.openai.com", mock_post.call_args[0][0])

    def test_fallback_priority_claude_when_gemini_fails(self):
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-valid-key"
        }):
            config = Config()
            solver = UnifiedAISolver(config=config)

            # Gemini returns None, Rule-based returns None
            with patch.object(solver, "_rule_based_solve", return_value=None):
                with patch.object(solver, "_call_gemini", return_value=None):
                    with patch.object(solver, "_call_claude", return_value=("Claude Answer", "Claude (claude-3-5-haiku)")) as mock_claude:
                        ans = solver.solve_question("Describe a challenging technical project you led.", "textarea")
                        self.assertEqual(ans, "Claude Answer")
                        mock_claude.assert_called_once()

    def test_fallback_priority_openai_when_claude_fails(self):
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-valid-openai-key"
        }):
            config = Config()
            solver = UnifiedAISolver(config=config)

            # Rule-based, Gemini, and Claude fail
            with patch.object(solver, "_rule_based_solve", return_value=None):
                with patch.object(solver, "_call_gemini", return_value=None):
                    with patch.object(solver, "_call_claude", return_value=None):
                        with patch.object(solver, "_call_openai", return_value=("OpenAI Answer", "OpenAI (gpt-4o-mini)")) as mock_openai:
                            ans = solver.solve_question("Why do you want to join our startup?", "text")
                            self.assertEqual(ans, "OpenAI Answer")
                            mock_openai.assert_called_once()

if __name__ == "__main__":
    unittest.main()
