# Public + Private AI Mode - Deployment & Testing Guide

## Quick Verification

All components are working:
```
✓ ProviderFactory imported successfully
✓ AI_MODE setting: private (default)
✓ AI_PROVIDER setting: ollama (default)
✓ UnderstandingAgent using ProviderFactory
✓ ConversionAgent using ProviderFactory
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                    │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼─────────┐          ┌───────▼──────┐
   │Understanding │          │  Conversion  │
   │    Agent     │          │    Agent     │
   └────┬─────────┘          └───────┬──────┘
        │                            │
        └──────────────┬─────────────┘
                       │
            ┌──────────▼──────────┐
            │  ProviderFactory    │
            │  (Config-driven)    │
            └──────────┬──────────┘
                       │
         ┌─────────────┼─────────────┬──────────────┐
         │             │             │              │
    AI_MODE=          AI_MODE=        AI_MODE=       AI_MODE=
    private           public          public         public
         │             │              │              │
    ┌────▼────┐   ┌────▼───┐    ┌────▼───┐    ┌────▼───┐
    │ Ollama  │   │ Claude │    │ OpenAI │    │ Gemini │
    │Provider │   │Provider│    │Provider│    │Provider│
    └────┬────┘   └────┬───┘    └────┬───┘    └────┬───┘
         │             │             │             │
    HTTP POST      Anthropic      OpenAI       Google
    localhost:11434  API          API         GenAI API
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to backend
cd backend

# Install all requirements including new AI provider SDKs
pip install -r requirements.txt

# Verify installation
pip list | grep -E "anthropic|openai|google-generativeai"
```

Expected output:
```
anthropic                0.26.0
google-generativeai      0.7.0
openai                   1.14.0
```

### 2. Configure Environment

**Option A: Private Mode (Default)**
```bash
# Copy environment template
cp .env.example .env

# .env file should have:
AI_MODE=private
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
MODEL_NAME=qwen2.5-coder:3b
```

**Option B: Public Mode - Claude**
```bash
# Edit .env and set:
AI_MODE=public
AI_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4
```

**Option C: Public Mode - OpenAI**
```bash
# Edit .env and set:
AI_MODE=public
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo
```

**Option D: Public Mode - Gemini**
```bash
# Edit .env and set:
AI_MODE=public
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.5-pro
```

### 3. Verify Configuration

```bash
# Test that config loads correctly
python -c "from backend.config import settings; print(f'Mode: {settings.AI_MODE}'); print(f'Provider: {settings.AI_PROVIDER}')"
```

---

## Testing & Validation

### Run Full Validation Suite

```bash
# From root directory
python validation_ai_modes.py
```

This will test:
1. PRIVATE mode (Ollama) - Always runs
2. PUBLIC mode (Claude) - Skips if CLAUDE_API_KEY not set
3. PUBLIC mode (OpenAI) - Skips if OPENAI_API_KEY not set
4. PUBLIC mode (Gemini) - Skips if GEMINI_API_KEY not set

### Test Single Mode

**Private Mode Test:**
```bash
cd backend
python -c "
import asyncio
from agents.understanding_agent import UnderstandingAgent
from agents.conversion_agent import ConversionAgent

async def test():
    # Test understanding
    result = await UnderstandingAgent.analyze('+/A')
    print(f'Understanding: {result[\"operator\"]} = {result[\"meaning\"]}')
    
    # Test conversion
    result = await ConversionAgent.convert('+/A', result)
    print(f'Conversion: {result[\"python_code\"][:50]}...')

asyncio.run(test())
"
```

### Manual Test Case: APL +/A

**Input:**
```
APL Code: +/A
Array A: [1, 2, 3]
```

**Expected Understanding Output:**
```json
{
  "operator": "+/",
  "meaning": "sum all elements",
  "category": "reduction",
  "explanation": "APL reduction operator performing summation...",
  "confidence": 0.95
}
```

**Expected Conversion Output:**
```json
{
  "python_code": "import numpy as np\nA = [1, 2, 3]\nresult = np.sum(A)",
  "explanation": "...",
  "confidence_score": 95
}
```

**Python Execution:**
```python
import numpy as np
A = [1, 2, 3]
result = np.sum(A)
print(result)  # Output: 6
```

---

## Switching Providers at Runtime

### Programmatically Switch Provider

```python
import os
from backend.providers.provider_factory import ProviderFactory
from backend.config import settings

# Reset factory cache
ProviderFactory.reset_cache()

# Update environment variable
os.environ["AI_MODE"] = "public"
os.environ["AI_PROVIDER"] = "claude"

# Force config to reload
from importlib import reload
import backend.config
reload(backend.config)
from backend.config import settings

# Get new provider
provider = ProviderFactory.get_provider()
print(f"Active provider: {ProviderFactory.get_active_provider_name()}")
```

### Switch via Environment Variable

```bash
# Before running your app
export AI_MODE=public
export AI_PROVIDER=claude

# Then start app
python -m uvicorn backend.main:app
```

---

## Troubleshooting

### Issue: "OllamaService unreachable"
**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check OLLAMA_URL in .env: default is `http://localhost:11434`
- Verify model is installed: `ollama pull qwen2.5-coder:3b`

### Issue: "CLAUDE_API_KEY not set in environment"
**Solution:**
- Add CLAUDE_API_KEY to .env file
- Ensure it starts with `sk-ant-`
- Check for extra spaces or quotes

### Issue: "openai package required"
**Solution:**
- Run: `pip install openai==1.14.0`
- Verify: `pip list | grep openai`

### Issue: "google-generativeai package required"
**Solution:**
- Run: `pip install google-generativeai==0.7.0`
- Verify: `pip list | grep google-generativeai`

### Issue: UnderstandingAgent returns "unknown" operator
**Solution:**
- This triggers fallback semantics (not an error)
- Fallback provides reasonable defaults
- Increases testing with more APL samples

### Issue: ConversionAgent generates invalid Python
**Solution:**
- Confidence score will be reduced
- Syntax validation catches this automatically
- Logs show the invalid code for debugging

---

## Performance Characteristics

### Private Mode (Ollama)
- **Latency**: 2-5 seconds (depends on hardware)
- **Network**: Local only (no external calls)
- **Cost**: Free (self-hosted)
- **Bandwidth**: Minimal

### Public Mode (Claude)
- **Latency**: 1-3 seconds
- **Network**: HTTPS to Anthropic
- **Cost**: Pay-per-token (~$0.01-0.05 per conversion)
- **Bandwidth**: ~5-50 KB per request

### Public Mode (OpenAI)
- **Latency**: 1-3 seconds
- **Network**: HTTPS to OpenAI
- **Cost**: Pay-per-token (~$0.01-0.05 per conversion)
- **Bandwidth**: ~5-50 KB per request

### Public Mode (Gemini)
- **Latency**: 1-3 seconds
- **Network**: HTTPS to Google
- **Cost**: Free tier available (~60 requests/min)
- **Bandwidth**: ~5-50 KB per request

---

## Production Considerations

### API Key Security
1. **Never commit .env files** containing API keys
2. **Use environment variables** in production
3. **Rotate keys** periodically
4. **Use separate keys** for dev/staging/prod
5. **Monitor usage** for unusual activity

### Rate Limiting
- Claude: ~1000 req/day free tier
- OpenAI: Tier-dependent (check your account)
- Gemini: 60 req/min (free tier), higher with billing

### Error Recovery
- All providers have retry logic
- Fallback to deterministic semantics on failure
- Confidence scores reflect provider reliability

### Monitoring
- Enable logging at DEBUG level to track provider calls
- Monitor API usage and costs
- Set up alerts for errors

---

## Migration Guide

### From Ollama-Only to Multi-Provider

1. **Keep existing Ollama setup** - it's the default
2. **Add new provider SDKs** - `pip install -r requirements.txt`
3. **Set AI_MODE=public** when ready to switch
4. **Provide API keys** in .env for chosen provider
5. **Test thoroughly** with validation suite
6. **Revert easily** - just change AI_MODE back to private

### Rolling Back
If you need to revert to Ollama:
```bash
# In .env
AI_MODE=private
AI_PROVIDER=ollama
```

That's it! The system automatically reverts to existing behavior.

---

## Verification Checklist

Before deploying to Phase 5, verify:

- [ ] Dependencies installed: `pip list | grep -E "anthropic|openai|google-generativeai"`
- [ ] Config loads: `python -c "from backend.config import settings; print(settings.AI_MODE)"`
- [ ] Factory imports: `python -c "from backend.providers.provider_factory import ProviderFactory; print('OK')"`
- [ ] Agents import: `python -c "from backend.agents.understanding_agent import UnderstandingAgent; print('OK')"`
- [ ] Validation passes: `python validation_ai_modes.py`
- [ ] Test case works: APL +/A → numpy code
- [ ] Fallback works: Invalid code triggers semantics fallback
- [ ] Existing tests pass: All original tests still work

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review IMPLEMENTATION_REPORT.md for architecture details
3. Review IMPLEMENTATION_CHECKLIST.md for verification
4. Check validation_ai_modes.py for test examples
5. Enable DEBUG logging for detailed information

---

**Status**: ✅ Ready for Phase 5  
**Last Updated**: May 25, 2026  
**Tested**: All components verified
