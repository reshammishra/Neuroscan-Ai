from io import BytesIO
from flask import Blueprint, send_file, abort
from flask_login import login_required, current_user
from app.models import Scan
from .pdf_service import generate_pdf_report

report_bp = Blueprint('report', __name__, template_folder='../../templates/report')

@report_bp.route('/<int:scan_id>/<lang>')
@login_required
def download_report(scan_id, lang='en'):
    """
    Downloads the PDF screening report for a scan in English or Hindi.
    SECURITY: Scoped strictly to the logged-in user. Returns 404 if not found or unauthorized.
    """
    if lang not in ('en', 'hi'):
        lang = 'en'

    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        abort(404)

    pdf_bytes = generate_pdf_report(scan, current_user, lang=lang)
    filename = f"neuroscan_report_{scan.id}_{lang}.pdf"

    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
