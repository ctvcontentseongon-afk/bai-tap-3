# BÁO CÁO TIẾN ĐỘ TUẦN {{ week }}

> 📅 Ngày tạo: {{ generated_at }} | Tổng số tasks: {{ total_tasks }}

---
{% if blockers %}
## 🔴 BỊ BLOCK — CẦN XỬ LÝ NGAY ({{ blockers|length }} tasks)

| STT | Công việc | Phụ trách | PIC | Deadline | Ghi chú |
|-----|-----------|-----------|-----|----------|---------|
{% for task in blockers %}| {{ loop.index }} | {{ task['Công việc'] }} | {{ task['Phụ trách'] }} | {{ task['PIC'] }} | {{ task['Deadline'] }} | {{ task['Ghi chú'] }} |
{% endfor %}

---
{% endif %}
{% if overdue %}
## ⚠️ QUÁ HẠN ({{ overdue|length }} tasks)

| STT | Công việc | Phụ trách | PIC | Deadline | Số ngày trễ | Ghi chú |
|-----|-----------|-----------|-----|----------|-------------|---------|
{% for task in overdue %}| {{ loop.index }} | {{ task['Công việc'] }} | {{ task['Phụ trách'] }} | {{ task['PIC'] }} | {{ task['Deadline'] }} | {{ task.days_overdue }} ngày | {{ task['Ghi chú'] }} |
{% endfor %}

{% endif %}
{% if due_soon %}
## 🟡 SẮP HẾT HẠN ({{ due_soon|length }} tasks)

| STT | Công việc | Phụ trách | PIC | Deadline | Còn lại | Ghi chú |
|-----|-----------|-----------|-----|----------|---------|---------|
{% for task in due_soon %}| {{ loop.index }} | {{ task['Công việc'] }} | {{ task['Phụ trách'] }} | {{ task['PIC'] }} | {{ task['Deadline'] }} | {{ task.days_left }} ngày | {{ task['Ghi chú'] }} |
{% endfor %}

{% endif %}
{% if completed %}
## 🟢 HOÀN THÀNH TRONG TUẦN ({{ completed|length }} tasks)

| STT | Công việc | Phụ trách | PIC | Deadline |
|-----|-----------|-----------|-----|----------|
{% for task in completed %}| {{ loop.index }} | {{ task['Công việc'] }} | {{ task['Phụ trách'] }} | {{ task['PIC'] }} | {{ task['Deadline'] }} |
{% endfor %}

{% endif %}
{% if on_track %}
## ⚪ ĐANG TRIỂN KHAI / CHƯA BẮT ĐẦU ({{ on_track|length }} tasks)

| STT | Công việc | Phụ trách | PIC | Deadline | Tình trạng | Ghi chú |
|-----|-----------|-----------|-----|----------|-----------|---------|
{% for task in on_track %}| {{ loop.index }} | {{ task['Công việc'] }} | {{ task['Phụ trách'] }} | {{ task['PIC'] }} | {{ task['Deadline'] }} | {{ task['Tình trạng'] }} | {{ task['Ghi chú'] }} |
{% endfor %}

{% endif %}
---

## 📊 TỔNG KẾT THEO CLIENT

| Client | Tổng | 🟢 Hoàn thành | 🔴 Bị block | ⚠️ Quá hạn | ⚪ Đang làm |
|--------|------|--------------|------------|-----------|------------|
{% for project, stats in by_project.items() %}| {{ project }} | {{ stats.total }} | {{ stats.done }} | {{ stats.blocked }} | {{ stats.overdue }} | {{ stats.total - stats.done - stats.blocked - stats.overdue }} |
{% endfor %}

## 👥 TỔNG KẾT THEO PIC

| PIC | Tổng | 🟢 Hoàn thành | 🔴 Bị block | ⚠️ Quá hạn |
|-----|------|--------------|------------|-----------|
{% for owner, stats in by_owner.items() %}| {{ owner }} | {{ stats.total }} | {{ stats.done }} | {{ stats.blocked }} | {{ stats.overdue }} |
{% endfor %}
