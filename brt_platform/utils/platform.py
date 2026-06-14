import os
import sys
import shutil
import multiprocessing
import logging

logger = logging.getLogger(__name__)


class PlatformDetector:
    def __init__(self):
        self.system = sys.platform
        self.machine = os.uname().machine.lower() if hasattr(os, 'uname') else 'unknown'
        self._is_wsl = self._detect_wsl()
        self._is_apple_silicon = self._detect_apple_silicon()
        self.gpu_type = self._detect_gpu()
        self.container_runtime = self._detect_container_runtime()

    def _detect_wsl(self) -> bool:
        try:
            return 'microsoft' in os.uname().release.lower()
        except AttributeError:
            return False

    def _detect_apple_silicon(self) -> bool:
        return self.system == "darwin" and self.machine in ("arm64", "aarch64")

    def _detect_gpu(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def _detect_container_runtime(self) -> str:
        if shutil.which("podman"):
            return "podman"
        if shutil.which("docker"):
            return "docker"
        return "none"

    def get_info(self) -> dict:
        return {
            "system": self.system,
            "machine": self.machine,
            "is_wsl": self._is_wsl,
            "is_apple_silicon": self._is_apple_silicon,
            "gpu_type": self.gpu_type,
            "container_runtime": self.container_runtime,
        }

    def get_optimal_config(self) -> dict:
        cpu_count = multiprocessing.cpu_count()
        config = {
            "embed_batch_size": 32,
            "max_workers": min(cpu_count, 4),
            "torch_threads": min(cpu_count, 4),
        }
        if self.gpu_type == "cuda":
            config["embed_batch_size"] = 256
        elif self.gpu_type == "mps":
            config["embed_batch_size"] = 64
        if self._is_apple_silicon or self._is_wsl:
            config["embed_batch_size"] = min(config["embed_batch_size"], 16)
            config["max_workers"] = 2
        return config

    def apply_optimal_config(self) -> dict:
        config = self.get_optimal_config()
        os.environ["OMP_NUM_THREADS"] = str(config["torch_threads"])
        try:
            import torch
            torch.set_num_threads(config["torch_threads"])
        except ImportError:
            pass
        info = self.get_info()
        logger.info(
            f"Platform: {info['system']} {info['machine']} | "
            f"GPU: {info['gpu_type']} | WSL: {info['is_wsl']} | "
            f"Runtime: {info['container_runtime']}"
        )
        return config
