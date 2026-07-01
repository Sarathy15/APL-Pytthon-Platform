# 🚀 APL Migration Platform - Complete Startup Guide

## Quick Start (Windows)

### Option 1: Automated Startup (Recommended)
```bash
# Run the batch script
RUN.bat
```

This will:
1. ✅ Check for .env file (create if missing)
2. ✅ Install all Python dependencies
3. ✅ Install all Node.js dependencies
4. ✅ Start backend server on port 8000
5. ✅ Start frontend server on port 3000

**Then open**: http://localhost:3000

---

### Option 2: Manual Startup

#### Terminal 1 - Backend
```bash
# Install dependencies (first time only)
pip install -r backend/requirements.txt

# Start backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: **http://localhost:8000**
API Documentation: **http://localhost:8000/docs**

#### Terminal 2 - Frontend
```bash
# Install dependencies (first time only)
npm install

# Start frontend
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
│                  http://localhost:3000                  │
└────────────────────┬────────────────────────────────────┘
                     │ (API Calls to /api/*)
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 Backend (FastAPI)                       │
│                 http://localhost:8000                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  /api/understand     → Understanding Agent             │
│  /api/convert        → Conversion Agent                │
│  /api/validate/apl   → APL Execution Runner            │
│  /api/validate/python → Python Execution Runner        │
│  /api/compare        → Comparator Engine               │
│  /api/health         → Health Check                    │
│                                                         │
└──────────┬──────────────────┬──────────────────┬────────┘
           │                  │                  │
           ↓                  ↓                  ↓
    ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
    │ Gemini API   │  │ Ollama Local │  │ Dyalog APL  │
    │ (Public)     │  │ (Private)    │  │ (Execution) │
    └──────────────┘  └──────────────┘  └─────────────┘
```

---

## Usage Flow

### Step 1: Open Frontend
```
http://localhost:3000
```

### Step 2: Navigate to "Upload" Tab
- Left sidebar → Click "Upload"
- Or use the file upload in dashboard

### Step 3: Enter APL Code
In the code editor (bottom right), enter APL code:
```apl
⍝ Example 1: Sum reduction
+/A

⍝ Example 2: Product reduction
×/A

⍝ Example 3: Maximum
⌈/A
```

### Step 4: Select Mode

**Public Mode (Gemini - Recommended for testing)**
- Uses Google Gemini API
- Requires internet connection
- API key already configured in .env
- Works immediately ✅

**Private Mode (Ollama - For local inference)**
- Requires Ollama installed locally
- No API keys needed
- More privacy
- Slower than cloud providers

### Step 5: Click "INITIATE MIGRATION"
- Frontend will show processing steps:
  1. ⚙️ LVM Understanding
  2. ⚙️ Vector Conversion
  3. ⚙️ Security Validation
  4. ⚙️ Compliance Index

### Step 6: View Results
After processing, you'll see:
- **APL Source**: Original code
- **Python Code**: Generated conversion
- **Metrics**: Confidence, complexity, validation status
- **Reasoning Trace**: How the conversion was made

---

## Environment Configuration

### Current Configuration (.env)
```
AI_MODE="public"        # Use Gemini (public) or Ollama (private)
AI_PROVIDER="gemini"    # gemini, ollama, claude, or openai
GEMINI_API_KEY="..."    # Already configured ✅
```

### Change to Private Mode (Ollama)

1. **Install Ollama**:
   - Download from https://ollama.ai
   - Run: `ollama serve`

2. **Pull Model**:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```

3. **Update .env**:
   ```
   AI_MODE="private"
   AI_PROVIDER="ollama"
   OLLAMA_URL="http://localhost:11434"
   ```

4. **Restart backend**

---

## API Reference

### 1. Understand APL
**Endpoint**: `POST /api/understand`

**Request**:
```json
{
  "apl_code": "+/A"
}
```

**Response**:
```json
{
  "operator": "+/",
  "meaning": "sum all elements",
  "category": "reduction",
  "explanation": "APL reduction operator performing summation",
  "confidence": 0.95
}
```

---

### 2. Convert to Python
**Endpoint**: `POST /api/convert`

**Request**:
```json
{
  "apl_code": "+/A",
  "understanding": {
    "operator": "+/",
    "meaning": "sum all elements",
    ...
  }
}
```

**Response**:
```json
{
  "python_code": "import numpy as np\nresult = np.sum(A)",
  "explanation": "Conversion uses NumPy sum for array reduction",
  "confidence_score": 0.92,
  "syntax_valid": true
}
```

---

### 3. Execute APL
**Endpoint**: `POST /api/validate/apl`

**Request**:
```json
{
  "apl_code": "+/A",
  "test_cases": [1, 2, 3]
}
```

**Response**:
```json
{
  "status": "success",
  "output": 6,
  "output_type": "scalar"
}
```

---

### 4. Execute Python
**Endpoint**: `POST /api/validate/python`

**Request**:
```json
{
  "python_code": "import numpy as np\nresult = np.sum(A)",
  "test_cases": [1, 2, 3]
}
```

**Response**:
```json
{
  "status": "success",
  "output": 6,
  "output_type": "scalar"
}
```

---

### 5. Compare Results
**Endpoint**: `POST /api/compare`

**Request**:
```json
{
  "apl_result": 6,
  "python_result": 6
}
```

**Response**:
```json
{
  "match": true,
  "score": 100.0,
  "issues": [],
  "details": {
    "dtype_match": true,
    "shape_match": true,
    "values_match": true
  }
}
```

---

## Testing the System

### Test Case 1: Simple Sum
```apl
+/A
```
With input `A = [1, 2, 3]`, both APL and Python should output `6`.

### Test Case 2: Product
```apl
×/A
```
With input `A = [1, 2, 3]`, both should output `6`.

### Test Case 3: Maximum
```apl
⌈/A
```
With input `A = [1, 2, 3]`, both should output `3`.

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If in use, kill the process or change port
python -m uvicorn main:app --port 8001
```

### Frontend won't start
```bash
# Clear cache
npm cache clean --force

# Reinstall dependencies
rm -r node_modules
npm install

# Try again
npm run dev
```

### API calls fail
1. Check backend is running: http://localhost:8000/docs
2. Check frontend console for error messages (F12)
3. Check .env configuration
4. Check firewall/antivirus blocking ports

### Gemini API errors
- Verify GEMINI_API_KEY in .env is correct
- Check internet connection
- Visit https://aistudio.google.com to verify API key is valid

### Ollama not connecting
- Verify Ollama is running: http://localhost:11434
- Check model is downloaded: `ollama list`
- Pull model if needed: `ollama pull qwen2.5-coder:3b`

---

## Development

### Backend Structure
```
backend/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration & settings
├── agents/                # AI agents
│   ├── understanding_agent.py
│   ├── conversion_agent.py
│   └── ...
├── providers/             # Multi-provider support
│   ├── provider_factory.py
│   ├── gemini_provider.py
│   ├── ollama_provider.py
│   └── ...
├── execution/             # Code execution
│   ├── apl_runner.py
│   ├── python_runner.py
│   └── sandbox.py
├── comparator/            # Output comparison
│   └── engine.py
├── api/                   # REST endpoints
│   └── routes/
└── utils/                 # Utilities
```

### Frontend Structure
```
src/
├── App.tsx               # Main component
├── components/           # React components
│   ├── Dashboard.tsx
│   ├── FileUploader.tsx
│   ├── ComparatorView.tsx
│   └── Sidebar.tsx
├── services/             # API integration
│   └── migrationService.ts
└── lib/
    └── gemini.ts         # API utilities
```

---

## Performance Tips

1. **Use Public Mode (Gemini)** for faster responses
2. **Keep APL expressions simple** (single-line reductions work best)
3. **Clear browser cache** if experiencing slow loads
4. **Check backend logs** for performance insights

---

## Support

### API Documentation
- **Live Docs**: http://localhost:8000/docs (when backend is running)
- **Alternative**: http://localhost:8000/redoc

### Getting Help
1. Check backend logs (Terminal 1)
2. Check frontend console (F12 in browser)
3. Review .env configuration
4. Check network tab in browser DevTools

---

## Next Steps

After verifying the system works:
1. Test with your own APL code
2. Explore different AI providers
3. Check conversion confidence scores
4. Review generated Python code quality
5. Verify output matches between APL and Python

---

**System Ready! Open http://localhost:3000 to start.**
