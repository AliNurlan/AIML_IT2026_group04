"""Tiny LangChain + Gemini tool-calling demo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR.parent / ".env")


@tool
def count_characters(text: str) -> str:
    """Count the characters in the given text, including spaces."""
    return f"The text contains {len(text)} characters."


DEFAULT_PROMPT = (
    'Call the count_characters tool with the exact text '
    '"LangChain + Gemini" and then briefly report the result.'
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the tool-calling prototype.")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT, help="Request to send to the model")
    parser.add_argument("--provider", choices=("lmstudio", "gemini"), help="Override LLM_PROVIDER")
    parser.add_argument("--model", help="Override the provider's model name")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    provider = (args.provider or os.getenv("LLM_PROVIDER", "lmstudio")).lower()
    if provider == "lmstudio":
        model = ChatOpenAI(
            model=args.model or os.getenv("LM_STUDIO_MODEL", "liquid/lfm2.5-1.2b"),
            base_url=os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key="lm-studio",  # LM Studio ignores this unless auth is enabled.
            temperature=0,
            timeout=60,
            max_retries=0,
        )
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            raise SystemExit("Set GOOGLE_API_KEY in the parent .env file.")
        model = ChatGoogleGenerativeAI(
            model=args.model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            temperature=0,
            timeout=30,
            max_retries=0,
        )
    else:
        raise SystemExit("LLM_PROVIDER must be 'lmstudio' or 'gemini'.")
    agent = create_agent(model, tools=[count_characters])

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": args.prompt,
                }
            ]
        },
        config={"recursion_limit": 12},
    )

    for message in result["messages"]:
        for tool_call in getattr(message, "tool_calls", []):
            print(f"Model called: {tool_call['name']}({tool_call['args']})")
    print(f"\n{provider}: {result['messages'][-1].text}")


if __name__ == "__main__":
    main()
