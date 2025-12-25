import sys
from pathlib import Path

# Add src and tests to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from ai_utilities import AiClient, AiSettings
from fake_provider import FakeProvider

def main() -> None:
    """
    Test the v1 API with fake provider (no OpenAI API needed).
    """
    # Create client with fake provider for testing
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider)
    
    prompt_single_text = "Who was the first human to walk on the moon?"
    result_single_text = client.ask(prompt_single_text)
    print(f'# Example with a single prompt:\nQuestion: {prompt_single_text}:\nAnswer:{result_single_text}\n')

    prompts_multiple_text = [
        "Who was the last person to walk on the moon?",
        "What is Kant's categorical imperative in simple terms?",
        "What is the Fibonacci sequence? do not include examples"
    ]

    print(f'# Example with multiple prompts:\n{prompts_multiple_text}\n')
    results_multiple_text = client.ask_many(prompts_multiple_text)

    if results_multiple_text:
        for question, result in zip(prompts_multiple_text, results_multiple_text):
            print(f"Question: {question}")
            print(f"Answer: {result}\n")

    print(f'\n# Example with a single prompt in JSON format:\n')
    prompt_single = "What are the current top 5 trends in AI, just the title? Please return the answer as a JSON format"
    result_single_json = client.ask_json(prompt_single)
    print(f'\nQuestion: {prompt_single}\nAnswer: {result_single_json}')

    print(f'\n# Example using a custom model "gpt-3.5-turbo":\n')
    prompt_custom_model = "What is the capital of France?"
    response = client.ask(prompt_custom_model, model="gpt-3.5-turbo")
    print(f'\nQuestion: {prompt_custom_model}\nAnswer: \n{response}')

if __name__ == "__main__":
    main()
