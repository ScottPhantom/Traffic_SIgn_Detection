from functools import lru_cache
from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from cpv301_autodrive import __version__
from cpv301_autodrive.config import get_settings
from cpv301_autodrive.inference import ModelService


class HealthResponse(BaseModel):
    status: str
    version: str
    model_exists: bool
    model_loaded: bool


class PredictionResponse(BaseModel):
    class_id: int
    label: str
    confidence: float
    accepted: bool


@lru_cache
def get_model_service() -> ModelService:
    settings = get_settings()
    return ModelService(settings.model_path, settings.confidence_threshold)


app = FastAPI(
    title="CPV301 Traffic Sign API",
    version=__version__,
    description="Inference API for the downloaded 43-class GTSRB model.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    service = get_model_service()
    return HealthResponse(
        status="ok" if service.model_path.is_file() else "degraded",
        version=__version__,
        model_exists=service.model_path.is_file(),
        model_loaded=service.loaded,
    )


@app.post("/v1/predict", response_model=PredictionResponse)
async def predict(file: Annotated[UploadFile, File(...)]) -> PredictionResponse:
    try:
        image = Image.open(BytesIO(await file.read()))
        result = get_model_service().predict(image)
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a readable image",
        ) from exc
    return PredictionResponse(**result.__dict__)
