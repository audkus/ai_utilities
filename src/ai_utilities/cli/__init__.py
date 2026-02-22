"""Command-line interface for ai_utilities."""

import argparse
import sys
from typing import Optional, List

from .env_writer import EnvWriter
from ..setup.wizard import run_setup_wizard, SetupMode


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
        choices=["normal", "enhanced", "improved", "single-provider", "multi-provider", "non-interactive"],
        help="Setup mode to run (skip mode selection)"
    )
    setup_parser.add_argument(
        "--provider",
        choices=["openai", "groq", "together", "openrouter", "deepseek", 
                "ollama", "lmstudio", "fastchat", "text-generation-webui"],
        help="Provider for single-provider mode (e.g., openai, ollama, groq)"
    )
    setup_parser.add_argument(
        "--model",
        help="Model name (provider-specific)"
    )
    setup_parser.add_argument(
        "--base-url",
        help="Base URL for provider (custom endpoints)"
    )
    setup_parser.add_argument(
        "--api-key",
        help="API key (use with caution, prefer environment variables)"
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
        help="Run without prompting (requires --mode and --provider)"
    )
    
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    
    # Default to setup command if no arguments provided
    if argv is None or len(argv) == 0:
        argv = ["setup"]
    
    args = parser.parse_args(argv)
    
    # Handle commands
    if args.command == "setup" or args.command is None:
        try:
            # Convert legacy mode strings to enum values
            mode = None
            if args.mode:
                # Map string values to old wizard enum
                mode_map = {
                    "normal": SetupMode.NORMAL,
                    "enhanced": SetupMode.ENHANCED, 
                    "improved": SetupMode.IMPROVED,
                    "single-provider": SetupMode.NORMAL,
                    "multi-provider": SetupMode.ENHANCED,
                    "non-interactive": SetupMode.IMPROVED
                }
                mode = mode_map.get(args.mode)
            
            # Check for non-interactive requirements
            if args.non_interactive:
                # If no mode specified, default to normal for non-interactive
                if not mode:
                    mode = SetupMode.NORMAL
                
                # For legacy compatibility, don't require provider for normal mode
                # The old wizard will handle defaults
            
            # Prepare kwargs for non-interactive mode
            setup_kwargs = {}
            if args.non_interactive:
                if args.provider:
                    setup_kwargs["provider"] = args.provider
                if args.model:
                    setup_kwargs["model"] = args.model
                if args.base_url:
                    setup_kwargs["base_url"] = args.base_url
                if args.api_key:
                    setup_kwargs["api_key"] = args.api_key
            
            # Run the setup wizard
            if setup_kwargs:
                result = run_setup_wizard(
                    mode=mode,
                    dotenv_path=args.dotenv_path,
                    dry_run=args.dry_run,
                    non_interactive=args.non_interactive,
                    **setup_kwargs
                )
            else:
                result = run_setup_wizard(
                    mode=mode,
                    dotenv_path=args.dotenv_path,
                    dry_run=args.dry_run,
                    non_interactive=args.non_interactive
                )
            
            # Print summary
            print("\nSetup completed successfully!")
            
            # Handle API key masking for output
            if hasattr(result, 'api_key') and result.api_key:
                masked_key = f"{'*' * 8}{result.api_key[-4:]}" if len(result.api_key) > 4 else "****"
                print(f"API Key: {masked_key}")
            
            if result.provider == "auto":
                print(f"Mode: Multi-provider with auto-selection")
                if result.auto_select_order:
                    print(f"Auto-select order: {', '.join(result.auto_select_order)}")
                if result.providers:
                    print(f"Configured providers: {', '.join(result.providers.keys())}")
            else:
                print(f"Provider: {result.provider}")
                # For mocks in tests, use direct attributes; for real results, use properties
                if hasattr(result, 'model') and result.model is not None:
                    print(f"Model: {result.model}")
                if hasattr(result, 'base_url') and result.base_url is not None:
                    print(f"Base URL: {result.base_url}")
            
            if not args.dry_run:
                # Use args.dotenv_path for printing (CLI contract)
                dotenv_str = args.dotenv_path
                print(f"Configuration written to: {dotenv_str}")
                if result.backup_created:
                    print(f"Backup created: {dotenv_str}.bak")
            else:
                # In dry-run mode, don't mention writing files
                pass
            
            if args.dry_run:
                print(f"\nDry run mode - no files were modified")
            
            print(f"\nTo use ai_utilities:")
            print(f"  import ai_utilities")
            if result.provider == "auto":
                print(f"  client = ai_utilities.AiClient()  # Auto-selects best provider")
            else:
                print(f"  client = ai_utilities.AiClient()  # Uses {result.provider}")
            
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
