# Quick Wins Logic — Chi tiết thuật toán

## Định nghĩa Quick Win

Một keyword là **Quick Win** khi đáp ứng đồng thời 3 điều kiện:

### Điều kiện 1: Position Range
```
5.0 ≤ avg_position ≤ 15.0
```
- Position 1-4: Đã rank tốt, optimize CTR vẫn tốt nhưng không phải quick win
- Position 5-15: "Low-hanging fruit" — một cải thiện nhỏ về title/meta có thể tăng đáng kể clicks
- Position > 15: Cần cải thiện ranking trước, chưa phải quick win

### Điều kiện 2: Minimum Impressions
```
impressions ≥ 100 (trong period 28 ngày)
```
- Đảm bảo keyword có đủ traffic tiềm năng
- Keywords dưới 100 impressions: quá nhỏ, tối ưu không có tác động đáng kể

### Điều kiện 3: CTR Gap
```
actual_ctr < benchmark_ctr[floor(avg_position)] × CTR_THRESHOLD
```
Với `CTR_THRESHOLD = 0.8` (tức là actual CTR thấp hơn 20% so với benchmark)

## Tính Opportunity Score

```python
opportunity_score = impressions × (benchmark_ctr - actual_ctr)
```

**Ý nghĩa:** Số clicks tiềm năng có thể tăng thêm nếu đạt benchmark CTR.

**Ví dụ:**
- Keyword "dịch vụ SEO Hà Nội", position 8.2, impressions 450, actual CTR 2.1%
- Benchmark CTR position 8: 3.8%
- CTR gap: 3.8% - 2.1% = 1.7%
- Opportunity score: 450 × 0.017 = **7.65 clicks/tháng tiềm năng**

## Sắp xếp kết quả

Quick wins được sort theo `opportunity_score` **giảm dần** — keyword có potential gain cao nhất ở đầu danh sách.

## Action Items cho Quick Wins

Khi đã có danh sách quick wins, các action cụ thể:

| Priority | Action | Impact |
|----------|--------|--------|
| 1 | Rewrite title tag theo format: [Benefit] + [Keyword] + [Brand] | CTR +15-30% |
| 2 | Thêm số liệu cụ thể vào title (năm, %, số lượng) | CTR +10-20% |
| 3 | Thêm meta description có CTA rõ ràng | CTR +5-15% |
| 4 | Implement FAQ structured data | CTR +20-40% (nếu trigger) |
| 5 | A/B test title tag (dùng Search Console Experiment) | Data-driven |

## Lưu ý quan trọng

- Quick wins **không cần** cải thiện content hay backlink
- Chỉ cần tối ưu **on-page metadata** (title, meta desc, structured data)
- Kết quả thường thấy trong 2-4 tuần sau khi Google crawl lại
- Luôn track trước/sau bằng GSC để đo impact thực tế
