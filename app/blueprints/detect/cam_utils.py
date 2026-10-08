"""
EigenCAM Heatmap Generator for YOLOv8.

Why EigenCAM on YOLOv8 backbone layer 8 (C2f)?
1. YOLOv8 is a detection model without a traditional single classification head, which
   causes gradient-based Grad-CAM to struggle with multiple anchorless detection outputs.
2. EigenCAM computes the principal components of the 2D activations from the target layer,
   making it completely class-independent and gradient-free. It highlights whatever visual
   features most strongly influenced the network's internal representations.
3. Layer 8 (C2f) is the final feature extraction block of the YOLOv8 backbone right before
   the SPPF (Spatial Pyramid Pooling - Fast) block. It provides rich, high-level semantic
   spatial representations with large receptive fields without suffering from the task-specific
   splitting that occurs later in the PANet neck and decoupled detection heads.
"""
import os
import cv2
import torch
import numpy as np
from PIL import Image
from pytorch_grad_cam import EigenCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from .yolo_service import get_yolo_model

_CAM_INSTANCE = None
_CACHED_MODEL_REF = None

def get_cam_instance(model_path):
    """Initializes and caches the EigenCAM instance on YOLOv8 backbone layer 8."""
    global _CAM_INSTANCE, _CACHED_MODEL_REF
    yolo_obj = get_yolo_model(model_path)
    py_model = yolo_obj.model.eval()

    if _CAM_INSTANCE is None or _CACHED_MODEL_REF != py_model:
        # Layer 8 is the last C2f backbone layer
        target_layer = [py_model.model[8]]
        _CAM_INSTANCE = EigenCAM(model=py_model, target_layers=target_layer)
        _CACHED_MODEL_REF = py_model

    return _CAM_INSTANCE


def generate_heatmap(image_path, model_path, output_heatmap_path):
    """
    Generates an EigenCAM heatmap overlay for the given image and saves it to output_heatmap_path.
    
    Args:
        image_path: Input image path (RGB/PNG/JPG)
        model_path: Path to best.pt
        output_heatmap_path: Path where overlay image should be saved
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Could not read image for heatmap generation at {image_path}")

    h, w = img_bgr.shape[:2]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # YOLOv8 input resizing (640x640)
    resized_rgb = cv2.resize(img_rgb, (640, 640))
    input_tensor = torch.from_numpy(resized_rgb).permute(2, 0, 1).unsqueeze(0).float() / 255.0

    cam = get_cam_instance(model_path)

    # EigenCAM computes the first principal component of activations
    grayscale_cam = cam(input_tensor=input_tensor, targets=[])[0, :]
    cam_resized = cv2.resize(grayscale_cam, (w, h))

    # Normalize image to [0, 1] for visualization
    rgb_normalized = img_rgb.astype(np.float32) / 255.0
    cam_overlay = show_cam_on_image(rgb_normalized, cam_resized, use_rgb=True)

    # Convert back to uint8 RGB and save
    os.makedirs(os.path.dirname(output_heatmap_path), exist_ok=True)
    overlay_img = Image.fromarray(cam_overlay)
    overlay_img.save(output_heatmap_path, format='PNG')
    return output_heatmap_path
