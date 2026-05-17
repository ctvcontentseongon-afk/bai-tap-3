---
name: project-status-tracker
description: Dùng skill này khi người dùng muốn xem tiến độ dự án SEO tuần này, tạo weekly status report, kiểm tra task nào đang bị blocked/overdue, hoặc tổng hợp tình trạng công việc của team từ Google Sheets.
---

# Project Status Tracker

## Mục đích

Đọc Google Sheets quản lý dự án của team SEO và sinh báo cáo tiến độ tuần dạng Markdown. Báo cáo phân loại task theo trạng thái, highlight blockers, nhóm theo Project và Owner.

## Khi nào dùng skill này

- "Tạo báo cáo tiến độ tuần này"
- "Weekly status report cho team SEO"
- "Xem task nào đang bị blocked / overdue"
- "Tổng hợp tiến độ dự án [tên project]"
- "Cập nhật tình hình công việc tuần W20"
- "Có task nào sắp deadline không?"

## Cách sử dụng

**Bước 1:** Đảm bảo đã setup Google Sheets service account (xem README.md gốc)

**Bước 2:** Chạy script:
```bash
cd .claude/skills/project-status-tracker
python scripts/gsheet_reader.py --sheet-id <SHEET_ID> --week current
```

**Chạy demo với mock data (không cần credentials):**
```bash
python scripts/gsheet_reader.py --mock --week current
```

**Bước 3:** Mở file output tại `outputs/weekly_status_YYYY-WW.md`

## Input

| Tham số | Bắt buộc | Mô tả | Ví dụ |
|---------|----------|-------|-------|
| `--sheet-id` | Có (nếu không `--mock`) | ID Google Sheet (lấy từ URL) | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms` |
| `--week` | Không | Tuần cần báo cáo | `current`, `2026-W20` |
| `--worksheet` | Không | Tên worksheet | `Tasks` (mặc định) |
| `--mock` | Không | Dùng mock data thay vì API | (flag) |
| `--output` | Không | Đường dẫn file output | `outputs/my_report.md` |

## Output

File Markdown tại `outputs/weekly_status_YYYY-WW.md` với cấu trúc:
- Blockers (highlight đầu tiên)
- Overdue tasks
- Due Soon (≤3 ngày)
- Completed This Week
- On-track
- Summary by Project
- Summary by Owner

## Dependencies

**Thư viện Python:**
```
gspread>=5.12.0
google-auth>=2.23.0
pandas>=2.1.0
jinja2>=3.1.2
python-dotenv>=1.0.0
```

**Credentials cần có:**
- `credentials/service_account.json` — Google service account key
- Google Sheet phải được share với email service account

## Files trong skill này

| File | Vai trò |
|------|---------|
| `SKILL.md` | Mô tả skill này |
| `scripts/gsheet_reader.py` | Script chính: kết nối Sheets, phân loại task, sinh report |
| `templates/status_report_template.md` | Jinja2 template cho báo cáo |
| `references/sheet_schema.md` | Định nghĩa cấu trúc Google Sheet |
| `tests/sample_sheet_data.csv` | Mock data để test không cần API |

## Ví dụ

**Ví dụ 1 — Báo cáo tuần hiện tại với mock data:**
```bash
python scripts/gsheet_reader.py --mock --week current
# Output: outputs/weekly_status_2026-20.md
```

**Ví dụ 2 — Báo cáo tuần cụ thể từ Google Sheets thật:**
```bash
python scripts/gsheet_reader.py \
  --sheet-id 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms \
  --week 2026-W19 \
  --worksheet "SEO Tasks"
# Output: outputs/weekly_status_2026-19.md
```
