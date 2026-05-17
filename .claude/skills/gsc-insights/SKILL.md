---
name: gsc-insights
description: Dùng skill này khi người dùng muốn phân tích Google Search Console để tìm quick wins, từ khóa bị cannibalization, keywords đang tụt hạng, hoặc cơ hội từ khóa mới nổi. Output là file Excel 4 sheets và báo cáo tóm tắt.
---

# GSC Insights Analyzer

## Mục đích

Kết nối Google Search Console API, pull data clicks/impressions/CTR/position, và tự động phân tích 4 loại cơ hội SEO:
1. **Quick Wins** — Keywords rank 5-15 có thể tăng CTR ngay
2. **Cannibalization** — Nhiều URL cùng rank cho 1 keyword
3. **Declining Queries** — Keywords đang tụt hạng
4. **Rising Opportunities** — Keywords mới nổi lên top 50

## Khi nào dùng skill này

- "Tìm quick wins cho domain example.com"
- "Phân tích GSC tháng này"
- "Keyword nào đang bị cannibalization?"
- "Có keyword nào tụt hạng mạnh không?"
- "Cơ hội SEO nào đang nổi lên?"
- "Tạo báo cáo GSC insights cho [domain]"

## Cách sử dụng

**Chạy demo với mock data:**
```bash
cd .claude/skills/gsc-insights
python scripts/gsc_analyzer.py --mock --domain example.com
```

**Chạy với Google Search Console thật:**
```bash
python scripts/gsc_analyzer.py \
  --domain example.com \
  --start-date 2026-04-01 \
  --end-date 2026-04-30
```

**Chỉ phân tích 1 loại:**
```bash
python scripts/gsc_analyzer.py --mock --domain example.com --analysis quick_wins
```

## Input

| Tham số | Bắt buộc | Mô tả | Ví dụ |
|---------|----------|-------|-------|
| `--domain` | Có | Domain cần phân tích | `example.com` |
| `--start-date` | Không | Ngày bắt đầu (mặc định: 28 ngày trước) | `2026-04-01` |
| `--end-date` | Không | Ngày kết thúc (mặc định: hôm qua) | `2026-04-30` |
| `--analysis` | Không | Loại phân tích cụ thể | `quick_wins`, `cannibalization`, `declining`, `rising`, `all` |
| `--mock` | Không | Dùng mock data | (flag) |
| `--output-dir` | Không | Thư mục lưu output | `outputs/` |

## Output

1. `outputs/[domain]_gsc_insights_YYYYMMDD.xlsx` — File Excel với 4 sheets:
   - **Quick Wins**: query, page, position, impressions, actual_ctr, benchmark_ctr, opportunity_score
   - **Cannibalization**: query, url_1, url_2, position_1, position_2
   - **Declining**: query, position_current, position_previous, position_drop
   - **Rising**: query, position_current, impressions_current, new_in_period

2. `outputs/[domain]_insights_summary.md` — Top 10 actions ưu tiên

## Dependencies

**Thư viện Python:**
```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
pandas>=2.1.0
openpyxl>=3.1.2
python-dotenv>=1.0.0
```

**Credentials cần có:**
- `credentials/gsc_client_secrets.json` — OAuth 2.0 Desktop app client
- Lần đầu chạy sẽ mở browser để xác thực

## Files trong skill này

| File | Vai trò |
|------|---------|
| `SKILL.md` | Mô tả skill này |
| `scripts/gsc_analyzer.py` | Script chính: kết nối GSC + 4 hàm phân tích + xuất xlsx |
| `references/quick_wins_logic.md` | Quy tắc chi tiết lọc quick wins |
| `references/ctr_benchmarks.md` | Bảng benchmark CTR theo position |
| `tests/mock_gsc_current.csv` | Mock data kỳ hiện tại |
| `tests/mock_gsc_previous.csv` | Mock data kỳ trước (để so sánh) |

## Ví dụ

**Ví dụ 1 — Full analysis với mock data:**
```bash
python scripts/gsc_analyzer.py --mock --domain seongon.com
# Output:
#   outputs/seongon.com_gsc_insights_20260518.xlsx  (4 sheets)
#   outputs/seongon.com_insights_summary.md
```

**Ví dụ 2 — Chỉ tìm quick wins từ GSC thật:**
```bash
python scripts/gsc_analyzer.py \
  --domain seongon.com \
  --analysis quick_wins \
  --start-date 2026-04-19 \
  --end-date 2026-05-16
```
