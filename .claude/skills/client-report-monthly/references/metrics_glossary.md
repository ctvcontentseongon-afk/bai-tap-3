# Metrics Glossary — SEO Monthly Report

## Google Search Console (GSC)

| Chỉ số | Tiếng Việt | Định nghĩa |
|--------|-----------|-----------|
| **Clicks** | Lượt nhấp | Số lần người dùng click vào kết quả tìm kiếm organic |
| **Impressions** | Lượt hiển thị | Số lần URL xuất hiện trong kết quả tìm kiếm (dù người dùng có thấy hay không) |
| **CTR** | Tỷ lệ click | Clicks ÷ Impressions × 100. Đo hiệu quả của title/meta trong SERP |
| **Average Position** | Vị trí trung bình | Vị trí trung bình của URL trong kết quả tìm kiếm (1 = cao nhất) |
| **Top Queries** | Từ khóa hàng đầu | Các từ khóa mang lại nhiều clicks nhất |
| **Top Pages** | Trang hàng đầu | Các URL mang lại nhiều clicks nhất |

## Google Analytics 4 (GA4)

| Chỉ số | Tiếng Việt | Định nghĩa |
|--------|-----------|-----------|
| **Organic Sessions** | Phiên organic | Số phiên truy cập đến từ kết quả tìm kiếm tự nhiên (không trả phí) |
| **Users** | Người dùng | Số người dùng unique truy cập website trong kỳ |
| **New Users** | Người dùng mới | Người dùng lần đầu truy cập trong kỳ |
| **Bounce Rate** | Tỷ lệ thoát | % phiên chỉ xem 1 trang rồi rời đi (GA4 dùng "Engaged Sessions" thay thế) |
| **Engagement Rate** | Tỷ lệ tương tác | % phiên có tương tác (xem > 1 trang, hoặc > 10 giây, hoặc có conversion event) |
| **Conversions** | Chuyển đổi | Số lần người dùng thực hiện hành động mục tiêu (liên hệ, mua hàng, đăng ký...) |
| **Conversion Rate** | Tỷ lệ chuyển đổi | Conversions ÷ Sessions × 100 |
| **Top Landing Pages** | Trang đích hàng đầu | Các trang người dùng organic truy cập đầu tiên |

## Ahrefs

| Chỉ số | Tiếng Việt | Định nghĩa |
|--------|-----------|-----------|
| **Domain Rating (DR)** | Chỉ số domain | Thang điểm 0-100 đánh giá sức mạnh backlink profile của domain. DR càng cao càng tốt |
| **URL Rating (UR)** | Chỉ số URL | Sức mạnh backlink của 1 URL cụ thể, thang 0-100 |
| **Referring Domains** | Domain liên kết | Số domain độc lập có ít nhất 1 backlink trỏ về site |
| **Backlinks** | Liên kết ngược | Tổng số backlink (nhiều backlinks từ 1 domain = 1 referring domain) |
| **New Backlinks** | Backlink mới | Backlinks xuất hiện lần đầu trong kỳ |
| **Lost Backlinks** | Backlink mất | Backlinks biến mất trong kỳ |
| **Organic Keywords** | Từ khóa organic | Số từ khóa domain rank trong top 100 |
| **Organic Traffic** | Traffic ước tính | Lượng traffic organic ước tính theo Ahrefs (không chính xác bằng GSC) |

## KPIs cần theo dõi hàng tháng

### KPIs Primary (báo cáo cho client)
1. Organic Sessions (GA4) — MoM growth
2. Organic Conversions (GA4) — số lượng và rate
3. Clicks (GSC) — MoM growth
4. Top Ranked Keywords — số keywords trong top 3, top 10

### KPIs Secondary (context cho team SEO)
5. Average Position (GSC) — xu hướng
6. CTR (GSC) — hiệu quả metadata
7. Domain Rating (Ahrefs) — tăng trưởng DR
8. New Referring Domains — tăng trưởng backlink profile

## Cách đọc MoM (Month-over-Month)

```
MoM Growth = (Giá trị tháng này - Giá trị tháng trước) / Giá trị tháng trước × 100%
```

- **+10% trở lên**: Tốt, thể hiện tăng trưởng tích cực
- **-5% đến +10%**: Ổn định, không có vấn đề lớn  
- **-5% trở xuống**: Cần điều tra nguyên nhân
