import os
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlatformInfo:
    os_name: str
    kernel_version: str
    cpu_architecture: str
    cpu_model: str
    cpu_cores: int
    is_raspberry_pi: bool
    pi_model: Optional[str]
    pi_revision: Optional[str]

class PlatformDetector:
    def __init__(self):
        pass

    def detect(self) -> PlatformInfo:
        os_name = self._get_os_name()
        kernel_version = platform.release()
        cpu_arch = platform.machine()
        cpu_model, cpu_cores = self._get_cpu_info()
        pi_model, pi_rev = self._get_pi_info()

        is_pi = pi_model is not None

        return PlatformInfo(
            os_name=os_name,
            kernel_version=kernel_version,
            cpu_architecture=cpu_arch,
            cpu_model=cpu_model,
            cpu_cores=cpu_cores,
            is_raspberry_pi=is_pi,
            pi_model=pi_model,
            pi_revision=pi_rev
        )

    def _get_os_name(self) -> str:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=")[1].strip().strip('"')
        except FileNotFoundError:
            pass
        return platform.system()

    def _get_cpu_info(self) -> tuple[str, int]:
        model = "Unknown"
        cores = os.cpu_count() or 1

        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name") or line.startswith("Model"):
                        parts = line.split(":")
                        if len(parts) > 1:
                            model = parts[1].strip()
                            break
        except FileNotFoundError:
            pass

        return model, cores

    def _get_pi_info(self) -> tuple[Optional[str], Optional[str]]:
        pi_model = None
        pi_revision = None

        try:
            # Check device tree for Pi model
            with open("/proc/device-tree/model", "r") as f:
                model_str = f.read().strip().strip('\x00')
                if "Raspberry Pi" in model_str:
                    pi_model = model_str
        except FileNotFoundError:
            pass

        try:
            # Check cpuinfo for revision
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("Revision"):
                        parts = line.split(":")
                        if len(parts) > 1:
                            pi_revision = parts[1].strip()
                            break
        except FileNotFoundError:
            pass

        return pi_model, pi_revision

class MockPlatformDetector(PlatformDetector):
    def __init__(self, pi_model="Raspberry Pi Zero 2 W Rev 1.0", cpu_arch="aarch64", cores=4):
        self._pi_model = pi_model
        self._cpu_arch = cpu_arch
        self._cores = cores

    def detect(self) -> PlatformInfo:
        return PlatformInfo(
            os_name="Debian GNU/Linux 12 (bookworm)",
            kernel_version="6.6.20-v8+",
            cpu_architecture=self._cpu_arch,
            cpu_model="Cortex-A53",
            cpu_cores=self._cores,
            is_raspberry_pi=True,
            pi_model=self._pi_model,
            pi_revision="902120"
        )
