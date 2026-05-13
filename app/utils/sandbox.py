import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SandboxResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float


class AbstractSandbox(ABC):
    @abstractmethod
    async def execute(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
    ) -> SandboxResult:
        pass

    @abstractmethod
    async def write_file(self, path: str, content: str) -> None:
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass


class DockerSandbox(AbstractSandbox):
    def __init__(
        self,
        image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        network: bool = False,
    ):
        self.image = image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network = network
        self.container_id: Optional[str] = None
        self._temp_dir: Optional[Path] = None

    async def _ensure_container(self) -> str:
        if self.container_id:
            return self.container_id

        self._temp_dir = Path(tempfile.mkdtemp(prefix="devmatrix_sandbox_"))

        network_flag = "--network=none" if not self.network else ""
        cmd = [
            "docker", "run", "-d", "--rm",
            "-m", self.memory_limit,
            "--cpus", self.cpu_limit,
        ]
        if network_flag:
            cmd.extend(network_flag.split())
        cmd.extend([
            "-v", f"{self._temp_dir}:/workspace",
            "-w", "/workspace",
            self.image,
            "sleep", "3600",
        ])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to start container: {stderr.decode()}")

        self.container_id = stdout.decode().strip()
        return self.container_id

    async def execute(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
    ) -> SandboxResult:
        container_id = await self._ensure_container()
        work_dir = working_dir or "/workspace"

        cmd = ["docker", "exec"]
        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])
        cmd.extend(["-w", work_dir, container_id] + command)

        start = asyncio.get_event_loop().time()
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=timeout,
            )
            stdout, stderr = await proc.communicate()
            duration = (asyncio.get_event_loop().time() - start) * 1000

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                duration_ms=duration,
            )
        except asyncio.TimeoutError:
            duration = (asyncio.get_event_loop().time() - start) * 1000
            return SandboxResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout}s",
                exit_code=-1,
                duration_ms=duration,
            )

    async def write_file(self, path: str, content: str) -> None:
        await self._ensure_container()
        local_path = self._temp_dir / path.lstrip("/")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content, encoding="utf-8")

    async def read_file(self, path: str) -> str:
        await self._ensure_container()
        local_path = self._temp_dir / path.lstrip("/")
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return local_path.read_text(encoding="utf-8")

    async def cleanup(self) -> None:
        if self.container_id:
            proc = await asyncio.create_subprocess_exec(
                "docker", "stop", "-t", "0", self.container_id,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
            self.container_id = None

        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None


class FirecrackerSandbox(AbstractSandbox):
    def __init__(
        self,
        kernel_image: str = "vmlinux",
        rootfs_image: str = "rootfs.ext4",
        memory_mb: int = 512,
        vcpus: int = 1,
    ):
        self.kernel_image = kernel_image
        self.rootfs_image = rootfs_image
        self.memory_mb = memory_mb
        self.vcpus = vcpus
        self._socket_path: Optional[str] = None
        self._temp_dir: Optional[Path] = None

    async def _start_microvm(self) -> str:
        self._temp_dir = Path(tempfile.mkdtemp(prefix="devmatrix_fc_"))
        socket_path = str(self._temp_dir / "firecracker.sock")
        self._socket_path = socket_path

        raise RuntimeError(
            "Firecracker sandbox requires manual setup. "
            "Install firecracker and configure kernel/rootfs images."
        )

    async def execute(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
    ) -> SandboxResult:
        await self._start_microvm()
        return SandboxResult(
            success=False,
            stdout="",
            stderr="Firecracker execution not fully implemented",
            exit_code=-1,
            duration_ms=0.0,
        )

    async def write_file(self, path: str, content: str) -> None:
        await self._start_microvm()
        raise NotImplementedError("Firecracker file operations require agent integration")

    async def read_file(self, path: str) -> str:
        await self._start_microvm()
        raise NotImplementedError("Firecracker file operations require agent integration")

    async def cleanup(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
        self._socket_path = None


def create_sandbox(
    provider: str = "docker",
    **kwargs,
) -> AbstractSandbox:
    if provider == "docker":
        return DockerSandbox(**kwargs)
    elif provider == "firecracker":
        return FirecrackerSandbox(**kwargs)
    else:
        raise ValueError(f"Unsupported sandbox provider: {provider}")
