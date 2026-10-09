---
title: NeuroScan AI
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

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
   - Uses trained weights at `models/best.pt`.
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
├── models/                      # Trained best.pt weights
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
The trained YOLOv8 weights are stored at `models/best.pt`. Training datasets and other model checkpoints are excluded from this repository.

```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## Deploying on Hugging Face Spaces

This Flask application uses the Docker SDK on Hugging Face Spaces.

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space) and select **Docker** as the Space SDK.
2. Push this repository's source to the new Space's Git repository. Do not push the local virtual environment, databases, uploads, or training datasets.
3. Push the repository, including `models/best.pt`, to the Space repository. Training datasets and other model checkpoints should not be pushed.
4. In the Space settings, add a `SECRET_KEY` secret with a long, randomly generated value.
5. Wait for the Docker build to finish, then open the Space URL.

The Space runs on CPU by default. The SQLite database and uploaded scans are configured under `/data`; this directory is ephemeral unless persistent storage is enabled for the Space. Without persistent storage, account and scan data can be lost when the Space restarts. This project handles medical images, so use only synthetic or properly de-identified scans in a public demo.

---

## Deploying on Render

This repository includes a Render Blueprint (`render.yaml`) for deploying the Flask app as a Docker web service.

1. Sign in to [Render](https://render.com/) and choose **New > Blueprint**.
2. Connect the GitHub repository and select the branch to deploy. Render reads `render.yaml` and creates the web service on the Free plan.
3. Wait for the Docker build and deployment to complete, then open the service URL.
4. The repository includes `models/best.pt`, so Render's Docker build can load the model. The weights will be public wherever this repository is public.

The Free web service spins down after 15 minutes without traffic and may take about a minute to start on the next request. Its filesystem is ephemeral: the SQLite database and uploaded scans can be lost on restart, redeploy, or spin-down. Persistent disks require a paid plan. Do not use the free service for production or store real patient scans; use only synthetic or properly de-identified images in a public demo.

---

## Running the Automated Test Suite

Run pytest to execute the 5 test suites covering access control, authentication, DICOM processing, sizing math, and bilingual PDF generation:

```bash
pytest tests/
```
