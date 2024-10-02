from ai_utilities.ai_integration import ask_ai


def main() -> None:
    """
    Example usage of the ai_integration module.
    """
    prompt_single_text = "Who was the first human to walk on the moon?"
    result_single_text = ask_ai(prompt_single_text)
    print(f'# Example with a single prompt:\nQuestion: {prompt_single_text}:\nAnswer:{result_single_text}\n')

    prompts_multiple_text = [
        "Who was the last person to walk on the moon?",
        "What is Kant’s categorical imperative in simple terms?",
        "What is the Fibonacci sequence? do not include examples"
    ]

    print(f'# Example with multiple prompts:\n{prompts_multiple_text}\n')
    results_multiple_text = ask_ai(prompts_multiple_text)

    if results_multiple_text:
        for question, result in zip(prompts_multiple_text, results_multiple_text):
            print(f"Question: {question}")
            print(f"Answer: {result}\n")

    print(f'\n# Example with a single prompt in JSON format:\n')
    prompt_single = "What are the current top 5 trends in AI, just the title? Please return the answer as a JSON format"
    return_format = "json"
    result_single_json = ask_ai(prompt_single, return_format)
    print(f'\nQuestion: {prompt_single}\nAnswer: {result_single_json}')


if __name__ == "__main__":
    main()
