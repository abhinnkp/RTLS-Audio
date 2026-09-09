import abc
import subprocess
import logging

class AbstractAudioMixer(abc.ABC):
    @abc.abstractmethod
    def set_pga_gain(self, gain_db: int) -> bool:
        pass

    @abc.abstractmethod
    def get_pga_gain(self) -> int:
        pass

class ALSAMixer(AbstractAudioMixer):
    def __init__(self, logger: logging.Logger, device: str = "default", control_name: str = "PGA"):
        self.logger = logger
        self.device = device
        # Note: The exact ALSA control name for ReSpeaker might vary (e.g. 'ADC PGA Gain' or 'PGA').
        # It should be established/mapped dynamically later if needed, but defaults to 'PGA'.
        self.control_name = control_name

    def set_pga_gain(self, gain_db: int) -> bool:
        # Implementation invokes amixer directly for the targeted device.
        # amixer -D hw:1 cset name='PGA' 25
        try:
            cmd = ["amixer", "-D", self.device, "sset", self.control_name, f"{gain_db}dB"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"ALSA Mixer: Successfully set PGA gain to {gain_db}dB on {self.device}.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ALSA Mixer: Failed to set PGA gain. Command returned {e.returncode}. Output: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"ALSA Mixer: Unexpected error applying PGA gain: {e}")
            return False

    def get_pga_gain(self) -> int:
        # Simple extraction. Real extraction involves regexing amixer outputs.
        # Fallback to -1 if unknown to distinguish from 0dB
        return -1

class MockAudioMixer(AbstractAudioMixer):
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.current_gain = -1

    def set_pga_gain(self, gain_db: int) -> bool:
        if gain_db == -999: # Magic number to test failure
            self.logger.error("Mock Mixer: Simulated failure setting PGA gain.")
            return False
        self.current_gain = gain_db
        self.logger.info(f"Mock Mixer: Successfully set simulated PGA gain to {gain_db}dB.")
        return True

    def get_pga_gain(self) -> int:
        return self.current_gain
