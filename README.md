# AI Utilities

## Overview

The `ai_utilities` project provides a simple interface for interacting with AI models such as OpenAI's GPT models. The project makes it easy to send prompts to AI models and receive responses using just one function: `ask_ai`. It also includes built-in threading support for efficiently handling multiple prompts, allowing users to get quick responses.

The project comes with optional configuration management to customize AI provider settings and built-in rate limiting to ensure API usage stays within defined limits.

### Key Features:
- **Simple AI Model Interaction**: Just use `ask_ai` to send prompts and get responses with minimal setup.
- **Support for Multiple Prompts**: When sending multiple prompts, the app leverages threading to deliver faster responses.
- **Customizable Configurations**: You can configure AI models, providers, and rate limits through a `config.ini` file.
- **Rate Limiting**: Built-in protection to keep API requests and token usage within predefined limits.

---

## External Libraries and Models

The `ai_utilities` project integrates with several external models and libraries to provide functionality such as AI interaction, system monitoring, and configuration management.

### 1. OpenAI Models

We use OpenAI's models for generating responses to user prompts. The models are accessed via OpenAI's public API, and you can select which model to use by setting the appropriate values in the configuration file (`config.ini`).

#### Models Supported:
- **GPT-4**: A large language model from OpenAI.
- **GPT-3.5-Turbo**: A smaller, faster version of GPT-4 that still provides high-quality results.

#### Setup and API Key

To use OpenAI's models, you will need an API key from OpenAI. To set this up:

1. Sign up at [OpenAI’s website](https://beta.openai.com/signup/) and obtain an API key.
2. Set the API key as an environment variable on your system:
   - **For Linux/Mac**:
     ```bash
     export OPENAI_API_KEY='your-api-key-here'
     ```
   - **For Windows**:
     ```bash
     setx OPENAI_API_KEY "your-api-key-here"
     ```

**N.B.** You probably need to restart your IDE for this to take effect.

#### Licensing and Usage Limits

- OpenAI's GPT models are licensed under OpenAI’s [terms of service](https://beta.openai.com/terms).
- The API has rate limits (Requests per Minute, Tokens per Minute, Tokens per Day), and you are responsible for managing your usage within these limits. These limits can be configured in the `config.ini` file under the relevant model section.
- OpenAI charges for API usage, and you should review their [pricing](https://openai.com/pricing) to understand the costs involved.

---

### 2. `psutil` (System and Process Utilities)

The `psutil` library is used in this project to monitor system performance and memory usage, especially when running multiple tasks or interacting with AI models that require heavy computation.

#### Features of `psutil` used in this project:
- **Memory Monitoring**: The app uses `psutil` to track system memory usage and trigger warnings if memory exceeds a certain threshold.
- **Process Monitoring**: The library is also used to monitor and manage concurrent API requests in a multithreaded environment.

#### Installation:
`psutil` is automatically installed with this project as a dependency, but you can manually install it using:

```bash
pip install psutil
```

#### Documentation and License:
- Official `psutil` documentation: [psutil Documentation](https://psutil.readthedocs.io/)
- Licensed under the BSD license: [psutil License](https://github.com/giampaolo/psutil/blob/master/LICENSE)

---

### 3. `config_utilities` (Configuration Management)

The `config_utilities` package is used to handle the configuration management in this project, ensuring that settings such as AI provider configurations and logging setups are consistent across different parts of the app.

#### Source:
This library is located in a separate repository: [config_utilities @ GitHub](https://github.com/audkus/config_utilities.git). It is automatically installed as a dependency when you install `ai_utilities`.

#### Key Features of `config_utilities`:
- **Configuration Loading**: Ensures that the app loads and validates the configuration from a central `config.ini` file.
- **Default Values**: Sets default values for configuration settings, such as logging and AI usage.
- **Flexible Configuration**: Allows developers to customize configurations for different environments (e.g., development, production).

#### Installation:

You do not need to manually install `config_utilities` as it is automatically installed as part of `ai_utilities`. However, if you want to install it separately, you can do so via pip:

```bash
pip install git+https://github.com/audkus/config_utilities.git
```

#### License:
- Check the repository for licensing information: [config_utilities License](https://github.com/audkus/config_utilities).

---

### Usage Example

To demonstrate how these external libraries work together, here’s an example workflow:

1. **AI Model Interaction**: Using OpenAI's GPT models via the `ask_ai` function.
2. **System Monitoring**: Using `psutil` to monitor memory usage and avoid exceeding system limits.
3. **Configuration Management**: Using `config_utilities` to load AI settings and ensure correct configurations across environments.

```python
import psutil
from ai_utilities.ai_integration import ask_ai
from config_utilities.config_manager import load_and_validate_config

def main() -> None:
    # Monitor memory usage
    memory_usage = psutil.virtual_memory().percent
    print(f"Current memory usage: {memory_usage}%")

    # Load configuration using config_utilities
    config, config_path = load_and_validate_config()

    # Ask AI using OpenAI models
    response = ask_ai("What are the current trends in AI?")
    print(response)

if __name__ == "__main__":
    main()
```

---

## Quick Start Guide

### Installation

You can install the project directly from GitHub:

```bash
pip install git+https://github.com/audkus/ai_utilities.git
```

### Setting Up the API Key

Before using the app, you need to set up the **OpenAI API key** on your computer:

1. **Obtain an API Key** from OpenAI at [OpenAI's API website](https://beta.openai.com/signup/).
2. Set the API key as an environment variable on your system:
   
   - **For Linux/Mac**:
     ```bash
     export OPENAI_API_KEY='your-api-key-here'
     ```

   - **For Windows**:
     ```bash
     setx OPENAI_API_KEY "your-api-key-here"
     ```

3. Make sure that your environment variable is correctly set up and available for the app.

---

## Examples

Below are three runnable examples that you can copy and paste directly into your project modules.

### 1. Single Prompt Example

This example sends a single prompt to the AI model and prints the response.

```python
from ai_utilities.ai_integration import ask_ai

def main() -> None:
    prompt_single_text = "What are the current top 2 trends in AI?"
    result_single_text = ask_ai(prompt_single_text)
    print(f'\nExample with a single prompt:\n{result_single_text}')

if __name__ == "__main__":
    main()
```

### 2. Multiple Prompts Example

This example demonstrates how to send multiple prompts. The app takes advantage of threading to get quick responses.

```python
from ai_utilities.ai_integration import ask_ai

def main() -> None:
    prompts_multiple_text = [
        "What are the current top 2 trends in AI?",
        "Tell me a joke about artificial intelligence.",
        "What is the most important AI development in 2023?"
    ]
    results_multiple_text = ask_ai(prompts_multiple_text)
    print(f'\nExample with multiple prompts:')
    for result in results_multiple_text:
        print(result)

if __name__ == "__main__":
    main()
```

### 3. JSON Response Example

If you need a response in JSON format, you can request that from the AI model using the `return_format` parameter.

```python
from ai_utilities.ai_integration import ask_ai

def main() -> None:
    prompt_json = "What are the current top 2 trends in AI, return the answer as JSON format."
    result_json = ask_ai(prompt_json, return_format="json")
    print(f'\nExample with a JSON response:\n{result_json}')

if __name__ == "__main__":
    main()
```

---

## AI Model Interaction

### `ask_ai`: The Core Function

The primary function to interact with the AI model is `ask_ai`. It simplifies sending prompts to the AI model and getting responses with minimal setup. The function supports both single prompts and multiple prompts and can return responses in text or JSON format.

#### **How `ask_ai` Works**

- **Single Prompt**: Sends a prompt to the AI and returns the response.
- **Multiple Prompts**: Sends multiple prompts simultaneously using threading, providing quicker results.
- **Return Format**: You can specify the `return_format` as either `'text'` or `'json'`.

   - **When `return_format='json'`**: The function will **attempt** to extract and return only the JSON portion of the response from the AI. However, this depends on the AI's output. If the AI does not provide a JSON response (even when requested), the entire response (pre-text and post-text included) is returned as is.
   - **No JSON Validation**: The app **does not validate** the JSON format of the returned data. It is up to the developer to add any necessary validation to the result, if required.

   **Note**: The prompt itself should indicate that a JSON-formatted answer is expected. If no JSON is found in the AI's response, the entire text response will be returned.

#### Example:

```python
from ai_utilities.ai_integration import ask_ai

response = ask_ai("What is artificial intelligence?")
print(response)

json_response = ask_ai("Return the top 2 AI trends in JSON format", return_format="json")
print(json_response)
```

In the first case, the AI returns a text response. In the second case, if the AI responds with JSON, the app will extract and return only the JSON part. If no valid JSON is found, the entire response is returned.

---

## Configuration Management (Optional)

While the `ask_ai` function works out-of-the-box, you can customize the AI provider and model settings via the `config.ini` file. The `ai_config_manager.py` module provides utility functions to manage and customize these settings.

### Configuration File (`config.ini`)

The default configuration file looks like this:

```ini
[AI]
use_ai = true
ai_provider = openai

[openai]
model = gpt-4
api_key = OPENAI_API_KEY

[gpt-4]
requests_per_minute = 5000
tokens_per_minute = 450000
tokens_per_day = 1350000
```

You can adjust the API key, model, or rate limits by modifying this file. Use the following functions from `ai_config_manager` to set or update these configurations:

#### Key Functions:
1. **`set_default_ai_config(config)`**: Sets the default AI provider and model configurations.
2. **`get_model_from_config(config, config_path)`**: Retrieves the AI model based on the configuration settings.

Example:

```python
from ai_utilities.ai_config_manager import set_default_ai_config, get_model_from_config

config = configparser.ConfigParser()
set_default_ai_config(config)
model = get_model_from_config(config, "../config.ini")
if model:
    print(model.ask_ai("Tell me a joke"))
```

### Function: `is_ai_usage_enabled`

Checks if AI usage is enabled based on the use_ai setting in the config.ini file.

**Parameters:**
- `config` (`configparser.ConfigParser`): Configuration object containing settings.

**Returns:**
- `bool`: `True` if AI usage is enabled in the configuration, `False` otherwise.

**Example Usage:**
```python
import configparser
from ai_integration import is_ai_usage_enabled

# Load configuration from file
config = configparser.ConfigParser()
config.read('config.ini')

# Check if AI usage is enabled
if is_ai_usage_enabled(config):
    print("AI usage is enabled.")
else:
    print("AI usage is disabled.")
```

---

## Rate Limiting (Internal)

The `rate_limiter.py` module enforces limits on API usage, ensuring that the app stays within the requests and tokens per minute and day allowed by the API provider.

While rate limiting is handled internally, you can customize the rate limits by modifying the `config.ini` file:

```ini
[gpt-4]
requests_per_minute = 5000
tokens_per_minute = 450000
tokens_per_day = 1350000
```

---

## Best Practices

1. **Use `ask_ai` for Simplicity**: The `ask_ai` function is the easiest way to interact with AI models. Use it for both single and multiple prompts.
2. **Multiple Prompts**: Leverage the built-in threading feature of `ask_ai` to send multiple prompts and get responses faster.
3. **Return Format**: Use the `return_format="json"` option when you need structured JSON responses, but ensure your prompt requests JSON explicitly, and handle validation yourself if needed.
4. **Customize AI Settings**: If you need to use a different AI provider or model, customize the `config.ini` file with your preferred settings.

---

## Conclusion

The `ai_utilities` project offers a simple and flexible way to interact with AI models in Python. The core `ask_ai` function allows you to quickly send prompts and receive responses, with support for both single and multiple prompts. Advanced users can customize the AI configurations and rate limits via the `config.ini` file.

This project integrates OpenAI models, `psutil` for system monitoring, and `config_utilities` for configuration management. These external models and libraries provide flexibility, monitoring, and control to ensure smooth interaction with AI models and efficient resource usage.

Feel free to contribute to the project by submitting issues or pull requests on [GitHub](https://github.com/audkus/ai_utilities).
