"""Command-line interface for ai_utilities."""

import argparse
import sys
from typing import Optional, List

from .setup.wizard import run_setup_wizard, SetupMode


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="ai-utilities",
        description="AI Utilities - Setup and configuration tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Run interactive setup wizard"
    )
    setup_parser.add_argument(
        "--mode",
        choices=["normal", "enhanced", "improved"],
        help="Setup mode to run (skip menu)"
    )
    setup_parser.add_argument(
        "--dotenv-path",
        default=".env",
        help="Path to .env file (default: .env)"
    )
    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without modifying files"
    )
    setup_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompting (error if required info missing)"
    )
    
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    
    # Handle case where no command is provided - default to setup
    if argv is None:
        argv = sys.argv[1:]
    
    if not argv:
        argv = ["setup"]
    
    args = parser.parse_args(argv)
    
    # Handle commands
    if args.command == "setup" or args.command is None:
        result = None
        try:
            # Convert mode string to enum
            mode = None
            if args.mode:
                mode_map = {
                    "normal": SetupMode.NORMAL,
                    "enhanced": SetupMode.ENHANCED,
                    "improved": SetupMode.IMPROVED
                }
                mode = mode_map[args.mode]
            
            # Run the setup wizard
            result = run_setup_wizard(
                mode=mode,
                dotenv_path=args.dotenv_path,
                dry_run=args.dry_run,
                non_interactive=args.non_interactive
            )
            
            # Print summary
            print(f"\nSetup completed successfully!")
            print(f"Provider: {result.provider}")
            if result.model:
                print(f"Model: {result.model}")
            if result.base_url:
                print(f"Base URL: {result.base_url}")
            if result.api_key:
                print(f"API Key: {'*' * 8}{result.api_key[-4:] if len(result.api_key) > 4 else '****'}")
            
            if not args.dry_run:
                print(f"Configuration written to: {args.dotenv_path}")
            
            return 0
            
        except KeyboardInterrupt:
            print("\nSetup cancelled by user.")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
