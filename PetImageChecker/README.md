# Pet Image Checker + Symptom Orchestrator

This backend uses **FastAPI** for two AI services:
- YOLOv8-based pet image verification
- Agentic symptom orchestration with PostgreSQL + Neo4j integration
- OpenAI (ChatGPT API) response enhancement with safe fallback to rule-engine output

## Getting Started

1. Simply double click on `run.bat` or run it from a PowerShell terminal:
```bash
.\run.bat
```
2. The script will automatically create the virtual environment, install dependencies from `requirements.txt`, and start the fastAPI server on `http://localhost:8000`.

## Endpoints

### `GET /health`
Returns system status.

### `POST /verify-pet-image`
Takes an image upload and responds with a JSON verification result.

Current scope:
- Verifies pet photos using the YOLO-based image classifier.
- This endpoint does not yet perform vaccination-card OCR or document authenticity checks.

If you extend this service for vaccination cards, add an OCR step first, then validate extracted fields such as pet name, vaccine type, date, and vet name before approving the upload.

### `POST /orchestrate/symptom`
Runs the AI flow for symptom analysis:
- Input Handler
- Prompt Processor
- Task Planner
- Agent Dispatcher
- Service Layer (PostgreSQL + Neo4j)
- Results Aggregator

Response now includes structured fields for agentic chat UX:
- `diagnosis_suggestion`
- `care_tips` (max 6)
- `emergency_guidance`
- `urgency` (`low | medium | high`)
- `follow_up_questions` (max 3)

Request body example:
```json
{
    "message": "my dog has fever and vomiting",
    "user_email": "user@example.com",
    "session_id": "session-123"
}
```

### `GET /admin/orchestrator/status`
Returns service status and DB connector readiness.


## Optional Environment Variables

- `POSTGRES_DSN`
    - Example: `dbname=pethub user=postgres password=your_password host=localhost port=5432`
- `NEO4J_URI`
    - Example: `bolt://localhost:7687`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `OPENROUTER_API_KEY`
    - Preferred when using OpenRouter models
- `OPENAI_API_KEY`
    - Optional fallback key (used if `OPENROUTER_API_KEY` is not set)
- `OPENAI_BASE_URL`
    - Optional custom endpoint URL, defaulted automatically to `https://openrouter.ai/api/v1` when `OPENROUTER_API_KEY` is set
- `OPENAI_MODEL`
    - Optional, default: `gpt-4.1-mini`

If neither `OPENROUTER_API_KEY` nor `OPENAI_API_KEY` is set (or the API is unreachable), the symptom endpoint still works using the built-in rule engine.

**Example Request from React Native (Expo):**
```javascript
let localUri = image.uri;
let filename = localUri.split('/').pop();
let match = /\.(\w+)$/.exec(filename);
let type = match ? `image/${match[1]}` : `image`;

let formData = new FormData();
formData.append('file', { uri: localUri, name: filename, type });

const verifyResponse = await fetch('http://localhost:8000/verify-pet-image', {
    method: 'POST',
    body: formData,
    headers: { 'content-type': 'multipart/form-data' },
});

const verification = await verifyResponse.json();
if (!verification.is_valid) {
    alert("This photo does not look like a dog or cat. Please try again.");
    return;
}
```
