# NeuroScan AI: Brain Tumor Screening Web Platform

Brain tumor detection web app using YOLOv8 and Flask. Supports JPG/PNG and DICOM MRI scans, Grad-CAM heatmaps, tumor size estimates, role-based login with scan history, and English/Hindi PDF reports.

An educational, end-to-end Flask web application for computer-aided brain tumor screening.

> **IMPORTANT NOTICE:**  
> **Educational project only. Not a medical diagnosis tool.**  
> This system is designed solely for academic and demonstration purposes. It produces screening and detection estimates, not clinical diagnoses.

---

## Key Features

1. **User Authentication & Role-Based Access Control**:
   - Secure account registration & login with password hashing via `werkzeug.security`.
   - Distinct roles: **Doctor** vs **Student / Researcher**.
   - Doctors can record and save clinical notes attached to each scan and exported to reports.
   - Strict per-user isolation: users can only view and manage their own scans (any cross-access attempts return HTTP 404).

2. **DICOM (.dcm) & Standard Image (JPG / PNG) Ingestion**:
   - Validates file content using `pydicom.dcmread` and `PIL.Image.verify()`.
   - Converts raw DICOM pixel arrays into normalized 8-bit RGB PNGs using rescale slope/intercept, window center/width, and `MONOCHROME1` inversion.
   - Extracts `PixelSpacing` for physical millimeter sizing.
   - **Privacy First**: Patient identifiers (`PatientName`, `PatientID`, birth date) are never stored or displayed. Original `.dcm` files are discarded immediately after in-memory conversion to PNG.

3. **YOLOv8 Detection & Sizing**:
   - Uses trained weights at `models/best.pt` (the model weights are not included in this source-only repository).
   - Interactive confidence threshold slider (default 40%).
   - Brain contour estimation using Otsu thresholding on grayscale scans to compute relative tumor area `%`.
   - Physical millimeter estimation ($W \times H\text{ mm}$) when DICOM pixel spacing is present.
   - Prominent low-confidence warnings when detection confidence is under 60%.

4. **Visual Explainability (EigenCAM Heatmap)**:
   - YOLOv8 is an anchorless object detection architecture without a traditional classifier head, meaning standard gradient-based Grad-CAM cannot be applied directly.
   - We utilize **EigenCAM** (`pytorch-grad-cam`) on **Backbone Layer 8 (C2f)**. Layer 8 is the deepest feature-extraction block before spatial pooling (`SPPF`), providing high-level semantic receptive fields before feature concatenation in the neck.
   - Frontend instant toggle switches between bounding box visualization and heatmap overlay without reloading.

5. **Bilingual PDF Reports (English & Hindi)**:
   - Built using `fpdf2` with text shaping enabled via `uharfbuzz` to correctly render complex Devanagari ligatures (e.g., क्ष, त्र, ज्ञ, and matras).
   - Bundles Google Noto Sans and Noto Sans Devanagari fonts in `app/static/fonts/`.
   - Natural Hindi phrasing managed in `app/translations.py`.

---

## Project Structure

```text
Brain_tumor_detection/
├── app/
│   ├── __init__.py              # App factory (create_app), extension initialization
│   ├── config.py                # Environment configs (SECRET_KEY from env, DB URI)
│   ├── models.py                # SQLAlchemy models: User and Scan
│   ├── translations.py          # Multilingual report strings (en, hi)
│   ├── blueprints/
│   │   ├── auth/                # Auth blueprint (login, register, logout)
│   │   ├── detect/              # YOLOv8, DICOM converter, EigenCAM, sizing
│   │   ├── history/             # Scans list, notes update, record deletion
│   │   └── report/              # fpdf2 PDF report service and download route
│   ├── static/
│   │   ├── css/style.css        # Clean light theme design (#EEF4FF, Inter font)
│   │   └── fonts/               # Noto Sans Latin & Devanagari fonts
│   └── templates/               # Responsive Jinja2 templates
├── models/                      # Place best.pt here (weights are not included)
├── tests/                       # Automated pytest suite
├── uploads/                     # Runtime scan storage (created locally)
├── app.py                       # Application runner
└── requirements.txt             # Project dependencies
```

---

## Setup & Running the Application

### 1. Prerequisites
- Python 3.10+
- Virtual environment tool

### 2. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
# Windows PowerShell:
$env:SECRET_KEY="your-super-secret-key-change-this"
$env:DATABASE_URL="sqlite:///app.db"

# Linux / macOS:
export SECRET_KEY="your-super-secret-key-change-this"
export DATABASE_URL="sqlite:///app.db"
```

### 4. Run the Application
Place your trained YOLOv8 weights at `models/best.pt`. Model weights and training datasets are excluded from this source-only repository.

```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## Running the Automated Test Suite

Run pytest to execute the 5 test suites covering access control, authentication, DICOM processing, sizing math, and bilingual PDF generation:

```bash
pytest tests/
```
