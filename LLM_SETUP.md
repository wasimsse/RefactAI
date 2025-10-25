# LLM Setup Guide for RefactAI

## Issue Summary

The LLM refactoring feature is returning a **400 error** because the OpenRouter API key is not configured. The backend is trying to authenticate with OpenRouter but receiving a **401 Unauthorized** response.

## Root Cause

In `/backend/server/src/main/resources/application.yml`, the configuration reads:

```yaml
llm:
  openrouter:
    api-key: ${OPENROUTER_API_KEY:}
```

This means the backend expects an environment variable `OPENROUTER_API_KEY` to be set. When it's not set, the API key is empty, causing authentication to fail.

## Solutions

### Option 1: Set the OpenRouter API Key (Production)

1. **Get an OpenRouter API Key:**
   - Visit [OpenRouter.ai](https://openrouter.ai/)
   - Sign up for an account
   - Generate an API key from your dashboard

2. **Set the environment variable:**

   **On macOS/Linux:**
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-YOUR-API-KEY-HERE"
   ```

   **On Windows (PowerShell):**
   ```powershell
   $env:OPENROUTER_API_KEY="sk-or-v1-YOUR-API-KEY-HERE"
   ```

3. **Restart the backend server:**
   ```bash
   cd backend/server
   mvn spring-boot:run
   ```

### Option 2: Use a Local LLM Provider (No API Key Required)

If you want to avoid cloud-based LLMs and API costs, you can configure a local LLM:

1. **Install Ollama** (local LLM runtime):
   ```bash
   # macOS
   brew install ollama
   
   # Or download from https://ollama.ai
   ```

2. **Pull a model:**
   ```bash
   ollama pull codellama
   # or
   ollama pull mistral
   ```

3. **Update the backend configuration** to use Ollama instead of OpenRouter (modify `backend/server/src/main/resources/application.yml`):
   ```yaml
   llm:
     openrouter:
       base-url: http://localhost:11434/v1  # Ollama endpoint
       api-key: "not-required"  # Ollama doesn't need auth
   ```

### Option 3: Development Mode with Mock Responses

For development and testing without an LLM, the application now provides graceful fallback responses. The changes made include:

1. **Better error messages** - The backend now returns a 503 status with a clear error message
2. **Frontend fallback** - The frontend displays a helpful error and continues with mock refactoring

The error will now show:
```
⚠️ LLM service not configured: Please set the OPENROUTER_API_KEY environment variable
```

And the refactoring will continue using the rule-based fallback system.

## Verifying the Setup

1. **Check if the environment variable is set:**
   ```bash
   echo $OPENROUTER_API_KEY
   ```

2. **Test the LLM endpoint:**
   ```bash
   curl -X POST http://localhost:8080/api/llm/refactoring \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "user", "content": "Hello"}
       ],
       "model": "openai/gpt-4",
       "maxTokens": 100
     }'
   ```

   If configured correctly, you should receive a response. If not, you'll see the error message.

3. **Check the backend logs:**
   ```bash
   tail -f backend/server/logs/refactai-server.log
   ```

## Cost Considerations

OpenRouter charges based on token usage. The current configuration has:
- Daily limit: $10.00
- Monthly limit: $100.00

You can adjust these in the `application.yml` file:
```yaml
llm:
  cost:
    daily-limit: 10.0
    monthly-limit: 100.0
```

## Next Steps

1. Choose one of the options above
2. Configure your environment
3. Restart the backend server
4. Test the refactoring feature again

## Support

If you encounter issues:
- Check backend logs: `backend/server/logs/refactai-server.log`
- Check frontend console for detailed error messages
- Verify the API key is valid and has sufficient credits

