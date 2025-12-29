"""
Menu rendering and user interaction utilities.

Handles model selection and scenario menu display with proper sorting.
"""

from __future__ import annotations

from typing import List, Optional

from .validation import ValidatedModel


def render_model_menu(validated_models: List[ValidatedModel]) -> None:
    """Render the model selection menu with status indicators.
    
    Args:
        validated_models: List of validated models to display.
    """
    print("\n" + "="*60)
    print("🤖 SELECT AI MODEL")
    print("="*60)
    print("Choose an AI model to use for the demo scenarios:\n")
    
    # Display models with status indicators
    for i, model in enumerate(validated_models, 1):
        status_icon = _get_status_icon(model.status.value)
        status_detail = model.status_detail
        
        # Truncate long model names for better display
        display_line = model.menu_line_text
        if len(display_line) > 45:
            display_line = display_line[:42] + "..."
        
        # Pad for alignment
        padding = " " * (45 - len(display_line))
        print(f"  [{i}] {display_line}{padding} {status_icon} {status_detail}")
    
    print()
    print("Status: ✅ ready  ⚠ needs setup  ❌ not available")
    print()


def render_scenario_menu(selected_model: ValidatedModel) -> None:
    """Render the scenario menu for the selected model.
    
    Args:
        selected_model: The currently selected model.
    """
    print("\n" + "="*60)
    print("🎯 SELECT SCENARIO")
    print("="*60)
    print(f"Using model: {selected_model.menu_line_text}")
    print("Choose a scenario to run:\n")
    
    print("📚 BASIC EXAMPLES:")
    print("   1. 💬 Basic Chat")
    print("   2. 📋 JSON Response") 
    print("   3. 🔧 Typed Response (Pydantic)")
    print()
    print("⚡ ADVANCED EXAMPLES:")
    print("   4. 🌐 Provider Comparison")
    print("   5. 🌍 Real-World Examples")
    print("   6. ⚠️  Error Handling Examples")
    print()
    print("🔧 UTILITIES:")
    print("   7. 🔍 Re-validate selected model")
    print("   8. 🔄 Change model")
    print()
    print("   0. ❌ Exit")
    print()


def prompt_model_choice(validated_models: List[ValidatedModel]) -> Optional[int]:
    """Prompt user to select a model from the list.
    
    Args:
        validated_models: List of available models.
        
    Returns:
        Selected model index (1-based) or None if invalid.
    """
    while True:
        try:
            choice_input = input("Enter your choice (0-{}): ".format(len(validated_models))).strip()
            
            # Handle empty input
            if not choice_input:
                print("❌ Please enter a number between 0 and {}".format(len(validated_models)))
                continue
                
            # Handle numeric input
            if choice_input.isdigit():
                choice = int(choice_input)
                if 0 <= choice <= len(validated_models):
                    return choice if choice != 0 else None
                else:
                    print("❌ Please enter a number between 0 and {}".format(len(validated_models)))
            else:
                print("❌ Please enter a valid number")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None
        except EOFError:
            print("\n👋 Goodbye!")
            return None
        except Exception as e:
            print(f"❌ Invalid input: {e}. Please try again.")


def prompt_scenario_choice() -> Optional[int]:
    """Prompt user to select a scenario.
    
    Returns:
        Selected scenario number or None if invalid.
    """
    while True:
        try:
            choice_input = input("Enter your choice (0-8): ").strip()
            
            # Handle empty input
            if not choice_input:
                print("❌ Please enter a number between 0 and 8")
                continue
                
            # Handle numeric input
            if choice_input.isdigit():
                choice = int(choice_input)
                if 0 <= choice <= 8:
                    return choice if choice != 0 else None
                else:
                    print("❌ Please enter a number between 0 and 8")
            else:
                print("❌ Please enter a valid number")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None
        except EOFError:
            print("\n👋 Goodbye!")
            return None
        except Exception as e:
            print(f"❌ Invalid input: {e}. Please try again.")


def sort_models_alphabetically(models: List[ValidatedModel]) -> List[ValidatedModel]:
    """Sort models alphabetically by menu_line_text (case-insensitive).
    
    Args:
        models: List of validated models to sort.
        
    Returns:
        Sorted list of models.
    """
    return sorted(models, key=lambda m: m.menu_line_text.lower())


def _get_status_icon(status: str) -> str:
    """Get status icon for display.
    
    Args:
        status: Model status value.
        
    Returns:
        Status icon character.
    """
    status_icons = {
        "ready": "✅",
        "needs_key": "⚠",
        "unreachable": "❌",
        "invalid_model": "❌",
        "error": "❌"
    }
    return status_icons.get(status, "❓")
