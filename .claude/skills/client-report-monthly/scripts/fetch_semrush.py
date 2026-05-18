"""fetch_semrush.py — Semrush API fetcher cho monthly report.

Authentication: API Key.
  1. Đăng nhập semrush.com → Account Settings → API → Copy API key
  2. Thêm vào .env: SEMRUSH_API_KEY=your_key_here

Env vars (.env):
  SEMRUSH_API_KEY — Semrush API key

Semrush API docs:
  - Domain Analytics: https://developer.semrush.com/api/v3/analytics/domain-reports/
  - Backlinks:        https://developer.semrush.com/api/v3/analytics/backlinks/

Lưu ý API units:
  - domain_ranks: 10 units/request
  - backlinks_overview: 1 unit/request
  - backlinks list (new/lost): 10 units/100 rows
  - referring_domains (new/lost): 10 units/100 rows
  → Mỗi lần fetch_all: ~100-150 units
"""
from __future__ import annotations

import calendar
import json
import os
from pathlib import Path
from urllib.parse import urlparse

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"
BASE_URL   = "https://api.semrush.com"
BL_BASE    = "https://api.semrush.com/analytics/v1"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _month_range(ym: str) -> tuple[str, str]:
    y, m = int(ym[:4]), int(ym[5:7])
    last = calendar.monthrange(y, m)[1]
    return f"{ym}-01", f"{ym}-{last:02d}"


def _display_date(ym: str) -> str:
    """Semrush historical date format: YYYYMM01."""
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y}{m:02d}01"


def _root_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc.lstrip("www.") if netloc else url
    except Exception:
        return url


# ─── Main class ───────────────────────────────────────────────────────────────

class SemrushFetcher:
    """Semrush API fetcher — trả về full report dict (same structure as AhrefsFetcher)."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.api_key  = os.getenv("SEMRUSH_API_KEY", "")

    def authenticate(self) -> None:
        if self.use_mock:
            return
        if not self.api_key:
            raise ValueError(
                "SEMRUSH_API_KEY chưa được set trong .env\n"
                "→ Lấy key tại: semrush.com → Account Settings → API"
            )
        print("   ✅ Semrush API key loaded")

    # ── Low-level request helpers ──────────────────────────────────────────────

    def _get_domain_rank(self, domain: str, display_date: str) -> int:
        """Lấy Authority Score từ domain ranks API (CSV response). Trả về int 0-100."""
        import requests
        resp = requests.get(
            BASE_URL + "/",
            params={
                "type":           "domain_ranks",
                "key":            self.api_key,
                "export_columns": "As",
                "domain":         domain,
                "database":       "us",
                "display_date":   display_date,
            },
            timeout=30,
        )
        self._check_status(resp)
        # Response CSV: "As\n42\n"
        lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]
        if len(lines) >= 2:
            try:
                return int(lines[1])
            except ValueError:
                pass
        return 0

    def _get_backlinks_overview(self, domain: str) -> dict:
        """Trả về: total, domains_num, follows_num, nofollows_num, ascore."""
        import requests
        resp = requests.get(
            BL_BASE + "/",
            params={
                "key":         self.api_key,
                "type":        "backlinks_overview",
                "target":      domain,
                "target_type": "root_domain",
            },
            timeout=30,
        )
        self._check_status(resp)
        return resp.json()

    def _get_backlinks(self, domain: str, filter_type: str, limit: int = 200) -> list:
        """filter_type: 'new' hoặc 'lost'."""
        import requests
        resp = requests.get(
            BL_BASE + "/",
            params={
                "key":            self.api_key,
                "type":           "backlinks",
                "target":         domain,
                "target_type":    "root_domain",
                "display_limit":  limit,
                "display_sort":   "page_ascore_desc",
                "display_filter": f"+|is_{filter_type}||1",
            },
            timeout=30,
        )
        self._check_status(resp)
        return resp.json().get("results", [])

    def _get_referring_domains(self, domain: str, filter_type: str,
                               limit: int = 500) -> list:
        """filter_type: 'new' hoặc 'lost'."""
        import requests
        resp = requests.get(
            BL_BASE + "/",
            params={
                "key":            self.api_key,
                "type":           "referring_domains",
                "target":         domain,
                "target_type":    "root_domain",
                "display_limit":  limit,
                "display_filter": f"+|is_{filter_type}||1",
            },
            timeout=30,
        )
        self._check_status(resp)
        return resp.json().get("results", [])

    def _check_status(self, resp) -> None:
        if resp.status_code in (401, 403):
            raise PermissionError("Semrush API key không hợp lệ hoặc hết quota.")
        if resp.status_code == 402:
            raise PermissionError("Semrush API — hết API units. Kiểm tra quota tại semrush.com.")
        resp.raise_for_status()

    # ── Public interface ───────────────────────────────────────────────────────

    def get_full_report(self, domain: str, year_month: str) -> dict:
        """Trả về dict đầy đủ — cùng structure với mock_ahrefs.json."""
        if self.use_mock:
            with open(TESTS_DIR / "mock_ahrefs.json", encoding="utf-8") as f:
                return json.load(f)

        prev_ym = _prev_month(year_month)

        print(f"   📡 Semrush: fetch {domain} — {year_month}")

        # ── Authority Score (hiện tại + tháng trước) ──────────────────────────
        as_cur  = self._get_domain_rank(domain, _display_date(year_month))
        as_prev = self._get_domain_rank(domain, _display_date(prev_ym))
        if as_prev == 0:
            as_prev = as_cur  # fallback nếu chưa có dữ liệu lịch sử

        # ── Backlinks overview ─────────────────────────────────────────────────
        overview      = self._get_backlinks_overview(domain)
        bl_cur        = overview.get("total",        0)
        rd_cur        = overview.get("domains_num",  0)
        follows_num   = overview.get("follows_num",  0)
        nofollows_num = overview.get("nofollows_num", 0)
        total_typed   = follows_num + nofollows_num
        dofollow_pct  = round(follows_num / total_typed, 2) if total_typed else 0.74

        # ── New / lost backlinks ───────────────────────────────────────────────
        bl_new_list  = self._get_backlinks(domain, "new",  limit=200)
        bl_lost_list = self._get_backlinks(domain, "lost", limit=50)
        bl_new_count  = len(bl_new_list)
        bl_lost_count = len(bl_lost_list)

        # ── New / lost referring domains ───────────────────────────────────────
        rd_new_list  = self._get_referring_domains(domain, "new",  limit=500)
        rd_lost_list = self._get_referring_domains(domain, "lost", limit=500)
        rd_new_count  = len(rd_new_list)
        rd_lost_count = len(rd_lost_list)

        # ── Tính ngược tháng trước ─────────────────────────────────────────────
        # Semrush không có snapshot theo tháng cho backlinks → ước tính
        bl_prev = max(0, bl_cur - bl_new_count + bl_lost_count)
        rd_prev = max(0, rd_cur - rd_new_count + rd_lost_count)

        # ── Parse danh sách backlinks nổi bật ─────────────────────────────────
        def _parse_new(items: list) -> list[dict]:
            result = []
            for b in items:
                result.append({
                    "source": _root_domain(b.get("source_url", "")),
                    "dr":     int(b.get("page_ascore") or b.get("root_source_ascore") or 0),
                    "target": ("/" + b.get("target_url", "").split("/", 3)[-1])
                              if "/" in b.get("target_url", "") else "/",
                    "type":   "nofollow" if b.get("nofollow") else "dofollow",
                    "anchor": b.get("anchor", ""),
                })
            return sorted(result, key=lambda x: x["dr"], reverse=True)

        def _parse_lost(items: list) -> list[dict]:
            result = []
            for b in items:
                result.append({
                    "source": _root_domain(b.get("source_url", "")),
                    "dr":     int(b.get("page_ascore") or 0),
                    "target": ("/" + b.get("target_url", "").split("/", 3)[-1])
                              if "/" in b.get("target_url", "") else "/",
                    "type":   "nofollow" if b.get("nofollow") else "dofollow",
                    "reason": "",
                })
            return result

        new_notable    = _parse_new(bl_new_list)[:8]
        lost_backlinks = _parse_lost(bl_lost_list)[:5]

        y, m = int(year_month[:4]), int(year_month[5:7])

        return {
            "period": {
                "current":  {"label": f"Tháng {m}/{y}"},
                "previous": {"label": f"Tháng {int(prev_ym[5:7])}/{int(prev_ym[:4])}"},
            },
            "domain_rating": {         # key giữ nguyên để tương thích, giá trị = Semrush AS
                "current":  as_cur,
                "previous": as_prev,
                "history":  [],
            },
            "referring_domains": {
                "current":         rd_cur,
                "previous":        rd_prev,
                "new_this_month":  rd_new_count,
                "lost_this_month": rd_lost_count,
                "net_change":      rd_new_count - rd_lost_count,
            },
            "backlinks": {
                "total":           bl_cur,
                "total_previous":  bl_prev,
                "new_this_month":  bl_new_count,
                "lost_this_month": bl_lost_count,
                "dofollow_pct":    dofollow_pct,
                "nofollow_pct":    round(1 - dofollow_pct, 2),
            },
            "new_notable_backlinks": new_notable,
            "lost_backlinks":        lost_backlinks,
        }
