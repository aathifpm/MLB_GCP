from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from ..dependencies import get_text_to_speech_service
import io
from google.api_core import exceptions

router = APIRouter(
    prefix="/audio",
    tags=["audio"]
)

class Voice(BaseModel):
    name: str
    gender: str
    language_codes: List[str]
    natural_sample_rate_hertz: int

class VoiceListResponse(BaseModel):
    voices: List[Voice]
    message: Optional[str] = None

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
        try:
            tts_service = get_text_to_speech_service()
            if not tts_service:
                raise HTTPException(status_code=500, detail="Text-to-speech service not available")
        except Exception as e:
            error_msg = str(e)
            if "GOOGLE_APPLICATION_CREDENTIALS" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Google Cloud credentials not properly configured. Please check GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )
            elif "Permission denied" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {error_msg}"
                )
            elif "Authentication failed" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail=f"Authentication failed: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize Text-to-Speech service: {error_msg}"
                )

        # Generate audio content
        try:
            audio_content = await tts_service.generate_long_audio(
                text=request.text,
                voice_id=request.voice,
                language_code=request.language_code,
                speaking_rate=request.speaking_rate,
                pitch=request.pitch,
            )
        except exceptions.PermissionDenied as e:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {str(e)}"
            )
        except exceptions.Unauthenticated as e:
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio generation failed: {str(e)}"
            )

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

@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(language_code: str = "en-US"):
    """
    Get a list of available voices for the specified language.
    """
    try:
        tts_service = get_text_to_speech_service()
        if not tts_service:
            return VoiceListResponse(
                voices=[],
                message="Text-to-speech service not available"
            )

        voices = await tts_service.get_available_voices(language_code)
        if not voices:
            return VoiceListResponse(
                voices=[],
                message=f"No voices found for language code: {language_code}"
            )

        # Convert the voice objects to Pydantic models
        voice_list = [
            Voice(
                name=voice["name"],
                gender=voice["gender"],
                language_codes=voice["language_codes"],
                natural_sample_rate_hertz=voice["natural_sample_rate_hertz"]
            )
            for voice in voices
        ]

        return VoiceListResponse(voices=voice_list)
    except Exception as e:
        # Log the error but return an empty list instead of throwing an error
        print(f"Error listing voices: {str(e)}")
        return VoiceListResponse(
            voices=[],
            message="Voice service temporarily unavailable"
        ) 