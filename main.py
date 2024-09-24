from ai_utilities.ai_integration import ask_ai


def main() -> None:
    """
    Example usage of the ai_integration module.
    """
    prompt_single_text = "What are the current top 2 trends in AI?"
    result_single_text = ask_ai(prompt_single_text)
    print(f'Example with a single prompt:\n{result_single_text}')

    prompts_multiple_text = [
        "Hello, how are you?",
        "What are your plans for today?",
        "Tell me about your favorite book."
    ]
    results_multiple_text = ask_ai(prompts_multiple_text)
    print(f'Example with multiple prompts:')
    if results_multiple_text:
        for result in results_multiple_text:
            print(result)

    prompt_single = "What are the current top 2 trends in AI, just the title? Please return the answer as a JSON format"

    return_format = "json"

    result_single_json = ask_ai(prompt_single, return_format)
    print(f'\nExample with a single prompt in JSON format: \n{result_single_json}')


if __name__ == "__main__":
    main()