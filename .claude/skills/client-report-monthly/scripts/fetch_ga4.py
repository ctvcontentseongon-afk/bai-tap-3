"""fetch_ga4.py — Lấy dữ liệu GA4 cho monthly report."""

from __future__ import annotations

import json
import os
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"


class GA4Fetcher:
    """Pull GA4 data phục vụ monthly report."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.client = None

    def authenticate(self, property_id: str | None = None) -> None:
        """Khởi tạo GA4 Data API client."""
        if self.use_mock:
            return
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise ImportError("pip install google-analytics-data google-auth")

        creds_path = os.getenv("GA4_SERVICE_ACCOUNT_PATH", "credentials/service_account.json")
        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        self.client = BetaAnalyticsDataClient(credentials=creds)
        self.property_id = property_id or os.getenv("GA4_PROPERTY_ID", "")

    def _load_mock(self) -> dict:
        with open(TESTS_DIR / "mock_ga4.json", encoding="utf-8") as f:
            return json.load(f)

    def get_organic_sessions(self, property_id: str, year_month: str) -> dict:
        """Tổng organic sessions, users, conversions cả tháng."""
        if self.use_mock:
            return self._load_mock()["summary"]

        import calendar
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
        )

        y, m = map(int, year_month.split("-"))
        start_date = f"{year_month}-01"
        end_date = f"{year_month}-{calendar.monthrange(y, m)[1]:02d}"

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="newUsers"),
                Metric(name="engagementRate"),
                Metric(name="conversions"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(value="Organic Search"),
                )
            ),
        )
        response = self.client.run_report(request)
        row = response.rows[0] if response.rows else None
        if not row:
            return {}
        return {
            "organic_sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "new_users": int(row.metric_values[2].value),
            "engagement_rate": float(row.metric_values[3].value),
            "conversions": int(row.metric_values[4].value),
        }

    def get_top_landing_pages(self, property_id: str, year_month: str, limit: int = 10) -> list[dict]:
        """Top landing pages theo organic sessions."""
        if self.use_mock:
            return self._load_mock()["top_landing_pages"][:limit]

        import calendar
        from google.analytics.data_v1beta.types import (
            DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
        )

        y, m = map(int, year_month.split("-"))
        start_date = f"{year_month}-01"
        end_date = f"{year_month}-{calendar.monthrange(y, m)[1]:02d}"

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="landingPage"), Dimension(name="sessionDefaultChannelGroup")],
            metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="conversions")],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(value="Organic Search"),
                )
            ),
            limit=limit,
            order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        )
        response = self.client.run_report(request)
        return [
            {
                "page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
            }
            for row in response.rows
        ]
