import io
import asyncio
import numpy as np
import soundfile as sf
from fastapi import APIRouter, Request, HTTPException
import librosa


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])
Target_SampR = 16000


@router.post("/twi_transcribe")
async def twi_transcribe(request: Request):
    asr = request.app.state.asr_pipeline
    audio_bytes = await request.body()

    try:
        audio_buffer = io.BytesIO(audio_bytes)
        audio_array, sample_rate = sf.read(audio_buffer)

        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)
        audio_array = audio_array.astype(np.float32)

        if sample_rate != Target_SampR:
            audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=Target_SampR) # noqa
        sample_rate = Target_SampR

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: asr({"raw": audio_array, "sampling_rate": sample_rate}),
        )
        return {"text": result["text"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
