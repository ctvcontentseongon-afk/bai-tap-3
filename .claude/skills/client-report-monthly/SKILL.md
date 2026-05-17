---
name: client-report-monthly
description: Dùng skill này khi cần tạo báo cáo SEO tháng cho client dạng PowerPoint (.pptx). Tích hợp dữ liệu từ GSC, GA4, và Ahrefs vào template 7 slides với brand SEONGON.
---

# Client Monthly SEO Report Generator

## Mục đích

Tự động tạo báo cáo SEO định kỳ hàng tháng dạng `.pptx` cho client bằng cách:
- Pull data từ **Google Search Console** (clicks, impressions, top queries)
- Pull data từ **Google Analytics 4** (organic sessions, conversions, landing pages)
- Pull data từ **Ahrefs** (Domain Rating, referring domains, new backlinks)
- Inject vào template PowerPoint 7 slides với brand SEONGON

## Khi nào dùng skill này

- "Tạo báo cáo tháng 4 cho client ABC"
- "Generate monthly report cho example.com"
- "Tạo SEO report tháng 2026-04 cho [client name]"
- "Xuất PowerPoint báo cáo SEO tháng"

## Cách sử dụng

**Chạy demo với mock data:**
```bash
cd .claude/skills/client-report-monthly
python scripts/report_generator.py --mock --client "ABC Company" --domain example.com --month 2026-04
```

**Chạy với data thật:**
```bash
python scripts/report_generator.py \
  --client "ABC Company" \
  --domain example.com \
  --month 2026-04 \
  --ga4-property 123456789
```

## Input

| Tham số | Bắt buộc | Mô tả | Ví dụ |
|---------|----------|-------|-------|
| `--client` | Có | Tên client | `"ABC Company"` |
| `--domain` | Có | Domain client | `example.com` |
| `--month` | Có | Tháng báo cáo | `2026-04` |
| `--ga4-property` | Không | GA4 Property ID | `123456789` |
| `--mock` | Không | Dùng mock data | (flag) |
| `--output-dir` | Không | Thư mục lưu output | `outputs/` |
| `--template` | Không | Path template .pptx | `templates/monthly_report_template.pptx` |

## Output

`outputs/[ClientName]_SEO_Report_YYYY-MM.pptx` với 7 slides:
1. **Cover** — Tên client, tháng báo cáo, logo SEONGON
2. **Executive Summary** — KPIs chính, highlights, tóm tắt
3. **Organic Traffic (GA4)** — Sessions, users, conversions, trend
4. **GSC Performance** — Clicks, impressions, CTR, avg position
5. **Top Performing Pages** — Top 10 pages by organic traffic
6. **Backlinks Growth (Ahrefs)** — DR, referring domains, new backlinks
7. **Next Month Action Plan** — 5 ưu tiên tháng tới

## Dependencies

**Thư viện Python:**
```
python-pptx>=0.6.23
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
pandas>=2.1.0
requests>=2.31.0
python-dotenv>=1.0.0
```

**Credentials cần có:**
- `credentials/service_account.json` — Google service account (GSC + GA4)
- `credentials/gsc_client_secrets.json` — OAuth cho GSC (nếu không dùng service account)
- `AHREFS_API_KEY` trong `.env` — Ahrefs API key

## Files trong skill này

| File | Vai trò |
|------|---------|
| `SKILL.md` | Mô tả skill này |
| `scripts/report_generator.py` | Script chính: orchestrate toàn bộ flow |
| `scripts/fetch_gsc.py` | GSC data fetcher |
| `scripts/fetch_ga4.py` | GA4 data fetcher |
| `scripts/fetch_ahrefs.py` | Ahrefs data fetcher |
| `scripts/create_template.py` | Script tạo template .pptx lần đầu |
| `templates/monthly_report_template.pptx` | Template PowerPoint (tạo bằng create_template.py) |
| `templates/brand_assets/colors.json` | Brand colors SEONGON |
| `templates/brand_assets/fonts.txt` | Brand fonts list |
| `references/metrics_glossary.md` | Định nghĩa các chỉ số SEO |
| `tests/mock_data/` | Mock data cho cả 3 nguồn |

## Ví dụ

**Ví dụ 1 — Demo với mock data:**
```bash
python scripts/report_generator.py \
  --mock \
  --client "XYZ Corporation" \
  --domain xyz.com \
  --month 2026-04
# Output: outputs/XYZ_Corporation_SEO_Report_2026-04.pptx
```

**Ví dụ 2 — Report thật tháng trước:**
```bash
python scripts/report_generator.py \
  --client "ABC Brand" \
  --domain abcbrand.vn \
  --month 2026-04 \
  --ga4-property 987654321
# Output: outputs/ABC_Brand_SEO_Report_2026-04.pptx
```
