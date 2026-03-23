"""
BaseDataProvider — Generic CRUD data provider.

Inspired by Salesforce sObject API and Refine-CRM dataProvider pattern.
Each resource service extends this class with module-specific logic.
"""
from models.user import db


class BaseDataProvider:
    """Generic data provider for CRM resources (Salesforce/Refine pattern).

    Subclasses MUST set:
        - model: the SQLAlchemy model class
        - module_name: string identifier (e.g. 'contact', 'deal')

    Subclasses CAN override:
        - build_search_filter(query, search)
        - build_filters(query, filters)
        - default_order()
        - enrich_detail(record, tenant_id)
        - before_create(data, tenant_id, user_id)
        - after_create(record, tenant_id, user_id)
        - before_update(record, data, tenant_id)
        - after_update(record, data, tenant_id)
        - before_delete(record, tenant_id)
    """

    model = None
    module_name = None

    # ── List ────────────────────────────────────────────────────
    def get_list(self, tenant_id, filters=None, search=None,
                 sorters=None, page=1, per_page=20):
        """Return paginated list with metadata.

        Args:
            filters: dict of {field_name: value} for equality filters
            search: free-text search string
            sorters: list of (field, 'asc'|'desc') tuples
            page, per_page: pagination

        Returns:
            SQLAlchemy Pagination object
        """
        query = self.model.query.filter_by(tenant_id=tenant_id)

        if search:
            query = self.build_search_filter(query, search)

        if filters:
            query = self.build_filters(query, filters)

        order = self._resolve_sorters(sorters)
        query = query.order_by(*order)

        return query.paginate(page=page, per_page=per_page, error_out=False)

    # ── Get One ─────────────────────────────────────────────────
    def get_one(self, tenant_id, record_id):
        """Return a single record or 404."""
        return self.model.query.filter_by(
            id=record_id, tenant_id=tenant_id
        ).first_or_404()

    # ── Get Many ────────────────────────────────────────────────
    def get_many(self, tenant_id, ids):
        """Return multiple records by ID list."""
        return self.model.query.filter(
            self.model.tenant_id == tenant_id,
            self.model.id.in_(ids)
        ).all()

    # ── Create ──────────────────────────────────────────────────
    def create(self, tenant_id, data, user_id):
        """Create a new record from a dict of field values.

        Returns the created record.
        """
        data = self.before_create(data, tenant_id, user_id)

        record = self.model(
            tenant_id=tenant_id,
            created_by=user_id,
            owner_id=user_id,
        )
        self._apply_data(record, data)

        db.session.add(record)
        db.session.commit()

        self.after_create(record, tenant_id, user_id)
        return record

    # ── Update ──────────────────────────────────────────────────
    def update(self, tenant_id, record_id, data):
        """Update an existing record.

        Returns the updated record.
        """
        record = self.get_one(tenant_id, record_id)
        data = self.before_update(record, data, tenant_id)
        self._apply_data(record, data)
        db.session.commit()
        self.after_update(record, data, tenant_id)
        return record

    # ── Delete ──────────────────────────────────────────────────
    def delete(self, tenant_id, record_id):
        """Delete a record. Returns True on success."""
        record = self.get_one(tenant_id, record_id)
        self.before_delete(record, tenant_id)
        db.session.delete(record)
        db.session.commit()
        return True

    # ── Query helpers (override in subclasses) ──────────────────
    def build_search_filter(self, query, search):
        """Apply free-text search. Override in subclass."""
        return query

    def build_filters(self, query, filters):
        """Apply equality filters from dict."""
        for field, value in filters.items():
            if value and hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query

    def default_order(self):
        """Default ORDER BY clause. Override to customize."""
        return [self.model.created_at.desc()]

    # ── Lifecycle hooks (override in subclasses) ────────────────
    def before_create(self, data, tenant_id, user_id):
        """Hook called before creating a record. Return modified data."""
        return data

    def after_create(self, record, tenant_id, user_id):
        """Hook called after record is committed."""
        pass

    def before_update(self, record, data, tenant_id):
        """Hook called before updating. Return modified data."""
        return data

    def after_update(self, record, data, tenant_id):
        """Hook called after update is committed."""
        pass

    def before_delete(self, record, tenant_id):
        """Hook called before deleting."""
        pass

    # ── Related data loader ─────────────────────────────────────
    def get_related(self, tenant_id, record_id):
        """Load related records for detail views. Override in subclass.

        Returns dict of {relation_name: records}.
        """
        return {}

    # ── Internal helpers ────────────────────────────────────────
    def _apply_data(self, record, data):
        """Set model attributes from a dict."""
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

    def _resolve_sorters(self, sorters):
        """Convert sorter tuples to SQLAlchemy order_by clauses."""
        if not sorters:
            return self.default_order()

        clauses = []
        for field, direction in sorters:
            col = getattr(self.model, field, None)
            if col is not None:
                clauses.append(col.asc() if direction == 'asc' else col.desc())
        return clauses or self.default_order()
