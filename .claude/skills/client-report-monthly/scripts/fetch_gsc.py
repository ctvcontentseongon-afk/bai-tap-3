"""fetch_gsc.py — Lấy dữ liệu GSC cho monthly report."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import pandas as pd


TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"


class GSCFetcher:
    """Pull GSC data phục vụ monthly report."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.service = None

    def authenticate(self) -> None:
        """OAuth 2.0 flow cho GSC API."""
        if self.use_mock:
            return
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("pip install google-api-python-client google-auth-oauthlib")

        scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
        secrets_path = os.getenv("GSC_CLIENT_SECRETS_PATH", "credentials/gsc_client_secrets.json")
        token_path = os.getenv("GSC_TOKEN_PATH", "credentials/gsc_token.json")

        creds = None
        if Path(token_path).exists():
            creds = Credentials.from_authorized_user_file(token_path, scopes)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, scopes)
            creds = flow.run_local_server(port=0)
            Path(token_path).write_text(creds.to_json())
        self.service = build("searchconsole", "v1", credentials=creds)

    def _load_mock(self) -> dict:
        with open(TESTS_DIR / "mock_gsc.json", encoding="utf-8") as f:
            return json.load(f)

    def _query_api(
        self,
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions: list[str],
    ) -> list[dict]:
        response = (
            self.service.searchanalytics()
            .query(
                siteUrl=f"sc-domain:{site_url}",
                body={"startDate": start_date, "endDate": end_date, "dimensions": dimensions, "rowLimit": 500},
            )
            .execute()
        )
        return response.get("rows", [])

    def get_monthly_summary(self, site_url: str, year_month: str) -> dict:
        """Tổng hợp clicks, impressions, CTR, avg position cả tháng."""
        if self.use_mock:
            return self._load_mock()["summary"]

        start_date = f"{year_month}-01"
        # Ngày cuối tháng
        y, m = map(int, year_month.split("-"))
        import calendar
        last_day = calendar.monthrange(y, m)[1]
        end_date = f"{year_month}-{last_day:02d}"

        rows = self._query_api(site_url, start_date, end_date, ["date"])
        total_clicks = sum(r.get("clicks", 0) for r in rows)
        total_impressions = sum(r.get("impressions", 0) for r in rows)
        return {
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr": total_clicks / total_impressions if total_impressions else 0,
            "avg_position": sum(r.get("position", 0) for r in rows) / len(rows) if rows else 0,
        }

    def get_top_queries(self, site_url: str, year_month: str, limit: int = 10) -> list[dict]:
        """Top queries theo clicks."""
        if self.use_mock:
            return self._load_mock()["top_queries"][:limit]

        start_date = f"{year_month}-01"
        import calendar
        y, m = map(int, year_month.split("-"))
        end_date = f"{year_month}-{calendar.monthrange(y, m)[1]:02d}"
        rows = self._query_api(site_url, start_date, end_date, ["query"])
        result = [
            {"query": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"],
             "ctr": r["ctr"], "position": r["position"]}
            for r in rows
        ]
        return sorted(result, key=lambda x: x["clicks"], reverse=True)[:limit]

    def get_top_pages(self, site_url: str, year_month: str, limit: int = 10) -> list[dict]:
        """Top pages theo clicks."""
        if self.use_mock:
            return self._load_mock()["top_pages"][:limit]

        start_date = f"{year_month}-01"
        import calendar
        y, m = map(int, year_month.split("-"))
        end_date = f"{year_month}-{calendar.monthrange(y, m)[1]:02d}"
        rows = self._query_api(site_url, start_date, end_date, ["page"])
        result = [
            {"page": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"], "ctr": r["ctr"]}
            for r in rows
        ]
        return sorted(result, key=lambda x: x["clicks"], reverse=True)[:limit]
