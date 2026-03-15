import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variable
model = None

# COCO dataset class indices
# 15: cat
# 16: dog
ALLOWED_CLASSES = [15, 16]

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading YOLOv8 model...")
    # This will download yolov8n.pt on the first run if it doesn't exist
    model = YOLO("yolov8n.pt")
    logger.info("YOLOv8 model loaded successfully.")
    yield
    # Clean up if needed
    model = None

app = FastAPI(
    title="Pet Image Verification API",
    description="An API to verify if an uploaded image contains a dog or a cat using YOLOv8.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/verify-pet-image")
async def verify_pet_image(file: UploadFile = File(...)):
    """
    Upload an image file and check if a cat or dog is detected.
    Returns {"is_valid": bool, "message": str}
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        # Read the file from the upload
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Run inference using YOLOv8
        global model
        if model is None:
            raise HTTPException(status_code=500, detail="Model is not loaded.")
            
        results = model.predict(source=image, conf=0.5, save=False)
        
        # Check detected classes
        detected_classes = []
        for result in results:
            # result.boxes.cls contains the detected class indices
            if result.boxes is not None and result.boxes.cls is not None:
                classes = result.boxes.cls.cpu().numpy().tolist()
                detected_classes.extend([int(c) for c in classes])
        
        # Determine if any allowed class (cat/dog) is found
        has_pet = any(cls in ALLOWED_CLASSES for cls in detected_classes)
        
        if has_pet:
            return JSONResponse({
                "is_valid": True,
                "message": "Valid pet photo. Cat or dog detected."
            })
        else:
            return JSONResponse({
                "is_valid": False,
                "message": "Invalid photo. No cat or dog detected."
            })

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@app.get("/health")
async def health_check():
    """Simple healthcheck endpoint."""
    return {"status": "ok"}
