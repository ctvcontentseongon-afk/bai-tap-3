# SEONGON Claude Workspace

Workspace cá nhân dành cho **Trưởng phòng Quản lý Dự án SEO tại SEONGON Agency**, tích hợp 3 Claude skills phục vụ công việc SEO thực tế hàng ngày.

## 3 Skills

| Skill | Mục đích | Kết nối ngoài | Output |
|-------|----------|---------------|--------|
| `project-status-tracker` | Đọc Google Sheets → sinh weekly status report | Google Sheets API | `.md` |
| `gsc-insights` | Phân tích GSC → tìm cơ hội SEO (quick wins, cannibalization...) | Google Search Console API | `.xlsx` + `.md` |
| `client-report-monthly` | Tổng hợp GSC + GA4 + Ahrefs → báo cáo tháng cho client | GSC + GA4 + Ahrefs API | `.pptx` |

## Cấu trúc Folder

```
seongon-claude-workspace/
├── .claude/
│   └── skills/
│       ├── project-status-tracker/
│       │   ├── SKILL.md
│       │   ├── scripts/gsheet_reader.py
│       │   ├── templates/status_report_template.md
│       │   ├── references/sheet_schema.md
│       │   └── tests/sample_sheet_data.csv
│       │
│       ├── gsc-insights/
│       │   ├── SKILL.md
│       │   ├── scripts/gsc_analyzer.py
│       │   ├── references/quick_wins_logic.md
│       │   ├── references/ctr_benchmarks.md
│       │   └── tests/mock_gsc_current.csv
│       │       tests/mock_gsc_previous.csv
│       │
│       └── client-report-monthly/
│           ├── SKILL.md
│           ├── scripts/
│           │   ├── report_generator.py    ← Script chính
│           │   ├── fetch_gsc.py
│           │   ├── fetch_ga4.py
│           │   ├── fetch_ahrefs.py
│           │   └── create_template.py     ← Chạy 1 lần để tạo template
│           ├── templates/
│           │   ├── monthly_report_template.pptx
│           │   └── brand_assets/
│           │       ├── colors.json
│           │       └── fonts.txt
│           ├── references/metrics_glossary.md
│           └── tests/mock_data/
│               ├── mock_gsc.json
│               ├── mock_ga4.json
│               └── mock_ahrefs.json
│
├── outputs/          # File output (chỉ commit thư mục samples/)
│   └── samples/      # Output mẫu để demo
├── credentials/      # API keys, service accounts (KHÔNG commit — xem .gitignore)
├── .env.example      # Template biến môi trường
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- pip

> **Chưa có Python?** Cài bằng Homebrew: `brew install python@3.11`

## Setup

```bash
# 1. Clone repo
git clone https://github.com/<your-username>/seongon-claude-workspace.git
cd seongon-claude-workspace

# 2. Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# hoặc: .venv\Scripts\activate   # Windows

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Tạo file .env từ template
cp .env.example .env
# Mở .env và điền credentials (bước tiếp theo)
```

## Setup Credentials

### Skill 1: project-status-tracker (Google Sheets)

1. Vào [Google Cloud Console](https://console.cloud.google.com/) → Tạo project
2. Enable **Google Sheets API** và **Google Drive API**
3. Vào **IAM & Admin → Service Accounts** → Create service account
4. Tạo JSON key → Tải về → Đổi tên thành `service_account.json`
5. Copy vào `credentials/service_account.json`
6. Mở Google Sheet → Share → Thêm email service account (Viewer quyền)
7. Cập nhật `.env`:
   ```
   GOOGLE_SERVICE_ACCOUNT_PATH=credentials/service_account.json
   ```

### Skill 2: gsc-insights (Google Search Console)

1. Enable **Google Search Console API** trong cùng project Google Cloud
2. Vào **APIs & Services → Credentials** → Create **OAuth 2.0 Client ID**
   - Application type: **Desktop app**
3. Download JSON → Lưu thành `credentials/gsc_client_secrets.json`
4. Cập nhật `.env`:
   ```
   GSC_CLIENT_SECRETS_PATH=credentials/gsc_client_secrets.json
   GSC_TOKEN_PATH=credentials/gsc_token.json
   ```
5. Lần đầu chạy script sẽ mở browser để đăng nhập Google → token lưu tự động

### Skill 3: client-report-monthly

**GSC**: Dùng chung credentials với Skill 2

**GA4**:
1. Enable **Google Analytics Data API** trong Google Cloud
2. Vào GA4 Admin → Property Access Management → Thêm email service account
3. Lấy **Property ID** từ GA4 Admin (format: `123456789`)
4. Cập nhật `.env`:
   ```
   GA4_PROPERTY_ID=123456789
   GA4_SERVICE_ACCOUNT_PATH=credentials/service_account.json
   ```

**Ahrefs**:
1. Đăng nhập [app.ahrefs.com](https://app.ahrefs.com) → Settings → API
2. Generate API Key
3. Cập nhật `.env`:
   ```
   AHREFS_API_KEY=your_api_key_here
   ```

## Chạy Demo với Mock Data

Không cần credentials — chạy ngay với flag `--mock`:

### Skill 1: Weekly Status Report

```bash
cd .claude/skills/project-status-tracker
python3 scripts/gsheet_reader.py --mock --week current
# Output: ../../outputs/weekly_status_YYYY-WW.md
```

### Skill 2: GSC Insights

```bash
cd .claude/skills/gsc-insights
python3 scripts/gsc_analyzer.py --mock --domain example.com
# Output: ../../outputs/example_com_gsc_insights_YYYYMMDD.xlsx
#         ../../outputs/example_com_insights_summary.md
```

### Skill 3: Monthly Client Report

```bash
# Bước 1: Tạo template (chỉ cần làm 1 lần)
cd .claude/skills/client-report-monthly
python3 scripts/create_template.py

# Bước 2: Tạo report
python3 scripts/report_generator.py \
  --mock \
  --client "ABC Company" \
  --domain example.com \
  --month 2026-04
# Output: ../../outputs/ABC_Company_SEO_Report_2026-04.pptx
```

## Push lên GitHub

```bash
# 1. Khởi tạo git trong thư mục workspace
cd seongon-claude-workspace
git init

# 2. Stage tất cả (credentials/ và .env đã được .gitignore bảo vệ)
git add .

# 3. Verify không có file nhạy cảm
git status   # Kiểm tra không thấy credentials/ hay .env

# 4. Commit đầu tiên
git commit -m "feat: SEONGON Claude workspace with 3 SEO skills"

# 5. Tạo repo trên GitHub tại github.com/new
# 6. Connect và push
git remote add origin https://github.com/<username>/seongon-claude-workspace.git
git branch -M main
git push -u origin main
```

> **Lưu ý bảo mật:**
> - `credentials/` — KHÔNG bao giờ commit
> - `.env` — KHÔNG bao giờ commit  
> - Chỉ commit `.env.example` (không có giá trị thật)

## Tác giả

**SEONGON Agency** — SEO Project Management Team  
Email: ctvcontent.seongon@gmail.com
