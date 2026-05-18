"""fetch_ahrefs.py — Ahrefs API v3 fetcher cho monthly report.

Authentication: API Key (Bearer token).
  1. Đăng nhập ahrefs.com → Settings → API → Copy API key
  2. Thêm vào .env: AHREFS_API_KEY=your_key_here

Env vars (.env):
  AHREFS_API_KEY — Ahrefs API key

Ahrefs API v3 docs: https://docs.ahrefs.com/docs/api-reference
"""
from __future__ import annotations

import calendar
import json
import os
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent / "tests" / "mock_data"
BASE_URL   = "https://api.ahrefs.com/v3"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _prev_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _month_range(ym: str) -> tuple[str, str]:
    y, m = int(ym[:4]), int(ym[5:7])
    last = calendar.monthrange(y, m)[1]
    return f"{ym}-01", f"{ym}-{last:02d}"


# ─── Main class ───────────────────────────────────────────────────────────────

class AhrefsFetcher:
    """Ahrefs REST API v3 fetcher — trả về full report dict."""

    def __init__(self, use_mock: bool = False) -> None:
        self.use_mock = use_mock
        self.api_key  = os.getenv("AHREFS_API_KEY", "")

    def authenticate(self) -> None:
        """Validate API key."""
        if self.use_mock:
            return
        if not self.api_key:
            raise ValueError(
                "AHREFS_API_KEY chưa được set trong .env\n"
                "→ Lấy key tại: ahrefs.com → Settings → API"
            )
        print(f"   ✅ Ahrefs API key loaded")

    def _get(self, endpoint: str, params: dict) -> dict:
        import requests
        resp = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            timeout=30,
        )
        if resp.status_code == 401:
            raise PermissionError("Ahrefs API key không hợp lệ hoặc hết hạn.")
        if resp.status_code == 402:
            raise PermissionError("Ahrefs API — hết quota. Kiểm tra plan tại ahrefs.com.")
        resp.raise_for_status()
        return resp.json()

    def get_full_report(self, domain: str, year_month: str) -> dict:
        """Trả về dict đầy đủ — cùng structure với mock_ahrefs.json."""
        if self.use_mock:
            with open(TESTS_DIR / "mock_ahrefs.json", encoding="utf-8") as f:
                return json.load(f)

        prev_ym        = _prev_month(year_month)
        c_start, c_end = _month_range(year_month)
        p_start, p_end = _month_range(prev_ym)

        print(f"   📡 Ahrefs: fetch {domain} — {year_month}")

        # ── Domain Rating ──────────────────────────────────────────────────
        dr_cur_data  = self._get("site-explorer/domain-rating", {"target": domain, "date": c_end})
        dr_prev_data = self._get("site-explorer/domain-rating", {"target": domain, "date": p_end})
        dr_cur       = int(dr_cur_data.get("domain_rating",  {}).get("domain_rating",  0))
        dr_prev      = int(dr_prev_data.get("domain_rating", {}).get("domain_rating", 0))

        # ── Site metrics (backlinks, referring domains) ────────────────────
        metrics_cur  = self._get("site-explorer/metrics", {"target": domain, "date": c_end, "mode": "subdomains"})
        metrics_prev = self._get("site-explorer/metrics", {"target": domain, "date": p_end, "mode": "subdomains"})
        rd_cur   = int(metrics_cur.get("metrics",  {}).get("refdomains",  0))
        rd_prev  = int(metrics_prev.get("metrics", {}).get("refdomains",  0))
        bl_cur   = int(metrics_cur.get("metrics",  {}).get("backlinks",   0))
        bl_prev  = int(metrics_prev.get("metrics", {}).get("backlinks",   0))

        # ── New / lost referring domains ───────────────────────────────────
        rd_new_data  = self._get("site-explorer/new-lost-referring-domains", {
            "target": domain, "date_from": c_start, "date_to": c_end,
            "mode": "subdomains", "history": "new", "limit": 100,
        })
        rd_lost_data = self._get("site-explorer/new-lost-referring-domains", {
            "target": domain, "date_from": c_start, "date_to": c_end,
            "mode": "subdomains", "history": "lost", "limit": 100,
        })
        rd_new_count  = len(rd_new_data.get("referring_domains",  []))
        rd_lost_count = len(rd_lost_data.get("referring_domains", []))

        # ── New / lost backlinks ───────────────────────────────────────────
        bl_new_data  = self._get("site-explorer/new-lost-backlinks", {
            "target": domain, "date_from": c_start, "date_to": c_end,
            "mode": "subdomains", "history": "new",  "limit": 200,
        })
        bl_lost_data = self._get("site-explorer/new-lost-backlinks", {
            "target": domain, "date_from": c_start, "date_to": c_end,
            "mode": "subdomains", "history": "lost", "limit": 50,
        })
        bl_new_count  = len(bl_new_data.get("backlinks",  []))
        bl_lost_count = len(bl_lost_data.get("backlinks", []))

        # ── Parse notable new backlinks ────────────────────────────────────
        def _parse_bl(items: list) -> list[dict]:
            result = []
            for b in items:
                result.append({
                    "source": b.get("url_from_domain", b.get("domain_from", "")),
                    "dr":     int(b.get("domain_rating_source", b.get("ahrefs_rank", 0))),
                    "target": "/" + b.get("url_to", "").split("/", 3)[-1] if "/" in b.get("url_to", "") else "/",
                    "type":   "nofollow" if b.get("nofollow") else "dofollow",
                    "anchor": b.get("anchor", ""),
                })
            return sorted(result, key=lambda x: x["dr"], reverse=True)

        def _parse_lost_bl(items: list) -> list[dict]:
            result = []
            for b in items:
                result.append({
                    "source": b.get("url_from_domain", b.get("domain_from", "")),
                    "dr":     int(b.get("domain_rating_source", 0)),
                    "target": "/" + b.get("url_to", "").split("/", 3)[-1] if "/" in b.get("url_to", "") else "/",
                    "type":   "nofollow" if b.get("nofollow") else "dofollow",
                    "reason": b.get("lost_reason", ""),
                })
            return result

        new_notable  = _parse_bl(bl_new_data.get("backlinks",  []))[:8]
        lost_backlinks = _parse_lost_bl(bl_lost_data.get("backlinks", []))[:5]

        # ── Dofollow ratio ─────────────────────────────────────────────────
        dofollow_count = sum(1 for b in new_notable if b["type"] == "dofollow")
        dofollow_pct   = round(dofollow_count / len(new_notable), 2) if new_notable else 0.74

        y, m = int(year_month[:4]), int(year_month[5:7])

        return {
            "period": {
                "current":  {"label": f"Tháng {m}/{y}"},
                "previous": {"label": f"Tháng {int(prev_ym[5:7])}/{int(prev_ym[:4])}"},
            },
            "domain_rating": {
                "current":  dr_cur,
                "previous": dr_prev,
                "history":  [],
            },
            "referring_domains": {
                "current":        rd_cur,
                "previous":       rd_prev,
                "new_this_month": rd_new_count,
                "lost_this_month": rd_lost_count,
                "net_change":     rd_new_count - rd_lost_count,
            },
            "backlinks": {
                "total":            bl_cur,
                "total_previous":   bl_prev,
                "new_this_month":   bl_new_count,
                "lost_this_month":  bl_lost_count,
                "dofollow_pct":     dofollow_pct,
                "nofollow_pct":     round(1 - dofollow_pct, 2),
            },
            "new_notable_backlinks": new_notable,
            "lost_backlinks":        lost_backlinks,
        }
