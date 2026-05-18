"""data_fetcher.py — Orchestrator: gọi 3 nguồn API và tổng hợp data cho report.

Usage (real API):
    from data_fetcher import DataFetcher
    data = DataFetcher().fetch_all(
        domain       = "viettelstore.vn",
        ga4_property = "123456789",
        year_month   = "2026-05",
        actions_file = "path/to/actions.json",  # optional
    )
    # data keys: gsc, ga4, ahrefs, comparison, actions

Usage (mock):
    data = DataFetcher(use_mock=True).fetch_all(
        domain="viettelstore.vn", ga4_property="", year_month="2026-04"
    )
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
MOCK_DIR  = SKILL_DIR / "tests" / "mock_data"


def _delta(cur, prev) -> tuple[float, float]:
    """Trả về (delta_abs, delta_pct)."""
    delta_abs = cur - prev
    delta_pct = round(delta_abs / prev, 4) if prev else 0.0
    return round(delta_abs, 4), delta_pct


def _status(delta_pct: float, higher_is_better: bool) -> str:
    threshold = 0.03
    if abs(delta_pct) < threshold:
        return "neutral"
    improved = delta_pct > 0 if higher_is_better else delta_pct < 0
    return "good" if improved else "bad"


def _fmt_pct(v: float) -> str:
    return f"{v*100:+.1f}%"


def _build_comparison(gsc: dict, ga4: dict, ahrefs: dict, year_month: str) -> dict:
    """Tự động sinh comparison_data từ 3 nguồn — structure khớp mock_comparison.json."""
    y, m = int(year_month[:4]), int(year_month[5:7])
    prev_m = m - 1 if m > 1 else 12
    prev_y = y if m > 1 else y - 1
    period_cur  = f"Tháng {m}/{y}"
    period_prev = f"Tháng {prev_m}/{prev_y}"

    ga4_cur  = ga4["summary"]["current"]
    ga4_prev = ga4["summary"]["previous"]
    gsc_cur  = gsc["summary"]["current"]
    gsc_prev = gsc["summary"]["previous"]
    ahr_cur  = ahrefs["domain_rating"]["current"]
    ahr_prev = ahrefs["domain_rating"]["previous"]
    rd_cur   = ahrefs["referring_domains"]["current"]
    rd_prev  = ahrefs["referring_domains"]["previous"]

    def _metric(id_, name, source, cur, prev, unit, higher_is_better, note=""):
        da, dp = _delta(cur, prev)
        st = _status(dp, higher_is_better)
        label = "tăng" if da > 0 else "giảm"
        sign  = "+" if da > 0 else ""
        interp = (
            f"{name} {label} {_fmt_pct(dp)} ({period_prev} → {period_cur}). "
            f"Giá trị: {prev} → {cur} ({sign}{da:.4g} {unit}). {note}"
        ).strip()
        return {
            "id":               id_,
            "name":             name,
            "source":           source,
            "value_current":    cur,
            "value_previous":   prev,
            "delta_abs":        da,
            "delta_pct":        dp,
            "unit":             unit,
            "higher_is_better": higher_is_better,
            "status":           st,
            "interpretation":   interp,
            "possible_causes":  [],
            "suggested_actions": [],
        }

    sessions_cur  = ga4_cur["sessions"]
    sessions_prev = ga4_prev["sessions"]
    conv_cur      = ga4_cur["conversions"]
    conv_prev     = ga4_prev["conversions"]
    br_cur        = ga4_cur["bounce_rate"]
    br_prev       = ga4_prev["bounce_rate"]
    dur_cur       = ga4_cur["avg_session_duration_s"]
    dur_prev      = ga4_prev["avg_session_duration_s"]

    metrics = [
        _metric("sessions",          "Phiên truy cập (Sessions)",               "GA4",    sessions_cur,        sessions_prev,       "phiên",     True),
        _metric("gsc_clicks",        "Lượt nhấp GSC (Clicks)",                  "GSC",    gsc_cur["clicks"],   gsc_prev["clicks"],  "lượt nhấp", True),
        _metric("conversions",       "Chuyển đổi (Conversions)",                "GA4",    conv_cur,            conv_prev,           "chuyển đổi",True),
        _metric("domain_rating",     "Thẩm quyền tên miền — DR (Domain Rating)","Ahrefs", ahr_cur,             ahr_prev,            "điểm",      True),
        _metric("referring_domains", "Tên miền liên kết (Referring Domains)",   "Ahrefs", rd_cur,              rd_prev,             "tên miền",  True),
        _metric("bounce_rate",       "Tỷ lệ thoát (Bounce Rate)",               "GA4",    br_cur,              br_prev,             "%",         False),
        _metric("avg_session_duration","Thời gian phiên trung bình",            "GA4",    dur_cur,             dur_prev,            "giây",      True),
        _metric("gsc_ctr",           "Tỷ lệ nhấp trung bình — CTR (GSC)",       "GSC",    gsc_cur["ctr"],      gsc_prev["ctr"],     "%",         True),
        _metric("avg_position",      "Vị trí trung bình (Avg Position — GSC)",  "GSC",    gsc_cur["avg_position"], gsc_prev["avg_position"], "vị trí", False),
    ]

    good_count = sum(1 for m_ in metrics if m_["status"] == "good")
    score = round(good_count / len(metrics) * 10)

    return {
        "_meta": {
            "description":     "So sánh tổng hợp các chỉ số (tự động từ API).",
            "period_current":  period_cur,
            "period_previous": period_prev,
        },
        "metrics": metrics,
        "overall_assessment": {
            "score":     score,
            "max_score": 10,
            "label":     "Tháng tốt" if score >= 6 else ("Tháng trung bình" if score >= 4 else "Tháng khó"),
            "summary":   f"{period_cur}: {good_count}/{len(metrics)} chỉ số cải thiện.",
        },
    }


def _default_actions(year_month: str) -> dict:
    """Actions tối thiểu khi không cung cấp file — chỉ có skeleton."""
    y, m = int(year_month[:4]), int(year_month[5:7])
    next_m = m + 1 if m < 12 else 1
    next_y = y if m < 12 else y + 1
    return {
        "_meta": {
            "description":    "Actions tự động — hãy cập nhật file JSON để điền nội dung thực tế.",
            "period_current": f"Tháng {m}/{y}",
            "period_next":    f"Tháng {next_m}/{next_y}",
        },
        "completed_this_month": [],
        "in_progress_next_month": [],
        "long_term_recommendations": [],
        "summary": {
            "completed_count":      0,
            "in_progress_count":    0,
            "long_term_count":      0,
            "p1_tasks_next_month":  0,
            "key_focus_next_month": "Cập nhật actions.json để điền kế hoạch",
        },
    }


class DataFetcher:
    """Gọi 3 fetchers, tổng hợp thành dict đầy đủ cho report_generator."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock

    def fetch_all(
        self,
        domain:       str,
        ga4_property: str,
        year_month:   str,
        actions_file: Optional[str] = None,
        gsc_site_url: Optional[str] = None,
    ) -> dict:
        """
        Trả về dict với keys: gsc, ga4, ahrefs, comparison, actions.
        Khi use_mock=True: đọc từ tests/mock_data/*.json.
        """
        from fetch_gsc    import GSCFetcher
        from fetch_ga4    import GA4Fetcher
        from fetch_ahrefs import AhrefsFetcher

        # ── GSC ───────────────────────────────────────────────────────────────
        gsc_fetcher = GSCFetcher(use_mock=self.use_mock)
        gsc_fetcher.authenticate()
        gsc_data = gsc_fetcher.get_full_report(domain=domain, year_month=year_month)

        # ── GA4 ───────────────────────────────────────────────────────────────
        ga4_fetcher = GA4Fetcher(use_mock=self.use_mock)
        ga4_fetcher.authenticate(property_id=ga4_property)
        ga4_data = ga4_fetcher.get_full_report(property_id=ga4_property, year_month=year_month)

        # ── Ahrefs ────────────────────────────────────────────────────────────
        ahr_fetcher = AhrefsFetcher(use_mock=self.use_mock)
        ahr_fetcher.authenticate()
        ahr_data = ahr_fetcher.get_full_report(domain=domain, year_month=year_month)

        # ── Comparison (auto-generated) ────────────────────────────────────
        if self.use_mock:
            with open(MOCK_DIR / "mock_comparison.json", encoding="utf-8") as f:
                comparison_data = json.load(f)
        else:
            comparison_data = _build_comparison(gsc_data, ga4_data, ahr_data, year_month)

        # ── Actions ───────────────────────────────────────────────────────────
        if self.use_mock:
            with open(MOCK_DIR / "mock_actions.json", encoding="utf-8") as f:
                actions_data = json.load(f)
        elif actions_file and Path(actions_file).exists():
            with open(actions_file, encoding="utf-8") as f:
                actions_data = json.load(f)
        else:
            actions_data = _default_actions(year_month)

        return {
            "gsc":        gsc_data,
            "ga4":        ga4_data,
            "ahrefs":     ahr_data,
            "comparison": comparison_data,
            "actions":    actions_data,
        }
