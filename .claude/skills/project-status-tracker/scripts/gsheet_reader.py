"""
gsheet_reader.py — Đọc Google Sheets và sinh weekly status report.

Usage:
    python gsheet_reader.py --mock --week current
    python gsheet_reader.py --sheet-id <ID> --week 2026-W20
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

SKILL_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = SKILL_DIR.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

load_dotenv(WORKSPACE_ROOT / ".env")

OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
TEMPLATE_DIR = SKILL_DIR / "templates"
TESTS_DIR = SKILL_DIR / "tests"

# Tên cột theo format SEONGON thực tế
COL_TASK = "Công việc"
COL_CLIENT = "Phụ trách"
COL_PIC = "PIC"
COL_DEADLINE = "Deadline"
COL_STATUS = "Tình trạng"
COL_NOTES = "Ghi chú"

# Giá trị status (tiếng Việt)
STATUS_BLOCKED = "Bị block"
STATUS_DONE = "Hoàn thành"


# ---------------------------------------------------------------------------
# Google Sheets connector
# ---------------------------------------------------------------------------

class GSheetReader:
    """Kết nối Google Sheets qua service account và đọc dữ liệu."""

    def __init__(self, credentials_path: str | None = None) -> None:
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")

    def read_sheet(self, sheet_id: str, worksheet_name: str = "Tasks") -> pd.DataFrame:
        """Đọc worksheet từ Google Sheet và trả về DataFrame."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise ImportError("Cài gspread: pip install gspread google-auth")

        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df.fillna("")


def load_mock_data() -> pd.DataFrame:
    """Đọc mock data từ CSV để test không cần Google Sheets."""
    csv_path = TESTS_DIR / "sample_sheet_data.csv"
    df = pd.read_csv(csv_path)
    return df.fillna("")


def parse_deadline(deadline_str: str) -> date | None:
    """Parse deadline từ DD/MM/YYYY hoặc YYYY-MM-DD."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(deadline_str).strip(), fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Task classification
# ---------------------------------------------------------------------------

def get_week_string(week_arg: str) -> str:
    """Chuyển 'current' hoặc '2026-W20' thành chuỗi 'YYYY-WW'."""
    if week_arg == "current":
        today = date.today()
        return f"{today.year}-{today.isocalendar()[1]:02d}"
    return week_arg.replace("W", "").replace("-", "-", 1)


def classify_tasks(df: pd.DataFrame) -> dict[str, list[dict]]:
    """
    Phân loại task thành 5 nhóm dựa trên Tình trạng và Deadline.

    Thứ tự ưu tiên: Bị block > Quá hạn > Sắp hết hạn > Hoàn thành > Đang làm
    """
    today = date.today()
    week_ago = today - timedelta(days=7)

    blockers: list[dict] = []
    overdue: list[dict] = []
    due_soon: list[dict] = []
    completed: list[dict] = []
    on_track: list[dict] = []

    for _, row in df.iterrows():
        task = row.to_dict()
        status = str(task.get(COL_STATUS, "")).strip()
        deadline = parse_deadline(task.get(COL_DEADLINE, ""))

        if status == STATUS_BLOCKED:
            blockers.append(task)
        elif deadline and status != STATUS_DONE and deadline < today:
            task["days_overdue"] = (today - deadline).days
            overdue.append(task)
        elif deadline and status == STATUS_DONE and deadline >= week_ago:
            completed.append(task)
        elif deadline and status != STATUS_DONE and 0 <= (deadline - today).days <= 3:
            task["days_left"] = (deadline - today).days
            due_soon.append(task)
        else:
            on_track.append(task)

    return {
        "blockers": blockers,
        "overdue": overdue,
        "due_soon": due_soon,
        "completed": completed,
        "on_track": on_track,
    }


def build_project_summary(df: pd.DataFrame, classified: dict) -> dict[str, dict]:
    """Tổng hợp thống kê theo client (Phụ trách)."""
    projects: dict[str, dict] = {}
    for _, row in df.iterrows():
        proj = str(row.get(COL_CLIENT, "Unknown")).strip() or "Unknown"
        if proj not in projects:
            projects[proj] = {"total": 0, "done": 0, "blocked": 0, "overdue": 0}
        projects[proj]["total"] += 1
        status = str(row.get(COL_STATUS, "")).strip()
        if status == STATUS_DONE:
            projects[proj]["done"] += 1
        elif status == STATUS_BLOCKED:
            projects[proj]["blocked"] += 1
    for task in classified["overdue"]:
        proj = str(task.get(COL_CLIENT, "Unknown")).strip() or "Unknown"
        if proj in projects:
            projects[proj]["overdue"] += 1
    return dict(sorted(projects.items()))


def build_owner_summary(df: pd.DataFrame, classified: dict) -> dict[str, dict]:
    """Tổng hợp thống kê theo PIC."""
    owners: dict[str, dict] = {}
    for _, row in df.iterrows():
        owner = str(row.get(COL_PIC, "Unknown")).strip() or "Unknown"
        if owner not in owners:
            owners[owner] = {"total": 0, "done": 0, "blocked": 0, "overdue": 0}
        owners[owner]["total"] += 1
        status = str(row.get(COL_STATUS, "")).strip()
        if status == STATUS_DONE:
            owners[owner]["done"] += 1
        elif status == STATUS_BLOCKED:
            owners[owner]["blocked"] += 1
    for task in classified["overdue"]:
        owner = str(task.get(COL_PIC, "Unknown")).strip() or "Unknown"
        if owner in owners:
            owners[owner]["overdue"] += 1
    return dict(sorted(owners.items()))


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    classified: dict,
    by_project: dict,
    by_owner: dict,
    week_str: str,
    total_tasks: int,
) -> str:
    """Render Jinja2 template với dữ liệu đã phân loại."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("status_report_template.md")

    context: dict[str, Any] = {
        "week": week_str,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total_tasks": total_tasks,
        "by_project": by_project,
        "by_owner": by_owner,
        **classified,
    }
    return template.render(**context)


def save_report(content: str, output_path: Path) -> None:
    """Lưu nội dung báo cáo ra file Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"✅ Báo cáo đã được lưu: {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sinh weekly status report từ Google Sheets hoặc mock data."
    )
    parser.add_argument("--sheet-id", help="Google Sheet ID")
    parser.add_argument("--worksheet", default="Tasks", help="Tên worksheet (mặc định: Tasks)")
    parser.add_argument(
        "--week",
        default="current",
        help="Tuần cần báo cáo: 'current' hoặc '2026-W20'",
    )
    parser.add_argument("--mock", action="store_true", help="Dùng mock data thay vì Google Sheets")
    parser.add_argument("--output", help="Đường dẫn file output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.mock:
        print("🔧 Chế độ mock: đang đọc sample_sheet_data.csv...")
        df = load_mock_data()
    else:
        if not args.sheet_id:
            print("❌ Lỗi: cần --sheet-id hoặc --mock")
            sys.exit(1)
        print(f"📊 Đang kết nối Google Sheets: {args.sheet_id}...")
        reader = GSheetReader()
        df = reader.read_sheet(args.sheet_id, args.worksheet)

    print(f"   Đọc được {len(df)} tasks")

    week_str = get_week_string(args.week)
    classified = classify_tasks(df)
    by_project = build_project_summary(df, classified)
    by_owner = build_owner_summary(df, classified)

    print(f"\n📋 Phân loại tuần {week_str}:")
    print(f"   🔴 Bị block:     {len(classified['blockers'])}")
    print(f"   ⚠️  Quá hạn:      {len(classified['overdue'])}")
    print(f"   🟡 Sắp hết hạn:  {len(classified['due_soon'])}")
    print(f"   🟢 Hoàn thành:   {len(classified['completed'])}")
    print(f"   ⚪ Đang làm:     {len(classified['on_track'])}")

    content = generate_report(classified, by_project, by_owner, week_str, len(df))

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = OUTPUTS_DIR / f"weekly_status_{week_str}.md"

    save_report(content, output_path)


if __name__ == "__main__":
    main()
