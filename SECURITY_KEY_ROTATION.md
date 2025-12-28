# 🔒 OpenRouter API Key Security & Rotation Guide

## ⚠️ IMPORTANT: Key Exposure Detected

If your OpenRouter API key was exposed in git history, you **MUST** rotate it immediately.

## 🔄 How to Rotate Your API Key

### Step 1: Get a New API Key
1. Go to https://openrouter.ai/keys
2. Log in to your account
3. Revoke the old key (if exposed)
4. Create a new API key
5. Copy the new key (starts with `sk-or-v1-`)

### Step 2: Update Local Configuration

**Option A: Using .env file (Recommended)**
```bash
# Create or edit agents/.env file
cd agents
echo "OPENROUTER_API_KEY=sk-or-v1-YOUR-NEW-KEY-HERE" > .env
```

**Option B: Using Environment Variable**
```bash
# For current session
export OPENROUTER_API_KEY='sk-or-v1-YOUR-NEW-KEY-HERE'

# For permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENROUTER_API_KEY="sk-or-v1-YOUR-NEW-KEY-HERE"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Restart Services
```bash
# Stop agents service
pkill -f "uvicorn main:app"

# Restart with new key
cd agents
./start.sh
```

### Step 4: Verify New Key Works
```bash
cd agents
python3 test_openrouter.py
```

## 🛡️ Security Best Practices

1. **Never commit API keys to git**
   - ✅ Use `.env` files (already in `.gitignore`)
   - ✅ Use environment variables
   - ❌ Never hardcode in source files

2. **Check git history for exposed keys**
   ```bash
   git log --all --full-history -S "sk-or-" --source
   ```

3. **If keys were committed:**
   - Rotate the key immediately
   - Consider using `git-filter-repo` to remove from history
   - Or create a new repository without the history

## 📋 Current Status

✅ **Fixed Files:**
- `agents/main.py` - Only loads from environment (SECURE)
- `agents/test_openrouter.py` - Removed hardcoded fallback
- `agents/start.sh` - Now loads from env/.env only
- `.gitignore` - Properly excludes `.env` files

✅ **All hardcoded keys have been removed from the codebase.**

## 🔍 Verify Your Setup

```bash
# Check if key is set
echo $OPENROUTER_API_KEY

# Test the key
cd agents
python3 test_openrouter.py

# Check agents service health
curl http://localhost:8091/agents/health
```

## 📞 Need Help?

If you need to rotate your key or have security concerns:
1. Revoke old key at https://openrouter.ai/keys
2. Create new key
3. Update your local `.env` file
4. Restart services

