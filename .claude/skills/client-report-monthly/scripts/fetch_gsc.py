"""fetch_gsc.py — Google Search Console data fetcher cho monthly report.

Authentication: OAuth 2.0 (Desktop app flow).
  1. Tạo OAuth 2.0 Client ID (Desktop) tại Google Cloud Console
  2. Download JSON → lưu vào credentials/gsc_client_secrets.json
  3. Lần đầu chạy sẽ mở browser → đăng nhập → token tự lưu
  4. Lần sau dùng token đã lưu, không cần đăng nhập lại

Env vars (.env):
  GSC_CLIENT_SECRETS_PATH  — path tới client_secrets.json (default: credentials/gsc_client_secrets.json)
  GSC_TOKEN_PATH           — path lưu token OAuth (default: credentials/gsc_token.json)
  GSC_SITE_URL             — URL property trong GSC, vd: sc-domain:example.com
                             hoặc https://example.com/ (URL-prefix property)
"""
from __future__ import annotations

import calendar
import json
import os
from collections import defaultdict
from datetime import date as _date
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


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


def _iso_week(date_str: str) -> str:
    d = _date.fromisoformat(date_str)
    return f"W{d.isocalendar()[1]:02d}"


def _site_url(domain: str) -> str:
    """Chuyển domain → GSC site URL format."""
    if domain.startswith("sc-domain:") or domain.startswith("http"):
        return domain
    return f"sc-domain:{domain}"


# ─── Main class ───────────────────────────────────────────────────────────────

class GSCFetcher:
    """Google Search Console fetcher — trả về full report dict."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.service = None

    def authenticate(self) -> None:
        """OAuth 2.0 Desktop flow — mở browser lần đầu, tự refresh sau."""
        if self.use_mock:
            return
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Thiếu package: pip install google-api-python-client google-auth-oauthlib"
            )

        secrets_path = Path(os.getenv("GSC_CLIENT_SECRETS_PATH", "credentials/gsc_client_secrets.json"))
        token_path   = Path(os.getenv("GSC_TOKEN_PATH",           "credentials/gsc_token.json"))

        if not secrets_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy {secrets_path}\n"
                "→ Tạo OAuth 2.0 Client ID tại Google Cloud Console → Download JSON → lưu vào credentials/"
            )

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())

        self.service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        print(f"   ✅ GSC authenticated")

    def _query(self, site_url: str, start: str, end: str,
               dims: list[str], limit: int = 5000) -> list[dict]:
        body = {
            "startDate": start,
            "endDate":   end,
            "dimensions": dims,
            "rowLimit":   limit,
        }
        resp = (
            self.service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
        return resp.get("rows", [])

    def get_full_report(self, domain: str, year_month: str) -> dict:
        """Trả về dict đầy đủ — cùng structure với mock_gsc.json."""
        if self.use_mock:
            with open(TESTS_DIR / "mock_gsc.json", encoding="utf-8") as f:
                return json.load(f)

        site    = _site_url(domain)
        prev_ym = _prev_month(year_month)
        c_start, c_end = _month_range(year_month)
        p_start, p_end = _month_range(prev_ym)

        print(f"   📡 GSC: fetch {year_month} ({c_start} → {c_end})")

        # Fetch by query (cả 2 tháng)
        c_q = self._query(site, c_start, c_end, ["query"])
        p_q = self._query(site, p_start, p_end, ["query"])
        # Fetch by page
        c_p = self._query(site, c_start, c_end, ["page"])
        p_p = self._query(site, p_start, p_end, ["page"])
        # Fetch by date (weekly breakdown)
        c_d = self._query(site, c_start, c_end, ["date"])

        # ── Summary ────────────────────────────────────────────────────────
        def _sum(rows: list[dict]) -> dict:
            imp = sum(r["impressions"] for r in rows)
            clk = sum(r["clicks"]     for r in rows)
            pos = (sum(r["position"] * r["impressions"] for r in rows) / imp) if imp else 0
            return {
                "clicks":       clk,
                "impressions":  imp,
                "ctr":          round(clk / imp, 4) if imp else 0,
                "avg_position": round(pos, 1),
            }

        # ── Top queries ────────────────────────────────────────────────────
        p_q_map = {r["keys"][0]: r for r in p_q}
        top_queries = []
        for r in sorted(c_q, key=lambda x: x["clicks"], reverse=True)[:12]:
            q    = r["keys"][0]
            prev = p_q_map.get(q, {})
            pp   = prev.get("position", r["position"])
            d_pos = round(r["position"] - pp, 1)
            trend = "up" if d_pos < -0.5 else ("down" if d_pos > 0.5 else "stable")
            top_queries.append({
                "query":         q,
                "clicks":        r["clicks"],
                "impressions":   r["impressions"],
                "ctr":           round(r["ctr"],      4),
                "position":      round(r["position"], 1),
                "prev_clicks":   prev.get("clicks", 0),
                "prev_position": round(pp, 1),
                "trend":         trend,
            })

        # ── Top pages ──────────────────────────────────────────────────────
        def _rel(url: str) -> str:
            """https://example.com/path → /path"""
            parts = url.split("/", 3)
            return "/" + parts[3] if len(parts) > 3 else "/"

        p_p_map = {r["keys"][0]: r for r in p_p}
        top_pages = []
        page_changes = []
        for r in sorted(c_p, key=lambda x: x["clicks"], reverse=True)[:10]:
            raw  = r["keys"][0]
            pg   = _rel(raw)
            prev = p_p_map.get(raw, {})
            top_pages.append({
                "page":             pg,
                "clicks":           r["clicks"],
                "impressions":      r["impressions"],
                "ctr":              round(r["ctr"],      4),
                "position":         round(r["position"], 1),
                "prev_clicks":      prev.get("clicks",      0),
                "prev_impressions": prev.get("impressions", 0),
                "prev_position":    round(prev.get("position", r["position"]), 1),
            })

        for r in c_p:
            prev = p_p_map.get(r["keys"][0])
            if prev and prev["clicks"] > 0:
                d = r["clicks"] - prev["clicks"]
                page_changes.append({
                    "page":          _rel(r["keys"][0]),
                    "clicks_delta":  d,
                    "pct_change":    round(d / prev["clicks"], 3),
                })

        top_pages_increasing = sorted(
            [p for p in page_changes if p["pct_change"] > 0],
            key=lambda x: x["pct_change"], reverse=True,
        )[:5]
        top_pages_decreasing = sorted(
            [p for p in page_changes if p["pct_change"] < 0],
            key=lambda x: x["pct_change"],
        )[:4]

        # ── Keywords with big changes ──────────────────────────────────────
        kw_changes = []
        for r in c_q:
            q    = r["keys"][0]
            prev = p_q_map.get(q)
            if prev:
                d = round(r["position"] - prev["position"], 1)
                if abs(d) >= 0.4:
                    kw_changes.append({
                        "query":           q,
                        "position_change": d,
                        "direction":       "improved" if d < 0 else "declined",
                    })
        kw_changes.sort(key=lambda x: abs(x["position_change"]), reverse=True)

        # ── Weekly trend ───────────────────────────────────────────────────
        week_agg: dict[str, dict] = defaultdict(lambda: {"clicks": 0, "impressions": 0})
        for r in c_d:
            wk = _iso_week(r["keys"][0])
            week_agg[wk]["clicks"]      += r["clicks"]
            week_agg[wk]["impressions"] += r["impressions"]
        weekly_trend = [
            {"week": wk, "clicks": v["clicks"], "impressions": v["impressions"]}
            for wk, v in sorted(week_agg.items())
        ]

        # ── Organic keywords count ─────────────────────────────────────────
        def _count_pos(rows, pos_limit):
            return sum(1 for r in rows if r["position"] <= pos_limit)

        organic_keywords = {
            "current":  {
                "top_3":   _count_pos(c_q, 3),
                "top_10":  _count_pos(c_q, 10),
                "top_100": len(c_q),
            },
            "previous": {
                "top_3":   _count_pos(p_q, 3),
                "top_10":  _count_pos(p_q, 10),
                "top_100": len(p_q),
            },
        }

        return {
            "period": {
                "current":  {"label": _month_label(year_month), "start": c_start, "end": c_end},
                "previous": {"label": _month_label(prev_ym),    "start": p_start, "end": p_end},
            },
            "summary": {
                "current":  _sum(c_q),
                "previous": _sum(p_q),
            },
            "top_queries":           top_queries,
            "top_pages":             top_pages,
            "top_pages_increasing":  top_pages_increasing,
            "top_pages_decreasing":  top_pages_decreasing,
            "keywords_with_big_changes": kw_changes[:8],
            "weekly_trend":          weekly_trend,
            "organic_keywords":      organic_keywords,
        }
