from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from ..dependencies import get_text_to_speech_service
import io

router = APIRouter(prefix="/api", tags=["audio"])

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to convert to speech")
    voice: str = Field(..., description="The voice ID to use (e.g., 'en-US-Neural2-D')")
    language_code: Optional[str] = Field("en-US", description="The language code")
    speaking_rate: Optional[float] = Field(1.0, ge=0.25, le=4.0, description="Speaking rate (0.25 to 4.0)")
    pitch: Optional[float] = Field(0.0, ge=-20.0, le=20.0, description="Pitch adjustment (-20.0 to 20.0)")

@router.post("/generate-audio")
async def generate_audio(request: TextToSpeechRequest):
    """
    Generate audio from text using Google Cloud Text-to-Speech.
    Returns audio as a streaming response.
    """
    try:
        # Validate input text
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text provided")

        # Get TTS service
        tts_service = get_text_to_speech_service()
        if not tts_service:
            raise HTTPException(status_code=500, detail="Text-to-speech service not available")

        # Generate audio content
        try:
            audio_content = await tts_service.generate_long_audio(
                text=request.text,
                voice_id=request.voice,
                language_code=request.language_code,
                speaking_rate=request.speaking_rate,
                pitch=request.pitch,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

        # Validate audio content
        if not audio_content:
            raise HTTPException(status_code=500, detail="No audio content generated")

        # Create an in-memory bytes buffer
        audio_buffer = io.BytesIO(audio_content)
        audio_buffer.seek(0)
        
        # Return as streaming response with appropriate headers
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=story_narration.mp3",
                "Content-Length": str(len(audio_content)),
                "Cache-Control": "no-cache"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/voices")
async def list_voices(language_code: str = "en-US"):
    """
    Get a list of available voices for the specified language.
    """
    try:
        tts_service = get_text_to_speech_service()
        if not tts_service:
            raise HTTPException(status_code=500, detail="Text-to-speech service not available")

        voices = await tts_service.get_available_voices(language_code)
        if not voices:
            return {"voices": [], "message": f"No voices found for language code: {language_code}"}

        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing voices: {str(e)}") 