# Google Sheet Schema — SEO Task Tracker

## Tên worksheet mặc định: `Tasks`

## Cấu trúc cột (theo thứ tự) — khớp với format SEONGON thực tế

| Cột | Tên | Kiểu dữ liệu | Bắt buộc | Mô tả | Ví dụ |
|-----|-----|--------------|----------|-------|-------|
| A | `Công việc` | Text | Có | Mô tả task, có thể có link | "Audit technical SEO toàn site" |
| B | `Phụ trách` | Text | Có | Tên client / project | "Viettel" |
| C | `PIC` | Text | Có | Người thực hiện (Person In Charge) | "Hương" |
| D | `Deadline` | Date (DD/MM/YYYY) | Có | Ngày deadline | "20/05/2026" |
| E | `Tình trạng` | Enum | Có | Trạng thái hiện tại | "Đang triển khai" |
| F | `Ghi chú` | Text | Không | Ghi chú thêm | "Chờ brief từ client" |

## Giá trị hợp lệ cho cột `Tình trạng`

| Giá trị | Ý nghĩa | Hiển thị trong báo cáo |
|---------|---------|------------------------|
| `Đang triển khai` | Đang làm | 🟡 Đang triển khai |
| `Chưa bắt đầu` | Chưa bắt đầu | ⚪ Chưa bắt đầu |
| `Hoàn thành` | Hoàn thành | 🟢 Hoàn thành |
| `Bị block` | Đang bị block | 🔴 Bị block |

## Quy tắc phân loại task (logic giữ nguyên)

1. **Bị block**: Tình trạng == "Bị block" (ưu tiên cao nhất, bất kể deadline)
2. **Quá hạn**: Deadline < hôm nay AND Tình trạng != "Hoàn thành"
3. **Sắp hết hạn**: 0 ≤ (Deadline - hôm nay) ≤ 3 ngày AND Tình trạng != "Hoàn thành" AND != "Bị block"
4. **Hoàn thành tuần này**: Tình trạng == "Hoàn thành" AND đánh dấu done trong 7 ngày qua
5. **Đang thực hiện**: Tất cả còn lại

> **Lưu ý:** Deadline trong sheet dùng định dạng DD/MM/YYYY (theo chuẩn Việt Nam).

## Ví dụ dữ liệu hợp lệ

```
Công việc,Phụ trách,PIC,Deadline,Tình trạng,Ghi chú
Cấp quyền admin website,Viettel,Hương,15/05/2026,Đang triển khai,Chờ IT client
Share GA4 cho SEONGON,Viettel,Anh Việt,13/05/2026,Hoàn thành,
Duyệt content plan Samsung,Samsung,Hương,19/05/2026,Bị block,Chờ approval từ client
```

## Lưu ý khi setup Google Sheet

- Hàng đầu tiên phải là header (tên cột chính xác như bảng trên)
- Định dạng date: `DD/MM/YYYY` (chuẩn Việt Nam)
- Share sheet với email service account (quyền Viewer là đủ)
