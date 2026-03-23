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

    def validate(self, data, tenant_id, record_id=None):
        """Validate: Số hợp đồng không trùng."""
        contract_number = (data.get('contract_number') or '').strip()
        if contract_number:
            self._check_unique(tenant_id, 'contract_number', contract_number, record_id, 'Số hợp đồng')

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
        """Move a deal to a new stage. Returns (success, deal_or_None).
        IMPORTANT: value is NEVER reset during stage moves."""
        if new_stage not in DEAL_STAGES:
            return False, None

        deal = self.get_one(tenant_id, deal_id)
        deal.stage = new_stage
        deal.status = self._status_from_stage(new_stage)

        if new_stage == 'Đóng thắng':
            deal.actual_close_date = datetime.utcnow().date()
            # Set total_amount = value (preserve revenue for stats)
            if deal.value:
                deal.total_amount = deal.value
        elif new_stage == 'Đóng thua':
            deal.actual_close_date = datetime.utcnow().date()
        else:
            # Re-opening: clear close date
            if deal.actual_close_date and new_stage not in ('Đóng thắng', 'Đóng thua'):
                deal.actual_close_date = None

        db.session.commit()
        return True, deal

    # ── Sync from quote ─────────────────────────────────────────
    def get_quotes_for_deal(self, tenant_id, deal_id):
        """Get all quotes linked to a deal."""
        from models.quote import Quote
        return Quote.query.filter_by(
            tenant_id=tenant_id, deal_id=deal_id
        ).order_by(Quote.created_at.desc()).all()

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
