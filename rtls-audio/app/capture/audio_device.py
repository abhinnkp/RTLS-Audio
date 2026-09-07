import abc
import wave
import struct
from typing import List, Dict, Optional, Tuple

class AudioCapabilities:
    def __init__(self, channels: List[int], sample_rates: List[int]):
        self.channels = channels
        self.sample_rates = sample_rates

class AudioDeviceInfo:
    def __init__(self, name: str, card_index: int, capabilities: Optional[AudioCapabilities] = None):
        self.name = name
        self.card_index = card_index
        self.capabilities = capabilities

class AbstractAudioDevice(abc.ABC):
    @abc.abstractmethod
    def list_devices(self) -> List[AudioDeviceInfo]:
        pass

    @abc.abstractmethod
    def capture_test_audio(self, duration_sec: int, filepath: str, sample_rate: int = 48000, channels: int = 2, device: str = "default") -> bool:
        pass


class ALSAAudioDevice(AbstractAudioDevice):
    def __init__(self):
        try:
            import alsaaudio
            self.alsaaudio = alsaaudio
        except ImportError:
            self.alsaaudio = None

    def list_devices(self) -> List[AudioDeviceInfo]:
        devices = []
        if not self.alsaaudio:
            return devices

        try:
            # We can list PCMs
            pcms = self.alsaaudio.pcms(self.alsaaudio.PCM_CAPTURE)
            for idx, pcm in enumerate(pcms):
                # Basic info, getting full capabilities from ALSA can be complex,
                # we'll represent it simply for now or leave capabilities None
                devices.append(AudioDeviceInfo(name=pcm, card_index=idx))
        except Exception:
            pass
        return devices

    def capture_test_audio(self, duration_sec: int, filepath: str, sample_rate: int = 48000, channels: int = 2, device: str = "default") -> bool:
        if not self.alsaaudio:
            return False

        try:
            inp = self.alsaaudio.PCM(
                self.alsaaudio.PCM_CAPTURE,
                self.alsaaudio.PCM_NORMAL,
                channels=channels,
                rate=sample_rate,
                format=self.alsaaudio.PCM_FORMAT_S16_LE,
                periodsize=160,
                device=device
            )

            with wave.open(filepath, 'wb') as w:
                w.setnchannels(channels)
                w.setsampwidth(2) # 16 bit
                w.setframerate(sample_rate)

                frames_to_read = int(sample_rate * duration_sec / 160)
                frames_read = 0
                for _ in range(frames_to_read):
                    length, data = inp.read()
                    if length > 0:
                        w.writeframes(data)
                        frames_read += length
                    else:
                        # Capture failed or zero frames read
                        import logging
                        logging.getLogger("rtls-audio").error("ALSA capture returned zero frames.")
                        return False

                if frames_read == 0:
                    return False

            return True
        except Exception as e:
            import logging
            logging.getLogger("rtls-audio").error(f"ALSA capture failed: {e}")
            return False


class MockAudioDevice(AbstractAudioDevice):
    def list_devices(self) -> List[AudioDeviceInfo]:
        return [
            AudioDeviceInfo("Mock Generic Capture Device 0", 0, AudioCapabilities([1, 2], [16000, 48000])),
            AudioDeviceInfo("Mock Generic Capture Device 1", 1, AudioCapabilities([1, 2], [48000]))
        ]

    def capture_test_audio(self, duration_sec: int, filepath: str, sample_rate: int = 48000, channels: int = 2, device: str = "default") -> bool:
        try:
            if duration_sec <= 0 or channels <= 0 or sample_rate <= 0:
                return False

            with wave.open(filepath, 'wb') as w:
                w.setnchannels(channels)
                w.setsampwidth(2)
                w.setframerate(sample_rate)

                # Generate a simple dummy tone or silence
                total_frames = sample_rate * duration_sec
                # Just writing zeros for silence to mock audio
                data = struct.pack('<h', 0) * channels * total_frames
                w.writeframes(data)
            return True
        except Exception as e:
            import logging
            logging.getLogger("rtls-audio").error(f"Mock capture failed: {e}")
            return False
