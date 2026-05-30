"""GitHub API client — fetches PR data and posts review comments."""
import re
import os
import requests
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PRFile:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: Optional[str] = None


@dataclass
class PRData:
    number: int
    title: str
    body: str
    author: str
    base_branch: str
    head_branch: str
    head_sha: str
    url: str
    additions: int
    deletions: int
    changed_files: int
    files: list[PRFile] = field(default_factory=list)


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    # ── Parsing ──────────────────────────────────────────────────────────────

    @staticmethod
    def parse_pr_url(url: str) -> tuple[str, str, int]:
        """Parse 'https://github.com/owner/repo/pull/123' → (owner, repo, 123)."""
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        m = re.search(pattern, url)
        if not m:
            raise ValueError(f"Invalid GitHub PR URL: {url}")
        return m.group(1), m.group(2), int(m.group(3))

    # ── Fetching ─────────────────────────────────────────────────────────────

    def get_pr(self, owner: str, repo: str, number: int) -> PRData:
        resp = self.session.get(f"{self.BASE}/repos/{owner}/{repo}/pulls/{number}")
        resp.raise_for_status()
        d = resp.json()

        files = self._get_files(owner, repo, number)

        return PRData(
            number=number,
            title=d["title"],
            body=d.get("body") or "",
            author=d["user"]["login"],
            base_branch=d["base"]["ref"],
            head_branch=d["head"]["ref"],
            head_sha=d["head"]["sha"],
            url=d["html_url"],
            additions=d["additions"],
            deletions=d["deletions"],
            changed_files=d["changed_files"],
            files=files,
        )

    def _get_files(self, owner: str, repo: str, number: int) -> list[PRFile]:
        files, page = [], 1
        while True:
            resp = self.session.get(
                f"{self.BASE}/repos/{owner}/{repo}/pulls/{number}/files",
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for f in batch:
                files.append(PRFile(
                    filename=f["filename"],
                    status=f["status"],
                    additions=f["additions"],
                    deletions=f["deletions"],
                    patch=f.get("patch"),
                ))
            if len(batch) < 100:
                break
            page += 1
        return files

    # ── Posting ──────────────────────────────────────────────────────────────

    def post_comment(self, owner: str, repo: str, number: int, body: str) -> str:
        """Post a comment on a PR. Returns the comment URL."""
        resp = self.session.post(
            f"{self.BASE}/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )
        resp.raise_for_status()
        return resp.json()["html_url"]
