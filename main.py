#!/usr/bin/env python3
"""Interactive developer demo entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional


def _load_dotenv() -> None:
    """Optionally load a .env file for IDE runs.

    Returns:
        None.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    possible_env_paths = [
        Path(__file__).parent / ".env",
        Path(".") / ".env",
        Path(__file__).parent.parent / ".env",
    ]

    for env_path in possible_env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"📁 Loaded .env from: {env_path}")
            return


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the demo app.

    Returns:
        ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "AI Utilities developer demo.\n\n"
            "Stage A: select a validated model (cloud + local).\n"
            "Stage B: run scenarios using that selected model.\n\n"
            "Env vars: AI_API_KEY, GROQ_API_KEY, AI_PROVIDER, AI_MODEL, AI_BASE_URL, LOCAL_OPENAI_API_KEY."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--provider",
        choices=["openai", "openai_compatible", "ollama"],
        help="Override provider selection (CLI has highest precedence).",
    )
    parser.add_argument(
        "--model",
        help="Override model id (CLI has highest precedence).",
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        help="Override base URL for openai-compatible endpoints.",
    )
    parser.add_argument(
        "--endpoint",
        choices=["openai", "groq", "ollama", "lmstudio", "textgen", "fastchat"],
        help="Convenience selector for common endpoints.",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Print the validated model list and exit.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Never prompt; fail fast with actionable fix instructions.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug details (stack traces) on failures.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the demo entrypoint.

    Args:
        argv: Optional argv override.

    Returns:
        Process exit code.
    """
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    _load_dotenv()

    from ai_utilities.demo.app import run_app

    parser = _build_parser()
    args = parser.parse_args(argv)
    run_app(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
