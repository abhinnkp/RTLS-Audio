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

class AbstractAudioStream(abc.ABC):
    @abc.abstractmethod
    def read(self) -> Tuple[int, bytes]:
        """Returns (number_of_frames_read, frame_data_bytes)"""
        pass

    @abc.abstractmethod
    def close(self):
        pass

class AbstractAudioDevice(abc.ABC):
    @abc.abstractmethod
    def list_devices(self) -> List[AudioDeviceInfo]:
        pass

    @abc.abstractmethod
    def open_stream(self, sample_rate: int, channels: int, device: str = "default") -> AbstractAudioStream:
        pass

    @abc.abstractmethod
    def capture_test_audio(self, duration_sec: int, filepath: str, sample_rate: int = 48000, channels: int = 2, device: str = "default") -> bool:
        pass


class ALSAAudioStream(AbstractAudioStream):
    def __init__(self, pcm):
        self.pcm = pcm

    def read(self) -> Tuple[int, bytes]:
        if not self.pcm:
            return 0, b""
        try:
            return self.pcm.read()
        except Exception:
            return 0, b""

    def close(self):
        if self.pcm:
            try:
                self.pcm.close()
            except Exception:
                pass
            self.pcm = None


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

    def open_stream(self, sample_rate: int, channels: int, device: str = "default") -> AbstractAudioStream:
        if not self.alsaaudio:
            raise RuntimeError("pyalsaaudio is not available")

        inp = self.alsaaudio.PCM(
            self.alsaaudio.PCM_CAPTURE,
            self.alsaaudio.PCM_NORMAL,
            channels=channels,
            rate=sample_rate,
            format=self.alsaaudio.PCM_FORMAT_S16_LE,
            periodsize=160,
            device=device
        )
        return ALSAAudioStream(inp)

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


class MockAudioStream(AbstractAudioStream):
    def __init__(self, sample_rate: int, channels: int, device: str):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.periodsize = 160
        self.is_closed = False
        self.reads = 0

    def read(self) -> Tuple[int, bytes]:
        if self.is_closed:
            return 0, b""

        if self.device == "mock_read_error" and self.reads > 5:
            return 0, b"" # Simulate read failure midway

        if self.device == "mock_zero_frame":
            return 0, b""

        self.reads += 1
        data = struct.pack('<h', 0) * self.channels * self.periodsize
        return self.periodsize, data

    def close(self):
        self.is_closed = True


class MockAudioDevice(AbstractAudioDevice):
    def list_devices(self) -> List[AudioDeviceInfo]:
        return [
            AudioDeviceInfo("Mock Generic Capture Device 0", 0, AudioCapabilities([1, 2], [16000, 48000])),
            AudioDeviceInfo("Mock Generic Capture Device 1", 1, AudioCapabilities([1, 2], [48000]))
        ]

    def open_stream(self, sample_rate: int, channels: int, device: str = "default") -> AbstractAudioStream:
        if device == "mock_open_error":
            raise RuntimeError("Mock simulated device open failure")
        return MockAudioStream(sample_rate, channels, device)

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
