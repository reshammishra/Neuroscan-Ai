"""
YOLOv8 Detection and Tumor Sizing Service.
Runs YOLOv8 model inference, computes relative area percentage against Otsu brain contour,
and calculates physical dimensions (width x height in mm) if DICOM PixelSpacing is provided.
"""
import os
import cv2
import numpy as np
from ultralytics import YOLO

# Global model cache to avoid re-instantiating heavy PyTorch weights on every request
_MODEL_INSTANCE = None

def get_yolo_model(model_path):
    """Singleton getter for the trained YOLOv8 model."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = YOLO(model_path)
    return _MODEL_INSTANCE


def estimate_brain_area(image_bgr):
    """
    Estimates total brain area in pixels using Otsu thresholding on grayscale image
    and finding the largest contour (representing the skull/brain matter).
    Falls back to full image area if contour detection fails or returns an implausible area.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    total_image_area = float(gray.shape[0] * gray.shape[1])

    # Slight blur to reduce noise before thresholding
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Otsu automatic thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return total_image_area

    # Largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    brain_area = float(cv2.contourArea(largest_contour))

    # Plausibility check: brain area should be at least 5% of total image
    if brain_area < 0.05 * total_image_area:
        return total_image_area

    return brain_area


def run_yolo_detection(image_path, model_path, conf_threshold=0.40, pixel_spacing=None):
    """
    Executes YOLOv8 detection on the provided image.
    
    Args:
        image_path: Path to the image on disk (RGB/PNG/JPG)
        model_path: Path to best.pt
        conf_threshold: Confidence threshold float (e.g. 0.40)
        pixel_spacing: Optional tuple (row_spacing_mm, col_spacing_mm) from DICOM
        
    Returns:
        dict: {
            'predicted_class': str,
            'confidence': float, # 0.0 - 100.0
            'tumor_area_percent': float or None,
            'tumor_size_mm': str or None,
            'boxes': list of (x1, y1, x2, y2),
            'annotated_image': np.ndarray (BGR)
        }
    """
    model = get_yolo_model(model_path)
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError(f"Could not load image at {image_path}")

    # Run inference with user-selected confidence threshold
    results = model.predict(source=image_path, conf=conf_threshold, verbose=False)
    
    annotated_bgr = image_bgr.copy()
    detected_boxes = []

    # If no results or no bounding boxes detected
    if not results or len(results[0].boxes) == 0:
        return {
            'predicted_class': 'No tumor detected',
            'confidence': 0.0,
            'tumor_area_percent': None,
            'tumor_size_mm': None,
            'boxes': [],
            'annotated_image': annotated_bgr
        }

    first_result = results[0]
    boxes = first_result.boxes

    # Get class names dictionary from model
    names = getattr(model, 'names', {0: 'glioma', 1: 'meningioma', 2: 'pituitary'})

    # Find highest confidence detection
    best_idx = int(boxes.conf.argmax().item())
    best_conf = float(boxes.conf[best_idx].item()) * 100.0
    best_cls_id = int(boxes.cls[best_idx].item())
    predicted_class = names.get(best_cls_id, f"Class {best_cls_id}")

    # Brain area estimation via Otsu contour
    brain_area = estimate_brain_area(image_bgr)

    # Box coordinates [x1, y1, x2, y2]
    xyxy = boxes.xyxy[best_idx].cpu().numpy()
    x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
    box_w = max(0.0, x2 - x1)
    box_h = max(0.0, y2 - y1)
    box_area = box_w * box_h

    # Relative area %
    tumor_area_percent = (box_area / brain_area) * 100.0 if brain_area > 0 else 0.0

    # Physical mm estimation if DICOM PixelSpacing is provided
    tumor_size_mm = None
    if pixel_spacing and len(pixel_spacing) == 2:
        row_sp, col_sp = pixel_spacing
        w_mm = box_w * float(col_sp)
        h_mm = box_h * float(row_sp)
        tumor_size_mm = f"{w_mm:.1f} mm x {h_mm:.1f} mm (Approx)"

    # Draw all detected bounding boxes cleanly using standard colors matching UI palette
    for i in range(len(boxes)):
        b = boxes.xyxy[i].cpu().numpy()
        c = float(boxes.conf[i].item()) * 100.0
        cls_id = int(boxes.cls[i].item())
        label = f"{names.get(cls_id, 'Tumor')} {c:.1f}%"

        bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
        detected_boxes.append((bx1, by1, bx2, by2))

        # Primary border: Blue-purple BGR (237, 111, 47 in RGB -> (237, 111, 47) in BGR is (47, 111, 237))
        cv2.rectangle(annotated_bgr, (bx1, by1), (bx2, by2), (47, 111, 237), 2)

        # Label background
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(annotated_bgr, (bx1, max(0, by1 - th - baseline - 4)), (bx1 + tw + 6, max(0, by1)), (47, 111, 237), -1)
        cv2.putText(annotated_bgr, label, (bx1 + 3, max(th, by1 - baseline - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    return {
        'predicted_class': predicted_class,
        'confidence': best_conf,
        'tumor_area_percent': tumor_area_percent,
        'tumor_size_mm': tumor_size_mm,
        'boxes': detected_boxes,
        'annotated_image': annotated_bgr
    }
