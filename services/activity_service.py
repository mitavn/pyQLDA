"""ActivityService — Data provider for Activity resources."""
from models.user import db
from models.activity import Activity
from models.contact import Contact
from models.deal import Deal
from services.base_data_provider import BaseDataProvider

ACTIVITY_TYPES = [
    ('call', '📞 Cuộc gọi'),
    ('meeting', '🤝 Cuộc họp'),
    ('email', '✉️ Email'),
    ('task', '✅ Công việc'),
    ('note', '📝 Ghi chú'),
]


class ActivityService(BaseDataProvider):

    model = Activity
    module_name = 'activity'

    def build_search_filter(self, query, search):
        return query.filter(Activity.title.ilike(f'%{search}%'))

    def get_form_options(self, tenant_id):
        """Load dropdown data for create/edit forms."""
        return {
            'contacts': Contact.query.filter_by(tenant_id=tenant_id).all(),
            'deals': Deal.query.filter_by(tenant_id=tenant_id, status='open').all(),
        }

    def get_form_options_all(self, tenant_id):
        """Load dropdown data for edit forms (include all deals)."""
        return {
            'contacts': Contact.query.filter_by(tenant_id=tenant_id).all(),
            'deals': Deal.query.filter_by(tenant_id=tenant_id).all(),
        }
