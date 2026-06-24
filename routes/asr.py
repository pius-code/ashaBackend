import base64
import io
import asyncio
import numpy as np
import soundfile as sf
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])


class TranscribeRequest(BaseModel):
    audio: str  # base64-encoded audio file (WAV, OGG, WebM, etc.)


@router.post("/twi_transcribe")
async def twi_transcribe(payload: TranscribeRequest, request: Request):
    asr = request.app.state.asr_pipeline

    try:
        audio_bytes = base64.b64decode(payload.audio)
        audio_buffer = io.BytesIO(audio_bytes)
        audio_array, sample_rate = sf.read(audio_buffer)

        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)
        audio_array = audio_array.astype(np.float32)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: asr({"raw": audio_array, "sampling_rate": sample_rate}),
        )
        return {"text": result["text"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
