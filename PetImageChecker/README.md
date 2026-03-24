# Pet Image Checker + Symptom Orchestrator

This backend uses **FastAPI** for two AI services:
- YOLOv8-based pet image verification
- Agentic symptom orchestration with PostgreSQL + Neo4j integration

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

### `POST /orchestrate/symptom`
Runs the AI flow for symptom analysis:
- Input Handler
- Prompt Processor
- Task Planner
- Agent Dispatcher
- Service Layer (PostgreSQL + Neo4j)
- Results Aggregator

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
