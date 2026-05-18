import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import httpx


@dataclass
class PullRequest:
    number: int
    title: str
    url: str
    state: str
    branch: str
    base_branch: str


@dataclass
class Release:
    tag: str
    name: str
    url: str
    body: str


class GitProvider(ABC):
    @abstractmethod
    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> PullRequest:
        pass

    @abstractmethod
    async def list_pull_requests(
        self, repo: str, state: str = "open"
    ) -> List[PullRequest]:
        pass

    @abstractmethod
    async def create_release(
        self,
        repo: str,
        tag: str,
        name: str,
        body: str,
        target_commitish: str = "main",
    ) -> Release:
        pass


class GitHubProvider(GitProvider):
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )

    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> PullRequest:
        url = f"{self.base_url}/repos/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return PullRequest(
            number=data["number"],
            title=data["title"],
            url=data["html_url"],
            state=data["state"],
            branch=head,
            base_branch=base,
        )

    async def list_pull_requests(
        self, repo: str, state: str = "open"
    ) -> List[PullRequest]:
        url = f"{self.base_url}/repos/{repo}/pulls"
        response = await self._client.get(url, params={"state": state})
        response.raise_for_status()
        data = response.json()
        return [
            PullRequest(
                number=pr["number"],
                title=pr["title"],
                url=pr["html_url"],
                state=pr["state"],
                branch=pr["head"]["ref"],
                base_branch=pr["base"]["ref"],
            )
            for pr in data
        ]

    async def create_release(
        self,
        repo: str,
        tag: str,
        name: str,
        body: str,
        target_commitish: str = "main",
    ) -> Release:
        url = f"{self.base_url}/repos/{repo}/releases"
        payload = {
            "tag_name": tag,
            "name": name,
            "body": body,
            "target_commitish": target_commitish,
        }
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return Release(
            tag=data["tag_name"],
            name=data["name"],
            url=data["html_url"],
            body=data["body"],
        )

    async def close(self) -> None:
        await self._client.aclose()


class GitLabProvider(GitProvider):
    def __init__(
        self, token: Optional[str] = None, base_url: str = "https://gitlab.com"
    ):
        self.token = token or os.environ.get("GITLAB_TOKEN", "")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(headers={"PRIVATE-TOKEN": self.token})

    def _project_path(self, repo: str) -> str:
        return repo.replace("/", "%2F")

    async def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> PullRequest:
        project = self._project_path(repo)
        url = f"{self.base_url}/api/v4/projects/{project}/merge_requests"
        payload = {
            "source_branch": head,
            "target_branch": base,
            "title": title,
            "description": body,
        }
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return PullRequest(
            number=data["iid"],
            title=data["title"],
            url=data["web_url"],
            state=data["state"],
            branch=head,
            base_branch=base,
        )

    async def list_pull_requests(
        self, repo: str, state: str = "opened"
    ) -> List[PullRequest]:
        project = self._project_path(repo)
        url = f"{self.base_url}/api/v4/projects/{project}/merge_requests"
        response = await self._client.get(url, params={"state": state})
        response.raise_for_status()
        data = response.json()
        return [
            PullRequest(
                number=mr["iid"],
                title=mr["title"],
                url=mr["web_url"],
                state=mr["state"],
                branch=mr["source_branch"],
                base_branch=mr["target_branch"],
            )
            for mr in data
        ]

    async def create_release(
        self,
        repo: str,
        tag: str,
        name: str,
        body: str,
        target_commitish: str = "main",
    ) -> Release:
        project = self._project_path(repo)
        url = f"{self.base_url}/api/v4/projects/{project}/releases"
        payload = {
            "tag_name": tag,
            "name": name,
            "description": body,
            "ref": target_commitish,
        }
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return Release(
            tag=data["tag_name"],
            name=data["name"],
            url=data["_links"]["self"],
            body=data["description"],
        )

    async def close(self) -> None:
        await self._client.aclose()


def create_git_provider(provider: str = "github", **kwargs) -> GitProvider:
    if provider == "github":
        return GitHubProvider(**kwargs)
    elif provider == "gitlab":
        return GitLabProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported git provider: {provider}")
