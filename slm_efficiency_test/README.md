# Ollama OpenAI API Compatibility App

This application provides an interface to run inference using Ollama with OpenAI API compatibility. It allows you to use local language models through Ollama while maintaining the familiar OpenAI API interface.

## Features

- 🔄 **OpenAI-Compatible API**: Use the same interface you're familiar with from OpenAI
- 🤖 **Local Model Support**: Run inference on local models via Ollama
- 💬 **Chat Completions**: Support for conversation-style interactions
- 📝 **Text Completions**: Traditional text completion functionality
- 🌊 **Streaming Support**: Real-time response streaming
- 📊 **Usage Tracking**: Token usage statistics like OpenAI API
- 🔍 **Model Management**: List and manage available models

## Prerequisites

1. **Ollama Installation**: Install Ollama from [https://ollama.ai](https://ollama.ai)
2. **Python 3.7+**: Make sure you have Python installed
3. **Running Ollama**: Start the Ollama server

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
ollama serve
```

### 3. Pull a Model (if you haven't already)

```bash
ollama pull llama2
# or
ollama pull mistral
# or any other supported model
```

### 4. Run the Demo

```bash
python app.py
```

## Usage Examples

### Basic Chat Completion

```python
from app import OllamaOpenAICompatible

# Initialize client
client = OllamaOpenAICompatible()

# Chat completion
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"}
]

response = client.chat_completions(
    model="llama2",
    messages=messages,
    temperature=0.7,
    max_tokens=150
)

print(response['choices'][0]['message']['content'])
```

### Text Completion

```python
response = client.completions(
    model="llama2",
    prompt="The future of AI is",
    temperature=0.8,
    max_tokens=100
)

print(response['choices'][0]['text'])
```

### Streaming Response

```python
stream = client.chat_completions(
    model="llama2",
    messages=messages,
    stream=True
)

for chunk in stream:
    # Handle streaming data
    print(chunk, end='', flush=True)
```

### List Available Models

```python
models = client.list_models()
for model in models['data']:
    print(f"Model: {model['id']}")
```

## API Reference

### OllamaOpenAICompatible Class

#### Methods

- **`chat_completions(model, messages, temperature=0.7, max_tokens=None, stream=False, **kwargs)`**
  - Create chat completions with conversation context
  - Returns OpenAI-style response format

- **`completions(model, prompt, temperature=0.7, max_tokens=None, stream=False, **kwargs)`**
  - Create text completions from a prompt
  - Returns OpenAI-style response format

- **`list_models()`**
  - List all available models in Ollama
  - Returns OpenAI-style models list

- **`health_check()`**
  - Check if Ollama service is running
  - Returns boolean status

### Configuration

```python
from app import OllamaConfig, OllamaOpenAICompatible

config = OllamaConfig(
    base_url="http://localhost:11434",  # Ollama server URL
    default_model="llama2",             # Default model to use
    timeout=60                          # Request timeout in seconds
)

client = OllamaOpenAICompatible(config)
```

## Response Format

The API returns OpenAI-compatible response formats:

### Chat Completion Response
```json
{
    "id": "ollama-1234567890",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "llama2",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "Response text here"
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 25,
        "total_tokens": 35
    }
}
```

## Troubleshooting

### Common Issues

1. **"Ollama is not running"**
   - Make sure Ollama is started: `ollama serve`
   - Check if the service is accessible at `http://localhost:11434`

2. **"No models found"**
   - Pull a model first: `ollama pull llama2`
   - Verify models are available: `ollama list`

3. **Connection timeout**
   - Increase timeout in configuration
   - Check network connectivity to Ollama service

4. **Model not responding**
   - Ensure the model is properly loaded
   - Try with a smaller model if you have memory constraints

### Performance Tips

- Use smaller models for faster responses
- Adjust `max_tokens` to control response length
- Lower `temperature` for more deterministic outputs
- Use streaming for real-time applications

## Integration with Existing OpenAI Code

This app is designed to be a drop-in replacement for OpenAI API calls. You can replace your OpenAI client with this Ollama client while keeping the same API interface:

```python
# Instead of:
# import openai
# response = openai.ChatCompletion.create(...)

# Use:
from app import OllamaOpenAICompatible
client = OllamaOpenAICompatible()
response = client.chat_completions(...)
```

## Contributing

Feel free to submit issues and pull requests to improve this application.

## License

This project is open source and available under the MIT License.
