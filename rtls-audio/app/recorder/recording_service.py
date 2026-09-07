import os
import time
import wave
import logging
import datetime
from dataclasses import dataclass
from typing import Optional

from app.capture.audio_device import AbstractAudioDevice, AbstractAudioStream

@dataclass
class RecordingResult:
    success: bool
    output_path: Optional[str]
    duration_requested: float
    duration_captured: float
    frames_captured: int
    sample_rate: int
    channels: int
    sample_width: int
    error_message: Optional[str]

class RecordingService:
    def __init__(self, audio_device: AbstractAudioDevice, logger: logging.Logger):
        self.audio_device = audio_device
        self.logger = logger

    def _generate_filename(self) -> str:
        import uuid
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
        unique_id = uuid.uuid4().hex[:6]
        return f"{timestamp}_{unique_id}.wav"

    def record(self, output_dir: str, duration_sec: int, sample_rate: int = 48000,
               channels: int = 2, sample_width: int = 2, device_name: str = "default") -> RecordingResult:

        if sample_width != 2:
            self.logger.error(f"Unsupported sample width {sample_width}. Only 16-bit PCM (sample_width=2) is supported.")
            return RecordingResult(
                success=False, output_path=None, duration_requested=duration_sec,
                duration_captured=0.0, frames_captured=0, sample_rate=sample_rate,
                channels=channels, sample_width=sample_width, error_message=f"Unsupported sample width: {sample_width}"
            )

        result = RecordingResult(
            success=False,
            output_path=None,
            duration_requested=duration_sec,
            duration_captured=0.0,
            frames_captured=0,
            sample_rate=sample_rate,
            channels=channels,
            sample_width=sample_width,
            error_message=None
        )

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            result.error_message = f"Failed to create output directory {output_dir}: {e}"
            self.logger.error(result.error_message)
            return result

        filename = self._generate_filename()
        filepath = os.path.join(output_dir, filename)
        result.output_path = filepath

        stream: Optional[AbstractAudioStream] = None
        w: Optional[wave.Wave_write] = None

        try:
            stream = self.audio_device.open_stream(
                sample_rate=sample_rate,
                channels=channels,
                device=device_name
            )
        except Exception as e:
            result.error_message = f"Failed to open audio device '{device_name}': {e}"
            self.logger.error(result.error_message)
            return result

        try:
            w = wave.open(filepath, 'wb')
            w.setnchannels(channels)
            w.setsampwidth(sample_width)
            w.setframerate(sample_rate)

            expected_frames = sample_rate * duration_sec
            frames_read_total = 0

            # Simple streaming loop without massive RAM bloat
            while frames_read_total < expected_frames:
                length, data = stream.read()

                if length <= 0:
                    result.error_message = "Capture failed or zero frames read during stream."
                    self.logger.error(result.error_message)
                    break

                frames_to_write = min(length, expected_frames - frames_read_total)

                # Truncate data if we over-read slightly at the end of the duration
                if frames_to_write < length:
                    bytes_per_frame = channels * sample_width
                    data = data[:frames_to_write * bytes_per_frame]

                w.writeframes(data)
                frames_read_total += frames_to_write

            result.frames_captured = frames_read_total
            result.duration_captured = frames_read_total / sample_rate

            if frames_read_total > 0 and not result.error_message:
                result.success = True
            elif frames_read_total > 0 and frames_read_total < expected_frames:
                # We got a partial capture but failed midway. Do not mark as complete success.
                result.success = False
                result.error_message = result.error_message or "Partial capture only"
            else:
                result.success = False

        except Exception as e:
            result.error_message = f"Error during audio capture/write: {e}"
            self.logger.error(result.error_message)
            result.success = False
            result.frames_captured = frames_read_total
            result.duration_captured = frames_read_total / sample_rate

        finally:
            if w:
                try:
                    w.close()
                except Exception:
                    pass
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass

            # Cleanup broken files if 0 frames recorded
            if result.frames_captured == 0 and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

        return result
