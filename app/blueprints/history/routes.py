import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from app.models import db, Scan

history_bp = Blueprint('history', __name__, template_folder='../../templates/history')

@history_bp.route('/')
@login_required
def index():
    """
    Display a table of scans belonging strictly to the currently logged-in user.
    """
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
    return render_template('history.html', scans=scans)


@history_bp.route('/<int:scan_id>')
@login_required
def view_scan(scan_id):
    """
    View details for a specific scan.
    SECURITY: Ensures user can only view their own scan. Returns 404 if not found or unauthorized.
    """
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        abort(404)
    return render_template('view_scan.html', scan=scan)


@history_bp.route('/<int:scan_id>/notes', methods=['POST'])
@login_required
def update_notes(scan_id):
    """
    Update clinical notes for a scan (Doctor role only).
    """
    if not current_user.is_doctor:
        abort(403)

    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        abort(404)

    notes = request.form.get('clinical_notes', '').strip()
    scan.clinical_notes = notes
    db.session.commit()
    flash('Clinical notes updated successfully.', 'success')
    return redirect(request.referrer or url_for('history.index'))


@history_bp.route('/<int:scan_id>/delete', methods=['POST'])
@login_required
def delete_scan(scan_id):
    """
    Delete a scan and its associated files.
    SECURITY: Scoped strictly to the logged-in user. Returns 404 if not owned.
    """
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        abort(404)

    # Clean up image files from disk
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if scan.annotated_image_path:
        path = os.path.join(upload_dir, scan.annotated_image_path)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    if scan.heatmap_image_path:
        path = os.path.join(upload_dir, scan.heatmap_image_path)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.session.delete(scan)
    db.session.commit()
    flash('Scan record removed successfully.', 'info')
    return redirect(url_for('history.index'))
