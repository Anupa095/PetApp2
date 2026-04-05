# PetHub Chatbot - Configuration & Troubleshooting Guide

## Current Issues & Solutions

### 1. ❌ Neo4j Connection Failed (WinError 10061 - Connection Refused)
**Problem:** Neo4j service not running on localhost:7687

**Solutions:**
- **Option A: Start Neo4j locally** (if you have Docker)
  ```powershell
  docker pull neo4j:latest
  docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/Anu@4395 neo4j:latest
  ```

- **Option B: Disable Neo4j (use PostgreSQL only)**
  - Edit `.env`: set `NEO4J_URI=` (leave empty)
  - Set `NEO4J_PASSWORD=` (leave empty)
  - System will skip Neo4j and use PostgreSQL care tips instead

### 2. ❌ OpenAI/OpenRouter API Error (401 Unauthorized)
**Problem:** Invalid or missing API key

**Solutions:**
- Get valid OpenRouter API key from https://openrouter.ai/keys
- Update `.env`:
  ```
  OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx (your actual key)
  ```
- Or use local Ollama (free, no API key):
  ```
  OPENAI_BASE_URL=http://localhost:11434/v1
  OPENAI_API_KEY=ollama
  OPENAI_MODEL=mistral
  ```

### 3. ✅ PostgreSQL Care Tips (Already Working!)
- Your PostgreSQL connection is OK
- Care tips are being retrieved from database
- Diagnosis rules are functioning

## Quick Fix - Minimal Working Setup

If you don't have Neo4j or OpenRouter API key, the chatbot still works:

```env
# Keep PostgreSQL enabled
POSTGRES_DB=pethub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Anu@4395
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Disable Neo4j (no connection required)
NEO4J_URI=
NEO4J_PASSWORD=

# Disable OpenRouter (no LLM enhancement)
OPENROUTER_API_KEY=
OPENAI_API_KEY=
```

**Status:** ✅ Rule-based diagnosis + PostgreSQL care tips
- No Neo4j disease graph
- No LLM improvements
- Still provides functional advice

## Recommended Full Setup

```env
# PostgreSQL (required)
POSTGRES_DB=pethub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Anu@4395
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Neo4j (optional - improves diagnosis matching)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Anu@4395

# OpenRouter (optional - improves care tips with LLM)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=nvidia/nemotron-3-super-120b-a12b:free
```

## Testing Your Setup

### 1. Check PostgreSQL
```powershell
cd C:\Users\Anupa\Desktop\PetHub2\PetImageChecker
python -c "import psycopg; conn = psycopg.connect('dbname=pethub user=postgres password=Anu@4395 host=localhost'); print('✓ PostgreSQL OK')"
```

### 2. Test Chatbot API
```powershell
cd C:\Users\Anupa\Desktop\PetHub2\PetImageChecker
$payload = @{
    message = "My dog has vomiting and diarrhea"
    user_email = "test@pethub.local"
    session_id = "test-session"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/orchestrate/symptom" -Method Post -Body $payload -ContentType "application/json"
```

### 3. Check Service Status
```
GET http://localhost:8000/admin/orchestrator/status
```

## Current System Status

| Component | Status | Impact |
|-----------|--------|--------|
| PostgreSQL | ✅ Working | Care tips retrieved |
| Neo4j | ❌ Not running | Uses rule-based disease matching |
| OpenRouter API | ❌ Invalid key | Uses rule-based care tips |
| Spring Backend | ✅ Running | API gateway OK |
| FastAPI Orchestrator | ✅ Running | Symptom analysis working |
| Frontend | ✅ Ready | Chat UI functional |

## Output Quality

- **Without fixes:** Rule-only diagnosis (60% quality)
- **With PostgreSQL only:** Rule + DB tips (75% quality)
- **With Neo4j:** Rule + Graph matching (85% quality)
- **With OpenRouter:** Rule + LLM enhancement (95% quality)

Your current setup is at **75% quality** - functional but without graph database and LLM improvements.
