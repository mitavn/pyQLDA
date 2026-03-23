"""DealService — Data provider for Deal resources."""
from datetime import datetime
from models.user import db
from models.deal import Deal
from models.contact import Contact
from models.company import Company
from models.activity import Activity
from models.note import Note
from services.base_data_provider import BaseDataProvider

DEAL_STAGES = ['Tiếp cận', 'Đánh giá', 'Đề xuất', 'Thương lượng', 'Đóng thắng', 'Đóng thua']


class DealService(BaseDataProvider):

    model = Deal
    module_name = 'deal'

    def build_search_filter(self, query, search):
        return query.filter(Deal.name.ilike(f'%{search}%'))

    def before_create(self, data, tenant_id, user_id):
        """Auto-set status based on stage."""
        data['status'] = self._status_from_stage(data.get('stage'))
        return data

    def before_update(self, record, data, tenant_id):
        """Auto-set status based on stage."""
        data['status'] = self._status_from_stage(data.get('stage', record.stage))
        return data

    # ── Pipeline view ───────────────────────────────────────────
    def get_pipeline(self, tenant_id):
        """Return stages_data dict for pipeline/kanban view."""
        stages_data = {}
        for stage in DEAL_STAGES:
            deals = Deal.query.filter_by(
                tenant_id=tenant_id, stage=stage
            ).order_by(Deal.value.desc()).all()
            total = sum(d.value or 0 for d in deals)
            stages_data[stage] = {
                'deals': deals,
                'total': total,
                'count': len(deals),
            }
        return stages_data

    # ── Stage move (drag-drop) ──────────────────────────────────
    def move_stage(self, tenant_id, deal_id, new_stage):
        """Move a deal to a new stage. Returns (success, deal_or_None)."""
        if new_stage not in DEAL_STAGES:
            return False, None

        deal = self.get_one(tenant_id, deal_id)
        deal.stage = new_stage
        deal.status = self._status_from_stage(new_stage)

        if new_stage in ('Đóng thắng', 'Đóng thua'):
            deal.actual_close_date = datetime.utcnow().date()

        db.session.commit()
        return True, deal

    # ── Related data ────────────────────────────────────────────
    def get_related(self, tenant_id, record_id):
        activities = Activity.query.filter_by(
            tenant_id=tenant_id, deal_id=record_id
        ).order_by(Activity.created_at.desc()).limit(20).all()

        notes = Note.query.filter_by(
            tenant_id=tenant_id, module='deal', record_id=record_id
        ).order_by(Note.created_at.desc()).all()

        contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
        companies = Company.query.filter_by(tenant_id=tenant_id).all()

        return {
            'activities': activities,
            'notes': notes,
            'contacts': contacts,
            'companies': companies,
        }

    def get_form_options(self, tenant_id):
        """Load dropdown data for create/edit forms."""
        return {
            'contacts': Contact.query.filter_by(tenant_id=tenant_id).order_by(Contact.first_name).all(),
            'companies': Company.query.filter_by(tenant_id=tenant_id).order_by(Company.name).all(),
        }

    # ── Internal helpers ────────────────────────────────────────
    @staticmethod
    def _status_from_stage(stage):
        if stage == 'Đóng thắng':
            return 'won'
        elif stage == 'Đóng thua':
            return 'lost'
        return 'open'
