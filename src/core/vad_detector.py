"""
Silero VAD (Voice Activity Detection) module.
"""
import logging
import torch
import numpy as np
from pathlib import Path
from typing import Union, List, Tuple, Optional
from dataclasses import dataclass

from src.config import (
    VAD_THRESHOLD,
    VAD_MIN_SPEECH_DURATION,
    VAD_MINSilence_duration,
    VAD_MAX_PAUSE_DURATION
)

logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    """Speech segment detected by VAD."""
    start: float  # seconds
    end: float  # seconds
    speech_prob: float


class VADDetector:
    """Silero VAD detector for speech activity detection."""

    def __init__(
        self,
        threshold: float = VAD_THRESHOLD,
        min_speech_duration: float = VAD_MIN_SPEECH_DURATION,
        min_silence_duration: float = VAD_MINSilence_duration
    ):
        self.threshold = threshold
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration
        self.model = None
        self._vad_get_speech_timestamps = None  # Silero function (renamed to avoid conflict)
        self._read_audio = None

    def load_model(self):
        """Load Silero VAD model."""
        if self.model is None:
            logger.info("Loading Silero VAD model...")
            torch.set_num_threads(1)
            self.model, utils = torch.load(
                "silero_vad.jit",
                map_location=torch.device("cpu")
            )
            self.model = torch.jit.load("silero_vad.jit", map_location=torch.device("cpu"))
            (_, self._vad_get_speech_timestamps, _, self._read_audio, _, _) = utils
            logger.info("Silero VAD model loaded successfully")

    def get_speech_timestamps(self, audio_path: Union[str, Path]) -> List[SpeechSegment]:
        """
        Get speech timestamps from audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            List of SpeechSegment objects
        """
        if self.model is None:
            self.load_model()

        audio_path = Path(audio_path)

        # Read audio
        audio, sr = self._read_audio(str(audio_path), sampling_rate=16000)

        # Get speech timestamps using Silero function
        speech_timestamps = self._vad_get_speech_timestamps(
            audio,
            threshold=self.threshold,
            min_speech_duration=self.min_speech_duration,
            min_silence_duration=self.min_silence_duration
        )

        segments = []
        for seg in speech_timestamps:
            segments.append(SpeechSegment(
                start=seg["start"] / 16000,  # Convert to seconds
                end=seg["end"] / 16000,
                speech_prob=1.0  # Silero doesn't provide probability
            ))

        logger.info(f"VAD detected {len(segments)} speech segments")
        return segments

    def get_speech_timestamps_from_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000) -> List[SpeechSegment]:
        """
        Get speech timestamps from audio numpy array.

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio

        Returns:
            List of SpeechSegment objects
        """
        if self.model is None:
            self.load_model()

        # Get speech timestamps using Silero function
        speech_timestamps = self._vad_get_speech_timestamps(
            audio_data,
            threshold=self.threshold,
            min_speech_duration=self.min_speech_duration,
            min_silence_duration=self.min_silence_duration
        )

        segments = []
        for seg in speech_timestamps:
            segments.append(SpeechSegment(
                start=seg["start"] / sample_rate,
                end=seg["end"] / sample_rate,
                speech_prob=1.0
            ))

        return segments

    def find_long_pauses(self, speech_timestamps: List[SpeechSegment], max_pause_duration: float = VAD_MAX_PAUSE_DURATION) -> List[Tuple[float, float]]:
        """
        Find pauses longer than threshold between speech segments.

        Args:
            speech_timestamps: List of speech segments
            max_pause_duration: Maximum allowed pause duration

        Returns:
            List of (pause_start, pause_end) tuples
        """
        if len(speech_timestamps) < 2:
            return []

        pauses = []
        for i in range(len(speech_timestamps) - 1):
            current_end = speech_timestamps[i].end
            next_start = speech_timestamps[i + 1].start
            pause_duration = next_start - current_end

            if pause_duration > max_pause_duration:
                pauses.append((current_end, next_start))

        return pauses
