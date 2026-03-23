"""ContactService — Data provider for Contact resources."""
from models.user import db
from models.contact import Contact
from models.activity import Activity
from models.note import Note
from models.company import Company
from services.base_data_provider import BaseDataProvider


class ContactService(BaseDataProvider):

    model = Contact
    module_name = 'contact'

    def validate(self, data, tenant_id, record_id=None):
        """Validate: SĐT và Email không trùng."""
        phone = (data.get('phone') or '').strip()
        if phone:
            self._check_unique(tenant_id, 'phone', phone, record_id, 'Số điện thoại')

        email = (data.get('email') or '').strip()
        if email:
            self._check_unique(tenant_id, 'email', email, record_id, 'Email')

        customer_code = (data.get('customer_code') or '').strip()
        if customer_code:
            self._check_unique(tenant_id, 'customer_code', customer_code, record_id, 'Mã khách hàng')

    def build_search_filter(self, query, search):
        return query.filter(
            db.or_(
                Contact.first_name.ilike(f'%{search}%'),
                Contact.last_name.ilike(f'%{search}%'),
                Contact.email.ilike(f'%{search}%'),
                Contact.phone.ilike(f'%{search}%'),
                Contact.customer_code.ilike(f'%{search}%'),
            )
        )

    def get_related(self, tenant_id, record_id):
        activities = Activity.query.filter_by(
            tenant_id=tenant_id, contact_id=record_id
        ).order_by(Activity.created_at.desc()).limit(20).all()

        notes = Note.query.filter_by(
            tenant_id=tenant_id, module='contact', record_id=record_id
        ).order_by(Note.created_at.desc()).all()

        companies = Company.query.filter_by(
            tenant_id=tenant_id
        ).order_by(Company.name).all()

        return {
            'activities': activities,
            'notes': notes,
            'companies': companies,
        }

    def get_companies(self, tenant_id):
        return Company.query.filter_by(
            tenant_id=tenant_id
        ).order_by(Company.name).all()
