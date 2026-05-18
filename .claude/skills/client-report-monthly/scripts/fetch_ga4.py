"""fetch_ga4.py — Google Analytics 4 data fetcher cho monthly report.

Authentication: Service Account.
  1. Tạo Service Account tại Google Cloud Console → Enable Analytics Data API
  2. Download JSON key → lưu vào credentials/service_account.json
  3. Vào GA4 Admin → Property Access Management → Add email service account → Viewer

Env vars (.env):
  GA4_SERVICE_ACCOUNT_PATH — path tới service_account.json (default: credentials/service_account.json)
  GA4_PROPERTY_ID          — GA4 Property ID dạng số, vd: 123456789 (KHÔNG có "properties/")
"""
from __future__ import annotations

import calendar
import json
import os
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _month_range(ym: str) -> tuple[str, str]:
    y, m = int(ym[:4]), int(ym[5:7])
    last = calendar.monthrange(y, m)[1]
    return f"{ym}-01", f"{ym}-{last:02d}"


def _month_label(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"Tháng {m}/{y}"


# ─── Main class ───────────────────────────────────────────────────────────────

class GA4Fetcher:
    """Google Analytics 4 fetcher — trả về full report dict."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.client   = None
        self.prop_id  = ""

    def authenticate(self, property_id: str | None = None) -> None:
        """Khởi tạo GA4 Data API client bằng Service Account."""
        if self.use_mock:
            return
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise ImportError(
                "Thiếu package: pip install google-analytics-data"
            )

        sa_path = Path(os.getenv("GA4_SERVICE_ACCOUNT_PATH", "credentials/service_account.json"))
        if not sa_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy {sa_path}\n"
                "→ Tạo Service Account → Download JSON → lưu vào credentials/"
            )

        creds       = Credentials.from_service_account_file(
            str(sa_path),
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        self.client  = BetaAnalyticsDataClient(credentials=creds)
        self.prop_id = property_id or os.getenv("GA4_PROPERTY_ID", "")
        if not self.prop_id:
            raise ValueError("GA4_PROPERTY_ID chưa được set trong .env")
        print(f"   ✅ GA4 authenticated (property {self.prop_id})")

    def _run(self, dimensions: list, metrics: list,
             start: str, end: str,
             dim_filter=None, limit: int = 50) -> object:
        from google.analytics.data_v1beta.types import DateRange, RunReportRequest
        req = RunReportRequest(
            property    = f"properties/{self.prop_id}",
            date_ranges = [DateRange(start_date=start, end_date=end)],
            dimensions  = dimensions,
            metrics     = metrics,
            limit       = limit,
        )
        if dim_filter:
            req.dimension_filter = dim_filter
        return self.client.run_report(req)

    def _organic_filter(self):
        from google.analytics.data_v1beta.types import FilterExpression, Filter
        return FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(value="Organic Search"),
            )
        )

    def get_full_report(self, property_id: str, year_month: str) -> dict:
        """Trả về dict đầy đủ — cùng structure với mock_ga4.json."""
        if self.use_mock:
            with open(TESTS_DIR / "mock_ga4.json", encoding="utf-8") as f:
                return json.load(f)

        self.prop_id = property_id or self.prop_id
        prev_ym      = _prev_month(year_month)
        c_start, c_end = _month_range(year_month)
        p_start, p_end = _month_range(prev_ym)

        print(f"   📡 GA4: fetch {year_month} ({c_start} → {c_end})")

        from google.analytics.data_v1beta.types import Dimension, Metric

        dims_none    = []
        dims_channel = [Dimension(name="sessionDefaultChannelGroup")]
        dims_landing = [Dimension(name="landingPage"), Dimension(name="sessionDefaultChannelGroup")]
        dims_date    = [Dimension(name="date")]
        core_metrics = [
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="newUsers"),
            Metric(name="conversions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ]

        def _parse_summary(resp) -> dict:
            """Aggregate all rows into a single summary."""
            s = u = nu = conv = br_sum = dur_sum = 0
            for row in resp.rows:
                mv = row.metric_values
                s    += int(mv[0].value)
                u    += int(mv[1].value)
                nu   += int(mv[2].value)
                conv += int(mv[3].value)
            # bounceRate and avgDuration are weighted averages; take first row or recompute
            if resp.rows:
                total_s = sum(int(r.metric_values[0].value) for r in resp.rows)
                if total_s:
                    br_sum  = sum(float(r.metric_values[4].value) * int(r.metric_values[0].value) for r in resp.rows) / total_s
                    dur_sum = sum(float(r.metric_values[5].value) * int(r.metric_values[0].value) for r in resp.rows) / total_s
            return {
                "sessions":               s,
                "users":                  u,
                "new_users":              nu,
                "conversions":            conv,
                "bounce_rate":            round(br_sum,  3),
                "avg_session_duration_s": int(dur_sum),
                "conversion_rate":        round(conv / s, 4) if s else 0,
            }

        # ── All-channel summary (total sessions) ──────────────────────────
        c_all = self._run(dims_channel, core_metrics, c_start, c_end, limit=20)
        p_all = self._run(dims_channel, core_metrics, p_start, p_end, limit=20)
        c_sum = _parse_summary(c_all)
        p_sum = _parse_summary(p_all)

        # ── Organic sessions ───────────────────────────────────────────────
        c_org = self._run(dims_none, core_metrics, c_start, c_end, self._organic_filter(), limit=1)
        if c_org.rows:
            mv = c_org.rows[0].metric_values
            c_sum["organic_sessions"] = int(mv[0].value)
        else:
            c_sum["organic_sessions"] = 0

        p_org = self._run(dims_none, core_metrics, p_start, p_end, self._organic_filter(), limit=1)
        if p_org.rows:
            mv = p_org.rows[0].metric_values
            p_sum["organic_sessions"] = int(mv[0].value)
        else:
            p_sum["organic_sessions"] = 0

        # ── Traffic by source ──────────────────────────────────────────────
        def _traffic_sources(resp, total_s: int) -> list[dict]:
            result = []
            for row in resp.rows:
                s = int(row.metric_values[0].value)
                result.append({
                    "source":      row.dimension_values[0].value,
                    "sessions":    s,
                    "pct":         round(s / total_s, 3) if total_s else 0,
                    "conversions": int(row.metric_values[3].value),
                })
            return sorted(result, key=lambda x: x["sessions"], reverse=True)

        traffic_by_source = {
            "current":  _traffic_sources(c_all, c_sum["sessions"]),
            "previous": _traffic_sources(p_all, p_sum["sessions"]),
        }

        # ── Top landing pages (organic) ────────────────────────────────────
        landing_metrics = [
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="conversions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ]
        c_lp = self._run(dims_landing, landing_metrics, c_start, c_end, self._organic_filter(), limit=10)
        p_lp = self._run(dims_landing, landing_metrics, p_start, p_end, self._organic_filter(), limit=10)

        p_lp_map = {}
        for row in p_lp.rows:
            pg = row.dimension_values[0].value
            p_lp_map[pg] = {
                "sessions":    int(row.metric_values[0].value),
                "conversions": int(row.metric_values[2].value),
            }

        top_landing_pages = []
        for row in c_lp.rows:
            pg    = row.dimension_values[0].value
            pg_r  = "/" + pg.split("/", 3)[-1] if pg.count("/") >= 3 else pg
            prev  = p_lp_map.get(pg, {})
            top_landing_pages.append({
                "page":             pg_r,
                "sessions":         int(row.metric_values[0].value),
                "users":            int(row.metric_values[1].value),
                "conversions":      int(row.metric_values[2].value),
                "bounce_rate":      round(float(row.metric_values[3].value), 3),
                "avg_duration_s":   int(float(row.metric_values[4].value)),
                "prev_sessions":    prev.get("sessions",    0),
                "prev_conversions": prev.get("conversions", 0),
            })

        # ── Weekly trend ───────────────────────────────────────────────────
        from google.analytics.data_v1beta.types import OrderBy
        wk_resp = self._run(dims_date, [Metric(name="sessions"), Metric(name="conversions")],
                            c_start, c_end, self._organic_filter(), limit=31)
        from collections import defaultdict
        wk_agg: dict[str, dict] = defaultdict(lambda: {"sessions": 0, "conversions": 0})
        for row in wk_resp.rows:
            from datetime import date as _dt
            d  = _dt.fromisoformat(row.dimension_values[0].value)
            wk = f"W{d.isocalendar()[1]:02d}"
            wk_agg[wk]["sessions"]    += int(row.metric_values[0].value)
            wk_agg[wk]["conversions"] += int(row.metric_values[1].value)
        weekly_trend = [
            {"week": wk, "sessions": v["sessions"], "organic": v["sessions"], "conversions": v["conversions"]}
            for wk, v in sorted(wk_agg.items())
        ]

        # ── Goals (conversions by event) ───────────────────────────────────
        goals = [
            {
                "name":            "Tổng chuyển đổi",
                "completions":     c_sum["conversions"],
                "prev_completions": p_sum["conversions"],
                "conversion_rate":  c_sum["conversion_rate"],
            }
        ]

        return {
            "period": {
                "current":  {"label": _month_label(year_month), "start": c_start, "end": c_end},
                "previous": {"label": _month_label(prev_ym),    "start": p_start, "end": p_end},
            },
            "summary": {
                "current":  c_sum,
                "previous": p_sum,
            },
            "traffic_by_source": traffic_by_source,
            "top_landing_pages": top_landing_pages,
            "weekly_trend":      weekly_trend,
            "goals":             goals,
        }
