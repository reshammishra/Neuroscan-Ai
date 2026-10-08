import os
import uuid
import cv2
from PIL import Image
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import db, Scan
from .dicom_utils import is_valid_image_file, process_dicom_file
from .yolo_service import run_yolo_detection
from .cam_utils import generate_heatmap

detect_bp = Blueprint('detect', __name__, template_folder='../../templates/detect')

@detect_bp.route('/')
def index():
    """Landing route: redirect authenticated users to /detect, else login."""
    if current_user.is_authenticated:
        return redirect(url_for('detect.detect_view'))
    return redirect(url_for('auth.login'))


@detect_bp.route('/detect', methods=['GET', 'POST'])
@login_required
def detect_view():
    """
    Main tumor screening interface.
    Accepts JPG, PNG, and DICOM (.dcm), runs YOLOv8 and EigenCAM, computes estimates,
    and displays screening results.
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Please select an image or DICOM file to upload.', 'warning')
            return redirect(request.url)

        orig_filename = secure_filename(file.filename)
        valid, result = is_valid_image_file(file.stream, orig_filename)
        if not valid:
            flash(f"Upload rejected: {result}", 'danger')
            return redirect(request.url)

        ext = result
        unique_prefix = uuid.uuid4().hex[:12]
        upload_dir = current_app.config['UPLOAD_FOLDER']
        model_path = current_app.config['MODEL_PATH']

        # Parse confidence threshold from form
        try:
            conf_threshold = float(request.form.get('confidence', 0.40))
        except (ValueError, TypeError):
            conf_threshold = 0.40

        # Handle DICOM conversion vs Standard Image
        pixel_spacing = None
        base_img_filename = f"{unique_prefix}_input.png"
        base_img_path = os.path.join(upload_dir, base_img_filename)

        if ext == 'dcm':
            # Convert DICOM to 8-bit RGB PNG and extract pixel spacing
            pixel_spacing, err = process_dicom_file(file.stream, base_img_path)
            if err:
                flash(f"Error processing DICOM: {err}", 'danger')
                return redirect(request.url)
            # Original DICOM file is deleted/never saved for patient privacy
        else:
            file.stream.seek(0)
            img = Image.open(file.stream).convert('RGB')
            img.save(base_img_path, format='PNG')

        # Run YOLOv8 detection and brain area estimation
        det_res = run_yolo_detection(
            image_path=base_img_path,
            model_path=model_path,
            conf_threshold=conf_threshold,
            pixel_spacing=pixel_spacing
        )

        # Save annotated image
        annotated_filename = f"{unique_prefix}_annotated.png"
        annotated_path = os.path.join(upload_dir, annotated_filename)
        cv2.imwrite(annotated_path, det_res['annotated_image'])

        # Generate EigenCAM heatmap overlay
        heatmap_filename = f"{unique_prefix}_heatmap.png"
        heatmap_path = os.path.join(upload_dir, heatmap_filename)
        try:
            generate_heatmap(
                image_path=base_img_path,
                model_path=model_path,
                output_heatmap_path=heatmap_path
            )
        except Exception as e:
            current_app.logger.error(f"Error generating heatmap: {e}")
            heatmap_filename = None

        # Clean up intermediate base image
        if os.path.exists(base_img_path):
            try:
                os.remove(base_img_path)
            except OSError:
                pass

        # Save Scan record in DB linked to current_user
        scan = Scan(
            user_id=current_user.id,
            original_filename=orig_filename,
            file_type=ext,
            predicted_class=det_res['predicted_class'],
            confidence=det_res['confidence'],
            tumor_area_percent=det_res['tumor_area_percent'],
            tumor_size_mm=det_res['tumor_size_mm'],
            annotated_image_path=annotated_filename,
            heatmap_image_path=heatmap_filename
        )
        db.session.add(scan)
        db.session.commit()

        return render_template('detect/detect.html', scan=scan, result=True)

    return render_template('detect/detect.html', scan=None, result=False)


@detect_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded images securely."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
