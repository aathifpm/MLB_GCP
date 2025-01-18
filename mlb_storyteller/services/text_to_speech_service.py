from google.cloud import texttospeech
import os
from typing import Optional, List, Dict
import asyncio
from functools import lru_cache

class TextToSpeechService:
    def __init__(self):
        """Initialize the Google Cloud Text-to-Speech client."""
        self.client = texttospeech.TextToSpeechClient()

    async def generate_audio(
        self,
        text: str,
        voice_id: str,
        language_code: str = "en-US",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ) -> bytes:
        """
        Generate audio from text using Google Cloud Text-to-Speech.
        
        Args:
            text: The text to convert to speech
            voice_id: The ID of the voice to use (e.g., 'en-US-Neural2-A')
            language_code: The language code (default: 'en-US')
            speaking_rate: The speaking rate (0.25 to 4.0, default: 1.0)
            pitch: The pitch adjustment (-20.0 to 20.0, default: 0.0)
            
        Returns:
            bytes: The audio data in MP3 format
        """
        try:
            # Configure the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_id,
            )

            # Configure the audio encoding
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch,
                effects_profile_id=['headphone-class-device'],
            )

            # Perform the text-to-speech request
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            return response.audio_content
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            raise

    async def get_available_voices(self, language_code: str = "en-US") -> List[Dict]:
        """
        Get a list of available voices for the specified language.
        
        Args:
            language_code: The language code to filter voices by
            
        Returns:
            list: List of available voice names and properties
        """
        try:
            # Run the API call in a thread pool
            voices = await asyncio.to_thread(
                self.client.list_voices,
                language_code=language_code
            )
            
            return [
                {
                    'name': voice.name,
                    'gender': texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                    'language_codes': voice.language_codes,
                }
                for voice in voices.voices
            ]
        except Exception as e:
            print(f"Error listing voices: {str(e)}")
            raise

    @staticmethod
    def chunk_text(text: str, max_chars: int = 5000) -> List[str]:
        """
        Split text into chunks that are within Google Cloud Text-to-Speech limits.
        
        Args:
            text: The text to split
            max_chars: Maximum characters per chunk
            
        Returns:
            list: List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for the space
            if current_length + word_length > max_chars:
                # Find the nearest sentence end in the current chunk
                chunk_text = ' '.join(current_chunk)
                last_period = chunk_text.rfind('.')
                if last_period != -1 and last_period > len(chunk_text) * 0.5:
                    # Split at the last period if it's in the latter half
                    first_part = chunk_text[:last_period + 1]
                    remainder = chunk_text[last_period + 1:].strip()
                    chunks.append(first_part)
                    current_chunk = remainder.split() + [word]
                else:
                    chunks.append(chunk_text)
                    current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    async def generate_long_audio(
        self,
        text: str,
        voice_id: str,
        language_code: str = "en-US",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ) -> bytes:
        """
        Generate audio for long text by splitting it into chunks and concatenating the results.
        
        Args:
            text: The text to convert to speech
            voice_id: The ID of the voice to use
            language_code: The language code
            speaking_rate: The speaking rate
            pitch: The pitch adjustment
            
        Returns:
            bytes: The concatenated audio data in MP3 format
        """
        try:
            chunks = self.chunk_text(text)
            audio_chunks = []

            for chunk in chunks:
                chunk_audio = await self.generate_audio(
                    chunk,
                    voice_id,
                    language_code,
                    speaking_rate,
                    pitch,
                )
                audio_chunks.append(chunk_audio)

            # Concatenate the audio chunks
            return b''.join(audio_chunks)
            
        except Exception as e:
            print(f"Error generating long audio: {str(e)}")
            raise 