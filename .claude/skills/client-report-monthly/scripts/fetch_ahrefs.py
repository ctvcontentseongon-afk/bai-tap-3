"""fetch_ahrefs.py — Lấy dữ liệu Ahrefs cho monthly report."""

from __future__ import annotations

import json
import os
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"
AHREFS_API_BASE = "https://api.ahrefs.com/v3"


class AhrefsFetcher:
    """Pull Ahrefs data qua REST API v3."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.api_key = os.getenv("AHREFS_API_KEY", "")

    def _load_mock(self) -> dict:
        with open(TESTS_DIR / "mock_ahrefs.json", encoding="utf-8") as f:
            return json.load(f)

    def _get(self, endpoint: str, params: dict) -> dict:
        """HTTP GET đến Ahrefs API."""
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(
            f"{AHREFS_API_BASE}/{endpoint}",
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_domain_rating(self, domain: str, year_month: str) -> dict:
        """Lấy Domain Rating hiện tại và tháng trước."""
        if self.use_mock:
            return self._load_mock()["domain_rating"]

        data = self._get("domain-rating", {"target": domain, "date": f"{year_month}-01"})
        return {
            "current": data.get("domain_rating", 0),
            "previous": data.get("domain_rating_prev", 0),
        }

    def get_referring_domains(self, domain: str, year_month: str) -> dict:
        """Số referring domains hiện tại và growth."""
        if self.use_mock:
            return self._load_mock()["referring_domains"]

        data = self._get(
            "site-explorer/referring-domains",
            {"target": domain, "date_from": f"{year_month}-01", "mode": "subdomains", "limit": 1},
        )
        return {
            "current": data.get("refdomains", 0),
            "new_this_month": data.get("refdomains_new", 0),
            "lost_this_month": data.get("refdomains_lost", 0),
        }

    def get_new_backlinks(self, domain: str, year_month: str, limit: int = 10) -> list[dict]:
        """Danh sách backlinks mới trong tháng."""
        if self.use_mock:
            return self._load_mock()["new_backlinks"][:limit]

        data = self._get(
            "site-explorer/new-lost-backlinks",
            {
                "target": domain,
                "date_from": f"{year_month}-01",
                "mode": "subdomains",
                "limit": limit,
                "history": "new",
            },
        )
        return [
            {
                "source": item.get("url_from_domain", ""),
                "target": item.get("url_to", ""),
                "dr": item.get("domain_rating_source", 0),
                "type": "dofollow" if not item.get("nofollow") else "nofollow",
            }
            for item in data.get("backlinks", [])
        ]
