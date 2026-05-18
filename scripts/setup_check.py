"""setup_check.py — Kiểm tra toàn bộ credentials và dependencies.

Chạy lệnh này trước khi dùng live API lần đầu:
    python scripts/setup_check.py
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

WORKSPACE = Path(__file__).resolve().parent.parent
SKILL_DIR = WORKSPACE / ".claude" / "skills" / "client-report-monthly"

BOLD  = "\033[1m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

ok   = lambda s: print(f"  {GREEN}✅ {s}{RESET}")
warn = lambda s: print(f"  {YELLOW}⚠️  {s}{RESET}")
err  = lambda s: print(f"  {RED}❌ {s}{RESET}")
hdr  = lambda s: print(f"\n{BOLD}{s}{RESET}")


def check_python():
    hdr("1. Python version")
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        err(f"Python {v.major}.{v.minor} — cần Python ≥ 3.10")


def check_packages():
    hdr("2. Python packages")
    required = {
        "dotenv":                   "python-dotenv",
        "pptx":                     "python-pptx",
        "requests":                 "requests",
        "google.auth":              "google-auth",
        "googleapiclient":          "google-api-python-client",
        "google_auth_oauthlib":     "google-auth-oauthlib",
        "google.analytics.data_v1beta": "google-analytics-data",
        "gspread":                  "gspread",
        "pandas":                   "pandas",
        "openpyxl":                 "openpyxl",
        "jinja2":                   "jinja2",
    }
    missing = []
    for mod, pkg in required.items():
        try:
            importlib.import_module(mod)
            ok(pkg)
        except ImportError:
            err(f"{pkg}  →  pip install {pkg}")
            missing.append(pkg)
    if missing:
        print(f"\n  Chạy: pip install {' '.join(missing)}")


def check_env():
    hdr("3. Biến môi trường (.env)")
    vars_ = {
        "AHREFS_API_KEY":          ("required", "ahrefs.com → Settings → API"),
        "GA4_PROPERTY_ID":         ("required", "GA4 Admin → Property Settings → Property ID"),
        "GA4_SERVICE_ACCOUNT_PATH":("optional", "Path tới service_account.json"),
        "GSC_CLIENT_SECRETS_PATH": ("optional", "Path tới gsc_client_secrets.json"),
        "GSC_TOKEN_PATH":          ("optional", "Path lưu OAuth token GSC"),
        "GSC_SITE_URL":            ("optional", "sc-domain:yourdomain.com"),
    }
    for var, (level, hint) in vars_.items():
        val = os.getenv(var)
        if val:
            display = val[:20] + "..." if len(val) > 20 else val
            ok(f"{var} = {display}")
        elif level == "required":
            err(f"{var} chưa set  →  {hint}")
        else:
            warn(f"{var} chưa set (tùy chọn)  →  {hint}")


def check_credentials():
    hdr("4. Credential files")

    files = {
        os.getenv("GA4_SERVICE_ACCOUNT_PATH", "credentials/service_account.json"): {
            "label": "GA4 Service Account JSON",
            "guide": (
                "Google Cloud Console → IAM & Admin → Service Accounts → Create\n"
                "    → Enable 'Google Analytics Data API'\n"
                "    → Keys → Add Key → JSON → Download\n"
                "    → GA4 Admin → Property Access Management → Add email (Viewer)\n"
                f"    → Lưu vào credentials/service_account.json"
            ),
        },
        os.getenv("GSC_CLIENT_SECRETS_PATH", "credentials/gsc_client_secrets.json"): {
            "label": "GSC OAuth 2.0 Client Secrets JSON",
            "guide": (
                "Google Cloud Console → APIs & Services → Credentials\n"
                "    → Create Credentials → OAuth 2.0 Client ID → Desktop App\n"
                "    → Enable 'Google Search Console API'\n"
                "    → Download JSON\n"
                f"    → Lưu vào credentials/gsc_client_secrets.json"
            ),
        },
    }

    for path_str, info in files.items():
        p = Path(path_str)
        if not p.is_absolute():
            p = WORKSPACE / p
        if p.exists():
            size = p.stat().st_size
            if size > 50:
                ok(f"{info['label']}: {p.name} ({size} bytes)")
            else:
                warn(f"{info['label']}: {p.name} có vẻ trống ({size} bytes)")
        else:
            err(f"{info['label']}: không tìm thấy {p.relative_to(WORKSPACE)}")
            for line in info["guide"].splitlines():
                print(f"    {line}")
            print()

    # GSC token (optional — tạo tự động khi chạy lần đầu)
    token_path = Path(os.getenv("GSC_TOKEN_PATH", "credentials/gsc_token.json"))
    if not token_path.is_absolute():
        token_path = WORKSPACE / token_path
    if token_path.exists():
        ok(f"GSC OAuth token: {token_path.name} (đã login trước đó)")
    else:
        warn(f"GSC OAuth token: chưa có — sẽ tự tạo khi chạy lần đầu (mở browser)")


def check_mock_data():
    hdr("5. Mock data files")
    mock_dir = SKILL_DIR / "tests" / "mock_data"
    for f in ["mock_gsc.json", "mock_ga4.json", "mock_ahrefs.json",
              "mock_comparison.json", "mock_actions.json"]:
        p = mock_dir / f
        if p.exists():
            ok(f"{f}")
        else:
            err(f"{f} — bị thiếu, chạy demo sẽ lỗi")


def check_brand_profiles():
    hdr("6. Brand profiles")
    bp_dir = SKILL_DIR / "brand_profiles"
    profiles = list(bp_dir.glob("*.json")) if bp_dir.exists() else []
    if profiles:
        for p in profiles:
            ok(f"{p.stem}")
    else:
        warn("Không tìm thấy brand profile nào. Sẽ dùng 'default'.")


def print_usage():
    hdr("7. Cách chạy")
    print(f"""
  {BOLD}MOCK (không cần credentials):{RESET}
    python .claude/skills/client-report-monthly/scripts/report_generator.py \\
        --client "Tên Client" --domain example.com \\
        --month 2026-05 --brand default --mock

  {BOLD}LIVE API (cần hoàn thành setup ở trên):{RESET}
    python .claude/skills/client-report-monthly/scripts/report_generator.py \\
        --client "Tên Client" --domain example.com \\
        --month 2026-05 --brand default \\
        --ga4-property 123456789

  {BOLD}Kiểm tra credentials nhanh:{RESET}
    python .claude/skills/client-report-monthly/scripts/report_generator.py \\
        --client x --domain x --month 2026-05 --check-creds
""")


def main():
    print(f"\n{BOLD}{'='*60}")
    print("  SEONGON Workspace — Setup Credential Check")
    print(f"{'='*60}{RESET}")

    check_python()
    check_packages()
    check_env()
    check_credentials()
    check_mock_data()
    check_brand_profiles()
    print_usage()

    print(f"{BOLD}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
