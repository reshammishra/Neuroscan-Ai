"""
DICOM Processing Utilities.
Handles DICOM file validation, extraction of middle frame, windowing/normalization to 8-bit RGB,
and patient metadata privacy sanitization.
"""
import os
import numpy as np
from PIL import Image
import pydicom

def is_valid_image_file(file_stream, filename):
    """
    Validates file extension and integrity.
    Accepts .jpg, .jpeg, .png, and .dcm.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in {'jpg', 'jpeg', 'png', 'dcm'}:
        return False, f"Unsupported file extension: .{ext}"

    if ext == 'dcm':
        try:
            # Check DICOM validity without keeping patient data
            file_stream.seek(0)
            dcm = pydicom.dcmread(file_stream, stop_before_pixels=False, force=False)
            if not hasattr(dcm, 'pixel_array'):
                return False, "DICOM file has no pixel data."
            file_stream.seek(0)
            return True, ext
        except Exception as e:
            return False, f"Invalid DICOM file: {str(e)}"
    else:
        try:
            file_stream.seek(0)
            img = Image.open(file_stream)
            img.verify()
            file_stream.seek(0)
            return True, ext
        except Exception as e:
            return False, f"Corrupted or invalid image file: {str(e)}"


def apply_windowing(pixel_array, dcm):
    """
    Applies rescale slope/intercept and DICOM window width/center if present.
    """
    # Rescale slope and intercept
    slope = getattr(dcm, 'RescaleSlope', 1.0)
    intercept = getattr(dcm, 'RescaleIntercept', 0.0)
    
    # Handle possible MultiValue in slope/intercept
    try:
        slope = float(slope[0] if hasattr(slope, '__iter__') else slope)
        intercept = float(intercept[0] if hasattr(intercept, '__iter__') else intercept)
    except Exception:
        slope, intercept = 1.0, 0.0

    pixels = pixel_array.astype(np.float32) * slope + intercept

    # Window center and width
    wc = getattr(dcm, 'WindowCenter', None)
    ww = getattr(dcm, 'WindowWidth', None)

    if wc is not None and ww is not None:
        try:
            if hasattr(wc, '__iter__'):
                wc = float(wc[0])
            else:
                wc = float(wc)

            if hasattr(ww, '__iter__'):
                ww = float(ww[0])
            else:
                ww = float(ww)

            min_val = wc - (ww / 2.0)
            max_val = wc + (ww / 2.0)
            pixels = np.clip(pixels, min_val, max_val)
        except Exception:
            pass  # Fall back to min-max normalization

    # Min-max normalization to 0-255
    p_min = pixels.min()
    p_max = pixels.max()
    if p_max > p_min:
        pixels = (pixels - p_min) / (p_max - p_min) * 255.0
    else:
        pixels = np.zeros_like(pixels)

    return pixels.astype(np.uint8)


def process_dicom_file(file_stream, output_png_path):
    """
    Reads DICOM from file stream, converts to 8-bit RGB PNG, and extracts pixel spacing.
    PRIVACY GUARANTEE: Never stores PatientName, PatientID, or BirthDate.
    The original DICOM file is NEVER persisted to disk.
    
    Returns:
        (pixel_spacing_tuple_or_none, error_message_or_none)
    """
    file_stream.seek(0)
    dcm = pydicom.dcmread(file_stream)

    # 1. Pixel spacing extraction (used strictly for size calculations in mm)
    pixel_spacing = None
    if hasattr(dcm, 'PixelSpacing'):
        try:
            ps = dcm.PixelSpacing
            pixel_spacing = (float(ps[0]), float(ps[1]))  # (row_spacing_mm, col_spacing_mm)
        except Exception:
            pixel_spacing = None

    # 2. Extract pixel array and handle multi-frame (select middle frame)
    arr = dcm.pixel_array
    if arr.ndim == 3 and arr.shape[0] > 1:
        # Multi-frame volume: extract middle frame
        middle_idx = arr.shape[0] // 2
        arr = arr[middle_idx]
    elif arr.ndim == 4:
        # Multi-frame color or temporal
        middle_idx = arr.shape[0] // 2
        arr = arr[middle_idx]

    # 3. Apply windowing and intensity normalization
    norm_pixels = apply_windowing(arr, dcm)

    # 4. Handle Photometric Interpretation MONOCHROME1 (invert so bone/bright is high intensity)
    photo_interp = getattr(dcm, 'PhotometricInterpretation', '')
    if photo_interp == 'MONOCHROME1':
        norm_pixels = 255 - norm_pixels

    # 5. Convert to 8-bit RGB image
    if norm_pixels.ndim == 2:
        img_rgb = Image.fromarray(norm_pixels).convert('RGB')
    else:
        img_rgb = Image.fromarray(norm_pixels)
        if img_rgb.mode != 'RGB':
            img_rgb = img_rgb.convert('RGB')

    # 6. Save ONLY the converted PNG to output_png_path
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
    img_rgb.save(output_png_path, format='PNG')

    # PRIVACY: original dcm object is de-referenced and dropped here
    del dcm

    return pixel_spacing, None
