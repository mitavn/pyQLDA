"""
FormParser — Centralized form-data → model-dict converter.

Eliminates the duplicated `for fc in field_configs: ...` blocks
that appear in every route handler.
"""
from datetime import datetime


# Foreign-key field names that should be parsed as int
FK_FIELDS = {'contact_id', 'company_id', 'deal_id', 'product_id'}


def parse_form_data(form, field_configs):
    """Parse Flask request.form using FieldConfig list into a model-ready dict.

    Args:
        form: Flask request.form (ImmutableMultiDict)
        field_configs: list of FieldConfig objects (from get_visible_fields)

    Returns:
        dict of {field_name: parsed_value}
    """
    data = {}

    for fc in field_configs:
        raw = form.get(fc.field_name, '').strip()

        if fc.field_name in FK_FIELDS:
            data[fc.field_name] = int(raw) if raw else None

        elif fc.field_type == 'number':
            data[fc.field_name] = _parse_number(raw)

        elif fc.field_type == 'date':
            data[fc.field_name] = _parse_date(raw)

        elif fc.field_type == 'datetime':
            data[fc.field_name] = _parse_datetime(raw)

        else:
            # text, email, phone, textarea, select
            data[fc.field_name] = raw if raw else None

    return data


def parse_form_data_for_update(form, field_configs):
    """Same as parse_form_data but preserves None for empty FK fields
    (ensures they get cleared on update).
    """
    return parse_form_data(form, field_configs)


# ── Type parsers ────────────────────────────────────────────────

def _parse_number(raw):
    """Parse a numeric string, return float or None."""
    if not raw:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def _parse_date(raw):
    """Parse 'YYYY-MM-DD' string into date, or None."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _parse_datetime(raw):
    """Parse 'YYYY-MM-DDTHH:MM' string into datetime, or None."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%dT%H:%M')
    except (ValueError, TypeError):
        return None
