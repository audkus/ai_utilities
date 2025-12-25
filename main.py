# Add src to path for development usage (works both in repo and when installed)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_utilities import create_client, AiClient


def main() -> None:
    """
    Example usage of the ai_utilities v1 API with progress indicator.
    """
    print("=== AI Utilities v1 API Demo ===\n")
    
    try:
        # Create client with progress indicator (default: enabled)
        # Use a real OpenAI model for the demo
        client = create_client(model="gpt-4")
    except Exception as e:
        print(f"\n❌ Failed to initialize AI client: {e}")
        print("\nPlease ensure you have:")
        print("1. Set your OpenAI API key: export AI_API_KEY='your-key-here'")
        print("2. Or run the interactive setup to configure your settings")
        print("\nThe application will now exit.")
        return
    
    print("1. Single prompt with progress indicator (default):")
    prompt_single_text = "Who was the first human to walk on the moon?"
    result_single_text = client.ask(prompt_single_text)
    print(f"Question: {prompt_single_text}")
    print(f"Answer: {result_single_text}\n")

    print("2. Multiple prompts with progress indicator:")
    prompts_multiple_text = [
        "Who was the last person to walk on the moon?",
        "What is Kant's categorical imperative in simple terms?",
        "What is the Fibonacci sequence? do not include examples"
    ]

    results_multiple_text = client.ask_many(prompts_multiple_text)

    if results_multiple_text:
        for question, result in zip(prompts_multiple_text, results_multiple_text):
            print(f"Question: {question}")
            print(f"Answer: {result}\n")

    print("3. JSON format request with progress indicator:")
    prompt_single = "What are the current top 5 trends in AI, just the title? Please return the answer as a JSON format"
    result_single_json = client.ask_json(prompt_single)
    print(f"Question: {prompt_single}")
    print(f"Answer: {result_single_json}\n")

    print("4. Request without progress indicator:")
    # Create client with progress indicator disabled and real model
    client_no_progress = create_client(model="gpt-4", show_progress=False)
    prompt_custom_model = "What is the capital of France?"
    response = client_no_progress.ask(prompt_custom_model)
    print(f"Question: {prompt_custom_model}")
    print(f"Answer: {response}\n")

    print("5. Custom model with progress indicator:")
    response = client.ask("Explain quantum computing in simple terms")
    print(f"Answer: {response}\n")

    print("=== Demo Complete ===")

if __name__ == "__main__":
    main()
