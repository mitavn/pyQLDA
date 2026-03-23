<![CDATA[# 🏢 CRM Pro — Hệ thống Quản lý Quan hệ Khách hàng

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-green?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Giao_diện-Tiếng_Việt-red" alt="Vietnamese">
</p>

**CRM Pro** là ứng dụng quản lý quan hệ khách hàng (CRM) toàn diện, được xây dựng bằng Python/Flask với giao diện tiếng Việt. Hệ thống hỗ trợ đa người dùng (multi-tenant), quản lý khách hàng, công ty, deal, báo giá, sản phẩm & kho, nhân sự, và nhiều tính năng nghiệp vụ khác.

---

## ✨ Tính năng chính

### 📇 Quản lý Khách hàng & Công ty
- CRUD liên hệ với mã khách hàng, SĐT, email, tag
- Quản lý công ty với **tra cứu MST tự động** từ Tổng cục Thuế (kiểu masothue.com)
- Validation trùng lặp: SĐT, Email, Mã KH, MST

### 💼 Quản lý Deal & Pipeline
- Pipeline Kanban kéo thả giữa các giai đoạn
- Theo dõi giá trị deal, tỷ lệ thắng/thua
- Liên kết deal với liên hệ, công ty

### 📄 Báo giá (Quotes)
- Tạo báo giá với line items, thuế, chiết khấu
- Trạng thái: Nháp → Đã gửi → Chấp nhận / Từ chối
- Auto-save khi chỉnh sửa

### 📦 Quản lý Sản phẩm & Kho
- Quản lý sản phẩm, SKU, barcode, giá bán/giá vốn
- Phiếu nhập/xuất kho (dự kiến & thực tế)
- Kiểm kho hàng loạt với điều chỉnh tự động
- Import/Export Excel với template mẫu

### 👥 Quản lý Nhân sự
- Quản lý nhân viên với hồ sơ chi tiết
- Phòng ban với cấu trúc phân cấp
- Sơ đồ tổ chức (Org Chart)
- Phân quyền theo vai trò

### ⚙️ Hệ thống
- **Multi-tenant**: hỗ trợ nhiều tổ chức trên cùng hệ thống
- **Cấu hình trường động**: ẩn/hiện trường theo nhu cầu
- **Ghi log hoạt động**: theo dõi mọi thay đổi
- **Ghi chú & Hoạt động**: gắn vào từng bản ghi

---

## 🏗️ Kiến trúc

```
pyQLDN/
├── app.py                  # Flask app factory
├── run.py                  # Entry point
├── config.py               # Cấu hình
├── requirements.txt
│
├── models/                 # SQLAlchemy models
│   ├── user.py             # User, Tenant, db instance
│   ├── contact.py          # Khách hàng
│   ├── company.py          # Công ty
│   ├── deal.py             # Deal/Cơ hội
│   ├── quote.py            # Báo giá + line items
│   ├── product.py          # Sản phẩm, Kho, Phiếu NK/XK
│   ├── department.py       # Phòng ban
│   ├── activity.py         # Hoạt động
│   ├── note.py             # Ghi chú
│   ├── role.py             # Vai trò & quyền
│   └── field_config.py     # Cấu hình trường động
│
├── services/               # Business logic (Service Layer)
│   ├── base_data_provider.py  # BaseDataProvider + ValidationError
│   ├── contact_service.py
│   ├── company_service.py
│   ├── deal_service.py
│   ├── quote_service.py
│   ├── product_service.py
│   ├── field_service.py    # Cấu hình trường động
│   ├── form_parser.py      # Parse form data theo field config
│   └── ...
│
├── routes/                 # Flask Blueprints (Controllers)
│   ├── auth.py, dashboard.py, contacts.py, companies.py
│   ├── deals.py, quotes.py, products.py
│   ├── employees.py, departments.py, team.py
│   ├── settings.py, api.py, activities.py
│   └── ...
│
├── templates/              # Jinja2 templates
├── static/                 # CSS, JS, images
└── instance/               # SQLite database
```

### Design Pattern: Service Layer (Salesforce-inspired)

```python
BaseDataProvider          # CRUD cơ bản + validate + lifecycle hooks
  ├── ContactService      # validate: SĐT, Email, Mã KH unique
  ├── CompanyService      # validate: MST, Email unique
  ├── DealService         # validate: Số HĐ unique
  ├── ProductService      # validate: SKU, Barcode unique
  └── QuoteService        # Báo giá + line items
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.10+
- pip

### Cài đặt

```bash
# Clone project
git clone https://github.com/mitavn/pyQLDA.git
cd pyQLDA

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Cài đặt dependencies
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
python run.py
```

Truy cập: **http://127.0.0.1:5000**

### Tài khoản mặc định
| Tài khoản | Mật khẩu |
|-----------|----------|
| `admin`   | `admin123` |

---

## 🛠️ Tech Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Backend    | Flask 3.0, Flask-SQLAlchemy, Flask-Login |
| Database   | SQLite (có thể chuyển sang PostgreSQL/MySQL) |
| Frontend   | Jinja2, Vanilla CSS (Ant Design theme), JavaScript |
| Icons      | Font Awesome 6 |
| API        | RESTful endpoints cho tra cứu MST, search, AJAX |

---

## 📋 Validation Rules

| Module | Trường | Quy tắc |
|--------|--------|---------|
| Liên hệ | `phone`, `email`, `customer_code` | Không trùng trong cùng tenant |
| Công ty | `tax_code`, `email` | Không trùng trong cùng tenant |
| Sản phẩm | `sku`, `barcode` | Không trùng trong cùng tenant |
| Deal | `contract_number` | Không trùng trong cùng tenant |

---

## 📝 License

MIT License — Tự do sử dụng, chỉnh sửa và phân phối.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/mitavn">mitavn</a>
</p>
]]>
