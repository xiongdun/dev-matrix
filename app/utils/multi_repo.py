import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RepoConfig:
    name: str
    url: str
    branch: str = "main"
    local_path: Optional[str] = None
    auth_token: Optional[str] = None


@dataclass
class RepoStatus:
    name: str
    exists: bool
    branch: str = ""
    is_clean: bool = False
    ahead: int = 0
    behind: int = 0
    last_commit: str = ""


class MultiRepoManager:
    def __init__(self, base_dir: str = "./repos"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._repos: Dict[str, RepoConfig] = {}

    def register(self, config: RepoConfig) -> None:
        if config.local_path is None:
            config.local_path = str(self.base_dir / config.name)
        self._repos[config.name] = config

    def get_local_path(self, name: str) -> Optional[Path]:
        config = self._repos.get(name)
        if config and config.local_path:
            return Path(config.local_path)
        return None

    def clone(self, name: str) -> Path:
        config = self._repos.get(name)
        if not config:
            raise ValueError(f"Repository '{name}' not registered")

        local_path = Path(config.local_path)
        if local_path.exists():
            return self.pull(name)

        env = os.environ.copy()
        if config.auth_token:
            env["GIT_ASKPASS"] = "echo"
            env["GIT_PASSWORD"] = config.auth_token

        url = config.url
        if config.auth_token and url.startswith("https://"):
            url = url.replace("https://", f"https://oauth2:{config.auth_token}@")

        subprocess.run(
            ["git", "clone", "-b", config.branch, url, str(local_path)],
            env=env,
            check=True,
            capture_output=True,
        )
        return local_path

    def pull(self, name: str) -> Path:
        config = self._repos.get(name)
        if not config:
            raise ValueError(f"Repository '{name}' not registered")

        local_path = Path(config.local_path)
        if not local_path.exists():
            return self.clone(name)

        subprocess.run(
            ["git", "-C", str(local_path), "fetch", "origin"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(local_path), "checkout", config.branch],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(local_path), "pull", "origin", config.branch],
            check=True,
            capture_output=True,
        )
        return local_path

    def status(self, name: str) -> RepoStatus:
        config = self._repos.get(name)
        if not config:
            raise ValueError(f"Repository '{name}' not registered")

        local_path = Path(config.local_path)
        if not local_path.exists():
            return RepoStatus(name=name, exists=False)

        result = subprocess.run(
            ["git", "-C", str(local_path), "status", "--porcelain", "-b"],
            capture_output=True,
            text=True,
            check=False,
        )

        is_clean = True
        branch = config.branch
        ahead = 0
        behind = 0

        for line in result.stdout.splitlines():
            if line.startswith("##"):
                parts = line[3:].split("...")
                branch = parts[0]
                if len(parts) > 1:
                    tracking = parts[1]
                    if "[ahead " in tracking:
                        ahead_str = tracking.split("[ahead ")[1].split(",")[0].split("]")[0]
                        ahead = int(ahead_str)
                    if "[behind " in tracking:
                        behind_str = tracking.split("[behind ")[1].split("]")[0]
                        behind = int(behind_str)
            elif line.strip():
                is_clean = False

        commit_result = subprocess.run(
            ["git", "-C", str(local_path), "log", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            check=False,
        )
        last_commit = commit_result.stdout.strip()

        return RepoStatus(
            name=name,
            exists=True,
            branch=branch,
            is_clean=is_clean,
            ahead=ahead,
            behind=behind,
            last_commit=last_commit,
        )

    def create_branch(self, name: str, branch_name: str, base: str = "main") -> None:
        local_path = self.get_local_path(name)
        if not local_path or not local_path.exists():
            raise ValueError(f"Repository '{name}' not cloned")

        subprocess.run(
            ["git", "-C", str(local_path), "checkout", "-b", branch_name, base],
            check=True,
            capture_output=True,
        )

    def commit_changes(self, name: str, message: str, files: Optional[List[str]] = None) -> None:
        local_path = self.get_local_path(name)
        if not local_path or not local_path.exists():
            raise ValueError(f"Repository '{name}' not cloned")

        if files:
            for f in files:
                subprocess.run(
                    ["git", "-C", str(local_path), "add", f],
                    check=True,
                    capture_output=True,
                )
        else:
            subprocess.run(
                ["git", "-C", str(local_path), "add", "."],
                check=True,
                capture_output=True,
            )

        subprocess.run(
            ["git", "-C", str(local_path), "commit", "-m", message],
            check=True,
            capture_output=True,
        )

    def list_repos(self) -> List[str]:
        return list(self._repos.keys())
