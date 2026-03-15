# Pet Image Checker

This backend uses **FastAPI** and **YOLOv8** to verify that an uploaded image contains a cat or a dog.

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
