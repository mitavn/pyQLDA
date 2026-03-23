from models.user import db
from models.field_config import FieldConfig
import json

DEFAULT_FIELDS = {
    'contact': [
        # Thông tin chung
        {'field_name': 'customer_code', 'label': 'Mã khách hàng', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 1, 'is_required': False},
        {'field_name': 'first_name', 'label': 'Tên', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 2, 'is_required': True},
        {'field_name': 'last_name', 'label': 'Họ', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 3, 'is_required': False},
        {'field_name': 'email', 'label': 'Email', 'field_type': 'email', 'group_name': 'Thông tin chung', 'sort_order': 4, 'is_required': False},
        {'field_name': 'phone', 'label': 'Điện thoại', 'field_type': 'phone', 'group_name': 'Thông tin chung', 'sort_order': 5, 'is_required': False},
        {'field_name': 'mobile', 'label': 'Di động', 'field_type': 'phone', 'group_name': 'Thông tin chung', 'sort_order': 6, 'is_required': False},
        {'field_name': 'position', 'label': 'Chức vụ', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 7, 'is_required': False},
        {'field_name': 'department', 'label': 'Phòng ban', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 8, 'is_required': False},
        {'field_name': 'gender', 'label': 'Giới tính', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 9, 'options': json.dumps(['Nam', 'Nữ', 'Khác'])},
        {'field_name': 'date_of_birth', 'label': 'Ngày sinh', 'field_type': 'date', 'group_name': 'Thông tin chung', 'sort_order': 10},
        {'field_name': 'customer_type', 'label': 'Loại khách hàng', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 11, 'options': json.dumps(['Cá nhân', 'Doanh nghiệp'])},
        {'field_name': 'category', 'label': 'Phân loại', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 12, 'options': json.dumps(['VIP', 'Thường', 'Tiềm năng'])},
        {'field_name': 'source', 'label': 'Nguồn', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 13, 'options': json.dumps(['Website', 'Giới thiệu', 'Quảng cáo', 'Mạng xã hội', 'Sự kiện', 'Cold call', 'Khác'])},
        {'field_name': 'company_id', 'label': 'Công ty', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 14},
        # Địa chỉ
        {'field_name': 'address', 'label': 'Địa chỉ', 'field_type': 'text', 'group_name': 'Địa chỉ', 'sort_order': 20},
        {'field_name': 'city', 'label': 'Tỉnh/Thành phố', 'field_type': 'text', 'group_name': 'Địa chỉ', 'sort_order': 21},
        {'field_name': 'district', 'label': 'Quận/Huyện', 'field_type': 'text', 'group_name': 'Địa chỉ', 'sort_order': 22},
        {'field_name': 'ward', 'label': 'Phường/Xã', 'field_type': 'text', 'group_name': 'Địa chỉ', 'sort_order': 23},
        {'field_name': 'country', 'label': 'Quốc gia', 'field_type': 'text', 'group_name': 'Địa chỉ', 'sort_order': 24},
        # Tài chính
        {'field_name': 'tax_code', 'label': 'Mã số thuế', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 30},
        {'field_name': 'bank_account', 'label': 'Số tài khoản', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 31},
        {'field_name': 'bank_name', 'label': 'Ngân hàng', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 32},
        # Mạng xã hội
        {'field_name': 'website', 'label': 'Website', 'field_type': 'text', 'group_name': 'Mạng xã hội', 'sort_order': 40},
        {'field_name': 'facebook', 'label': 'Facebook', 'field_type': 'text', 'group_name': 'Mạng xã hội', 'sort_order': 41},
        {'field_name': 'zalo', 'label': 'Zalo', 'field_type': 'text', 'group_name': 'Mạng xã hội', 'sort_order': 42},
        {'field_name': 'linkedin', 'label': 'LinkedIn', 'field_type': 'text', 'group_name': 'Mạng xã hội', 'sort_order': 43},
        # Bổ sung
        {'field_name': 'description', 'label': 'Mô tả', 'field_type': 'textarea', 'group_name': 'Bổ sung', 'sort_order': 50},
        {'field_name': 'tags', 'label': 'Tags', 'field_type': 'text', 'group_name': 'Bổ sung', 'sort_order': 51},
    ],
    'company': [
        {'field_name': 'name', 'label': 'Tên công ty', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 1, 'is_required': True},
        {'field_name': 'short_name', 'label': 'Tên viết tắt', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 2},
        {'field_name': 'tax_code', 'label': 'Mã số thuế', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 3},
        {'field_name': 'industry', 'label': 'Ngành nghề', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 4, 'options': json.dumps(['Công nghệ', 'Tài chính', 'Bất động sản', 'Sản xuất', 'Thương mại', 'Dịch vụ', 'Giáo dục', 'Y tế', 'Khác'])},
        {'field_name': 'company_type', 'label': 'Loại hình', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 5, 'options': json.dumps(['Công ty TNHH', 'Công ty Cổ phần', 'Doanh nghiệp tư nhân', 'Hộ kinh doanh', 'Khác'])},
        {'field_name': 'staff_size', 'label': 'Quy mô', 'field_type': 'select', 'group_name': 'Thông tin chung', 'sort_order': 6, 'options': json.dumps(['1-10', '11-50', '51-200', '201-500', '500+'])},
        {'field_name': 'phone', 'label': 'Điện thoại', 'field_type': 'phone', 'group_name': 'Thông tin chung', 'sort_order': 7},
        {'field_name': 'email', 'label': 'Email', 'field_type': 'email', 'group_name': 'Thông tin chung', 'sort_order': 8},
        {'field_name': 'website', 'label': 'Website', 'field_type': 'text', 'group_name': 'Thông tin chung', 'sort_order': 9},
        # Địa chỉ hóa đơn
        {'field_name': 'billing_address', 'label': 'Địa chỉ hóa đơn', 'field_type': 'text', 'group_name': 'Địa chỉ hóa đơn', 'sort_order': 20},
        {'field_name': 'billing_city', 'label': 'Tỉnh/TP (HĐ)', 'field_type': 'text', 'group_name': 'Địa chỉ hóa đơn', 'sort_order': 21},
        {'field_name': 'billing_district', 'label': 'Quận/Huyện (HĐ)', 'field_type': 'text', 'group_name': 'Địa chỉ hóa đơn', 'sort_order': 22},
        # Tài chính
        {'field_name': 'bank_account', 'label': 'Số tài khoản', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 30},
        {'field_name': 'bank_name', 'label': 'Ngân hàng', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 31},
        {'field_name': 'annual_revenue', 'label': 'Doanh thu năm', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 32},
        {'field_name': 'credit_limit', 'label': 'Hạn mức tín dụng', 'field_type': 'number', 'group_name': 'Tài chính', 'sort_order': 33},
        # Bổ sung
        {'field_name': 'description', 'label': 'Mô tả', 'field_type': 'textarea', 'group_name': 'Bổ sung', 'sort_order': 50},
        {'field_name': 'tags', 'label': 'Tags', 'field_type': 'text', 'group_name': 'Bổ sung', 'sort_order': 51},
    ],
    'deal': [
        {'field_name': 'name', 'label': 'Tên deal', 'field_type': 'text', 'group_name': 'Thông tin deal', 'sort_order': 1, 'is_required': True},
        {'field_name': 'value', 'label': 'Giá trị', 'field_type': 'number', 'group_name': 'Thông tin deal', 'sort_order': 2},
        {'field_name': 'stage', 'label': 'Giai đoạn', 'field_type': 'select', 'group_name': 'Thông tin deal', 'sort_order': 3, 'options': json.dumps(['Tiếp cận', 'Đánh giá', 'Đề xuất', 'Thương lượng', 'Đóng thắng', 'Đóng thua'])},
        {'field_name': 'probability', 'label': 'Xác suất (%)', 'field_type': 'number', 'group_name': 'Thông tin deal', 'sort_order': 4},
        {'field_name': 'expected_close_date', 'label': 'Ngày đóng dự kiến', 'field_type': 'date', 'group_name': 'Thông tin deal', 'sort_order': 5},
        {'field_name': 'contact_id', 'label': 'Liên hệ', 'field_type': 'select', 'group_name': 'Thông tin deal', 'sort_order': 6},
        {'field_name': 'company_id', 'label': 'Công ty', 'field_type': 'select', 'group_name': 'Thông tin deal', 'sort_order': 7},
        {'field_name': 'source', 'label': 'Nguồn', 'field_type': 'select', 'group_name': 'Chi tiết', 'sort_order': 10, 'options': json.dumps(['Website', 'Giới thiệu', 'Quảng cáo', 'Cold call', 'Khác'])},
        {'field_name': 'description', 'label': 'Mô tả', 'field_type': 'textarea', 'group_name': 'Chi tiết', 'sort_order': 11},
        {'field_name': 'next_step', 'label': 'Bước tiếp theo', 'field_type': 'text', 'group_name': 'Chi tiết', 'sort_order': 12},
        {'field_name': 'competitor', 'label': 'Đối thủ', 'field_type': 'text', 'group_name': 'Chi tiết', 'sort_order': 13},
        # Tài chính
        {'field_name': 'discount', 'label': 'Chiết khấu', 'field_type': 'number', 'group_name': 'Tài chính', 'sort_order': 20},
        {'field_name': 'tax', 'label': 'Thuế', 'field_type': 'number', 'group_name': 'Tài chính', 'sort_order': 21},
        {'field_name': 'total_amount', 'label': 'Tổng tiền', 'field_type': 'number', 'group_name': 'Tài chính', 'sort_order': 22},
        {'field_name': 'contract_number', 'label': 'Số hợp đồng', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 23},
        {'field_name': 'payment_terms', 'label': 'Điều khoản thanh toán', 'field_type': 'text', 'group_name': 'Tài chính', 'sort_order': 24},
    ],
    'activity': [
        {'field_name': 'type', 'label': 'Loại', 'field_type': 'select', 'group_name': 'Thông tin hoạt động', 'sort_order': 1, 'is_required': True, 'options': json.dumps(['call', 'meeting', 'email', 'task', 'note'])},
        {'field_name': 'title', 'label': 'Tiêu đề', 'field_type': 'text', 'group_name': 'Thông tin hoạt động', 'sort_order': 2, 'is_required': True},
        {'field_name': 'description', 'label': 'Mô tả', 'field_type': 'textarea', 'group_name': 'Thông tin hoạt động', 'sort_order': 3},
        {'field_name': 'status', 'label': 'Trạng thái', 'field_type': 'select', 'group_name': 'Thông tin hoạt động', 'sort_order': 4, 'options': json.dumps(['planned', 'completed', 'cancelled'])},
        {'field_name': 'priority', 'label': 'Ưu tiên', 'field_type': 'select', 'group_name': 'Thông tin hoạt động', 'sort_order': 5, 'options': json.dumps(['low', 'normal', 'high', 'urgent'])},
        {'field_name': 'start_time', 'label': 'Thời gian bắt đầu', 'field_type': 'datetime', 'group_name': 'Thời gian', 'sort_order': 10},
        {'field_name': 'end_time', 'label': 'Thời gian kết thúc', 'field_type': 'datetime', 'group_name': 'Thời gian', 'sort_order': 11},
        {'field_name': 'duration_minutes', 'label': 'Thời lượng (phút)', 'field_type': 'number', 'group_name': 'Thời gian', 'sort_order': 12},
        {'field_name': 'location', 'label': 'Địa điểm', 'field_type': 'text', 'group_name': 'Bổ sung', 'sort_order': 20},
        {'field_name': 'result', 'label': 'Kết quả', 'field_type': 'textarea', 'group_name': 'Bổ sung', 'sort_order': 21},
        {'field_name': 'contact_id', 'label': 'Liên hệ', 'field_type': 'select', 'group_name': 'Liên kết', 'sort_order': 30},
        {'field_name': 'deal_id', 'label': 'Deal', 'field_type': 'select', 'group_name': 'Liên kết', 'sort_order': 31},
    ],
}


def seed_default_fields(tenant_id):
    """Tạo field config mặc định cho tenant mới."""
    for module, fields in DEFAULT_FIELDS.items():
        for field_data in fields:
            existing = FieldConfig.query.filter_by(
                tenant_id=tenant_id,
                module=module,
                field_name=field_data['field_name']
            ).first()
            if not existing:
                fc = FieldConfig(
                    tenant_id=tenant_id,
                    module=module,
                    field_name=field_data['field_name'],
                    label=field_data['label'],
                    field_type=field_data.get('field_type', 'text'),
                    group_name=field_data.get('group_name', 'Thông tin chung'),
                    sort_order=field_data.get('sort_order', 0),
                    is_visible=True,
                    is_required=field_data.get('is_required', False),
                    options=field_data.get('options'),
                )
                db.session.add(fc)
    db.session.commit()


def get_field_configs(tenant_id, module):
    """Lấy field configs theo module và tenant."""
    return FieldConfig.query.filter_by(
        tenant_id=tenant_id,
        module=module
    ).order_by(FieldConfig.sort_order).all()


def get_visible_fields(tenant_id, module):
    """Chỉ lấy fields visible."""
    return FieldConfig.query.filter_by(
        tenant_id=tenant_id,
        module=module,
        is_visible=True
    ).order_by(FieldConfig.sort_order).all()


def update_field_order(tenant_id, module, field_orders):
    """Cập nhật thứ tự kéo thả. field_orders = [{id, sort_order}, ...]"""
    for item in field_orders:
        fc = FieldConfig.query.filter_by(
            id=item['id'],
            tenant_id=tenant_id
        ).first()
        if fc:
            fc.sort_order = item['sort_order']
    db.session.commit()


def toggle_field_visibility(tenant_id, field_id):
    """Toggle ẩn/hiện field."""
    fc = FieldConfig.query.filter_by(id=field_id, tenant_id=tenant_id).first()
    if fc:
        fc.is_visible = not fc.is_visible
        db.session.commit()
        return fc.is_visible
    return None


def reset_fields_to_default(tenant_id, module=None):
    """Khôi phục cài đặt trường dữ liệu về mặc định.
    Nếu module=None thì reset tất cả modules.
    """
    if module and module in DEFAULT_FIELDS:
        modules_to_reset = [module]
    else:
        modules_to_reset = list(DEFAULT_FIELDS.keys())

    for mod in modules_to_reset:
        # Xóa tất cả field config hiện tại
        FieldConfig.query.filter_by(tenant_id=tenant_id, module=mod).delete()
        db.session.flush()

        # Tạo lại từ defaults
        for field_data in DEFAULT_FIELDS[mod]:
            fc = FieldConfig(
                tenant_id=tenant_id,
                module=mod,
                field_name=field_data['field_name'],
                label=field_data['label'],
                field_type=field_data.get('field_type', 'text'),
                group_name=field_data.get('group_name', 'Thông tin chung'),
                sort_order=field_data.get('sort_order', 0),
                is_visible=True,
                is_required=field_data.get('is_required', False),
                options=field_data.get('options'),
            )
            db.session.add(fc)

    db.session.commit()
    return True
