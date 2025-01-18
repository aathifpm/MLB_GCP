from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from ..dependencies import get_text_to_speech_service
import io

router = APIRouter(prefix="/api", tags=["audio"])

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str
    language_code: Optional[str] = "en-US"
    speaking_rate: Optional[float] = 1.0
    pitch: Optional[float] = 0.0

@router.post("/generate-audio")
async def generate_audio(request: TextToSpeechRequest):
    """
    Generate audio from text using Google Cloud Text-to-Speech.
    Returns audio as a streaming response.
    """
    try:
        tts_service = get_text_to_speech_service()
        audio_content = await tts_service.generate_long_audio(
            text=request.text,
            voice_id=request.voice,
            language_code=request.language_code,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
        )
        
        # Create an in-memory bytes buffer
        audio_buffer = io.BytesIO(audio_content)
        audio_buffer.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=story_narration.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def list_voices(language_code: str = "en-US"):
    """
    Get a list of available voices for the specified language.
    """
    try:
        tts_service = get_text_to_speech_service()
        voices = await tts_service.get_available_voices(language_code)
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 