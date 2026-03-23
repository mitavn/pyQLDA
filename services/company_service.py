"""CompanyService — Data provider for Company resources."""
from models.user import db
from models.company import Company
from models.contact import Contact
from models.activity import Activity
from models.note import Note
from services.base_data_provider import BaseDataProvider


class CompanyService(BaseDataProvider):

    model = Company
    module_name = 'company'

    def build_search_filter(self, query, search):
        return query.filter(
            db.or_(
                Company.name.ilike(f'%{search}%'),
                Company.tax_code.ilike(f'%{search}%'),
                Company.phone.ilike(f'%{search}%'),
            )
        )

    def get_related(self, tenant_id, record_id):
        contacts = Contact.query.filter_by(
            tenant_id=tenant_id, company_id=record_id
        ).all()

        activities = Activity.query.filter_by(
            tenant_id=tenant_id, company_id=record_id
        ).order_by(Activity.created_at.desc()).limit(20).all()

        notes = Note.query.filter_by(
            tenant_id=tenant_id, module='company', record_id=record_id
        ).order_by(Note.created_at.desc()).all()

        return {
            'contacts': contacts,
            'activities': activities,
            'notes': notes,
        }
