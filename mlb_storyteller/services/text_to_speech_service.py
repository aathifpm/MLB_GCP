from google.cloud import texttospeech
import os
from typing import Optional, List, Dict
import asyncio
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path
import json
from google.api_core import exceptions

load_dotenv()

class TextToSpeechService:
    def __init__(self):
        """Initialize the Google Cloud Text-to-Speech client."""
        try:
            # First try credentials as JSON string
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_json:
                try:
                    creds = json.loads(credentials_json)
                    if 'type' not in creds or creds['type'] != 'service_account':
                        raise Exception("Invalid credentials format - must be a service account key")
                    print(f"Using service account from JSON: {creds.get('client_email', 'unknown')}")
                    
                    # Initialize client with credentials JSON
                    self.client = texttospeech.TextToSpeechClient.from_service_account_info(creds)
                    print("Successfully initialized Google Cloud Text-to-Speech client from JSON")
                    return
                except json.JSONDecodeError:
                    print("Credentials not valid JSON, trying as file path...")
            
            # Fall back to credentials file path
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path:
                raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
                
            # Convert to absolute path if relative
            if not os.path.isabs(credentials_path):
                credentials_path = os.path.abspath(credentials_path)
                
            if not os.path.exists(credentials_path):
                raise Exception(f"Google Cloud credentials file not found at {credentials_path}")
                
            # Verify credentials file structure
            try:
                with open(credentials_path, 'r') as f:
                    creds = json.load(f)
                    if 'type' not in creds or creds['type'] != 'service_account':
                        raise Exception("Invalid credentials file format - must be a service account key")
                    print(f"Using service account: {creds.get('client_email', 'unknown')}")
            except json.JSONDecodeError:
                raise Exception("Invalid JSON in credentials file")
                
            # Update environment variable with absolute path
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            print(f"Using Google Cloud credentials from: {credentials_path}")
            
            # Initialize client with explicit project
            self.client = texttospeech.TextToSpeechClient()
            
            # Test the client by listing available voices
            try:
                self.client.list_voices()
                print("Successfully authenticated with Google Cloud Text-to-Speech API")
            except exceptions.PermissionDenied as e:
                raise Exception(
                    "Permission denied. Please ensure:\n"
                    "1. The Cloud Text-to-Speech API is enabled in your Google Cloud Console\n"
                    "2. The service account has the 'Cloud Text-to-Speech API User' role\n"
                    f"Service Account: {creds.get('client_email')}\n"
                    f"Project ID: {creds.get('project_id')}\n"
                    f"Error: {str(e)}"
                )
            except exceptions.Unauthenticated as e:
                raise Exception(
                    "Authentication failed. Please ensure:\n"
                    "1. The service account key file is valid\n"
                    "2. The GOOGLE_APPLICATION_CREDENTIALS environment variable points to the correct file\n"
                    f"Service Account: {creds.get('client_email')}\n"
                    f"Project ID: {creds.get('project_id')}\n"
                    f"Error: {str(e)}"
                )
            except Exception as e:
                raise Exception(f"Failed to access Text-to-Speech API: {str(e)}")
                
        except Exception as e:
            print(f"Error initializing Text-to-Speech client: {str(e)}")
            raise

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
        if not text.strip():
            raise ValueError("Empty text provided for audio generation")

        try:
            # Configure the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_id,
            )

            # Configure the audio encoding with enhanced quality
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=max(0.25, min(speaking_rate, 4.0)),  # Clamp to valid range
                pitch=max(-20.0, min(pitch, 20.0)),  # Clamp to valid range
                effects_profile_id=['headphone-class-device'],
                sample_rate_hertz=24000,  # Higher quality audio
            )

            # Perform the text-to-speech request
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            if not response.audio_content:
                raise ValueError("No audio content generated")

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
            
            if not voices or not voices.voices:
                return []

            return [
                {
                    'name': voice.name,
                    'gender': texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                    'language_codes': voice.language_codes,
                    'natural_sample_rate_hertz': voice.natural_sample_rate_hertz
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
        Improved to maintain sentence integrity and proper punctuation.
        
        Args:
            text: The text to split
            max_chars: Maximum characters per chunk
            
        Returns:
            list: List of text chunks
        """
        if not text:
            return []

        # Clean and normalize the text
        text = text.strip().replace('\n', ' ').replace('  ', ' ')
        
        # If text is short enough, return as is
        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = []
        current_length = 0
        sentences = text.split('. ')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add period if it was removed by split
            if not sentence.endswith('.'):
                sentence += '.'
                
            sentence_length = len(sentence) + 1  # +1 for space
            
            if current_length + sentence_length > max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk).strip())
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    # If a single sentence is too long, split it at word boundaries
                    words = sentence.split()
                    temp_chunk = []
                    temp_length = 0
                    
                    for word in words:
                        word_length = len(word) + 1
                        if temp_length + word_length > max_chars:
                            if temp_chunk:
                                chunks.append(' '.join(temp_chunk) + '.')
                            temp_chunk = [word]
                            temp_length = word_length
                        else:
                            temp_chunk.append(word)
                            temp_length += word_length
                    
                    if temp_chunk:
                        chunks.append(' '.join(temp_chunk) + '.')
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(' '.join(current_chunk).strip())

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
        if not text:
            raise ValueError("No text provided for audio generation")

        try:
            chunks = self.chunk_text(text)
            if not chunks:
                raise ValueError("Text chunking resulted in no valid chunks")

            audio_chunks = []
            total_chunks = len(chunks)

            print(f"Processing {total_chunks} text chunks...")

            for i, chunk in enumerate(chunks, 1):
                print(f"Generating audio for chunk {i}/{total_chunks}")
                chunk_audio = await self.generate_audio(
                    chunk,
                    voice_id,
                    language_code,
                    speaking_rate,
                    pitch,
                )
                if chunk_audio:
                    audio_chunks.append(chunk_audio)

            if not audio_chunks:
                raise ValueError("No audio chunks were generated")

            # Concatenate the audio chunks
            return b''.join(audio_chunks)
            
        except Exception as e:
            print(f"Error generating long audio: {str(e)}")
            raise 