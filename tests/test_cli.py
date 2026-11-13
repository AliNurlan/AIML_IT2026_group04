import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from main import DEFAULT_PROMPT, build_parser, count_characters, main


class CliTests(unittest.TestCase):
    def test_default_demo_is_retained(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.prompt, DEFAULT_PROMPT)
        self.assertIsNone(args.provider)
        self.assertIsNone(args.model)

    def test_custom_prompt_and_provider_overrides(self):
        args = build_parser().parse_args(["--provider", "gemini", "--model", "example", "Count abc"])
        self.assertEqual((args.provider, args.model, args.prompt), ("gemini", "example", "Count abc"))

    def test_tool_counts_spaces(self):
        self.assertEqual(count_characters.invoke({"text": "a b"}), "The text contains 3 characters.")

    def test_custom_request_reaches_agent_with_bounded_recursion(self):
        with patch("sys.argv", ["main.py", "--provider", "lmstudio", "--model", "local-model", "Count abc"]), \
             patch("main.ChatOpenAI") as model_class, \
             patch("main.create_agent") as create_agent, \
             contextlib.redirect_stdout(io.StringIO()):
            create_agent.return_value.invoke.return_value = {
                "messages": [SimpleNamespace(text="done", tool_calls=[])]
            }
            main()
        self.assertEqual(model_class.call_args.kwargs["model"], "local-model")
        self.assertEqual(create_agent.return_value.invoke.call_args.args[0]["messages"][0]["content"], "Count abc")
        self.assertEqual(create_agent.return_value.invoke.call_args.kwargs["config"]["recursion_limit"], 12)


if __name__ == "__main__":
    unittest.main()
