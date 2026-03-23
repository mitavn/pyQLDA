from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import db
from models.note import Note
from models.contact import Contact
from models.company import Company
from models.deal import Deal
from services.field_service import update_field_order, toggle_field_visibility, reset_fields_to_default
import csv
import io
from flask import Response

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/fields/reorder', methods=['POST'])
@login_required
def reorder_fields():
    data = request.get_json()
    module = data.get('module')
    fields = data.get('fields', [])
    update_field_order(current_user.tenant_id, module, fields)
    return jsonify({'success': True})


@api_bp.route('/fields/<int:field_id>/toggle', methods=['POST'])
@login_required
def toggle_field(field_id):
    result = toggle_field_visibility(current_user.tenant_id, field_id)
    if result is not None:
        return jsonify({'success': True, 'is_visible': result})
    return jsonify({'success': False}), 404


@api_bp.route('/fields/reset', methods=['POST'])
@login_required
def reset_fields():
    data = request.get_json()
    module = data.get('module')
    reset_fields_to_default(current_user.tenant_id, module)
    return jsonify({'success': True})


@api_bp.route('/notes', methods=['POST'])
@login_required
def add_note():
    data = request.get_json()
    note = Note(
        tenant_id=current_user.tenant_id,
        module=data.get('module'),
        record_id=data.get('record_id'),
        content=data.get('content', '').strip(),
        user_id=current_user.id
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({
        'success': True,
        'note': {
            'id': note.id,
            'content': note.content,
            'user': current_user.full_name or current_user.username,
            'created_at': note.created_at.strftime('%d/%m/%Y %H:%M')
        }
    })


@api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/export/<module>')
@login_required
def export_csv(module):
    tenant_id = current_user.tenant_id
    models = {
        'contacts': Contact,
        'companies': Company,
        'deals': Deal,
    }
    model = models.get(module)
    if not model:
        return jsonify({'error': 'Invalid module'}), 400

    records = model.query.filter_by(tenant_id=tenant_id).all()

    si = io.StringIO()
    writer = csv.writer(si)

    if records:
        exclude = {'tenant_id', 'password_hash'}
        columns = [c.name for c in model.__table__.columns if c.name not in exclude]
        writer.writerow(columns)
        for record in records:
            writer.writerow([getattr(record, col, '') for col in columns])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={module}_export.csv'}
    )
