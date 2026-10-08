"""
PDF Report Generator using fpdf2 and uharfbuzz.
Generates compliant, beautifully formatted reports in English and Hindi (Devanagari).
"""
import os
from fpdf import FPDF
from app.translations import TRANSLATIONS

class ScreeningReportPDF(FPDF):
    def __init__(self, lang='en', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang if lang in ('en', 'hi') else 'en'
        self.set_text_shaping(True)
        self.setup_fonts()

    def setup_fonts(self):
        """Register Noto Sans regular and bold fonts for Latin and Devanagari."""
        # Root app static/fonts directory
        # pdf_service.py is located at app/blueprints/report/pdf_service.py
        # so dirname(__file__) is app/blueprints/report, parent is app/blueprints, grandparent is app
        blueprints_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_dir = os.path.dirname(blueprints_dir)
        fonts_dir = os.path.join(app_dir, 'static', 'fonts')

        if self.lang == 'hi':
            self.add_font('ReportFont', '', os.path.join(fonts_dir, 'NotoSansDevanagari-Regular.ttf'))
            self.add_font('ReportFont', 'B', os.path.join(fonts_dir, 'NotoSansDevanagari-Bold.ttf'))
            self.add_font('ReportLatin', '', os.path.join(fonts_dir, 'NotoSans-Regular.ttf'))
            self.add_font('ReportLatin', 'B', os.path.join(fonts_dir, 'NotoSans-Bold.ttf'))
            self.set_fallback_fonts(['ReportLatin'])
        else:
            self.add_font('ReportFont', '', os.path.join(fonts_dir, 'NotoSans-Regular.ttf'))
            self.add_font('ReportFont', 'B', os.path.join(fonts_dir, 'NotoSans-Bold.ttf'))

    def header(self):
        # Header bar
        self.set_fill_color(238, 244, 255)  # Light theme page bg
        self.rect(0, 0, 210, 25, 'F')

        self.set_font('ReportFont', 'B', 15)
        self.set_text_color(47, 111, 237)  # Primary blue
        t = TRANSLATIONS[self.lang]
        self.set_xy(14, 6)
        self.cell(0, 8, t['title'], new_x='LMARGIN', new_y='NEXT')

        self.set_font('ReportFont', '', 9)
        self.set_text_color(91, 107, 140)  # Secondary text
        self.set_x(14)
        self.cell(0, 5, t['subtitle'], new_x='LMARGIN', new_y='NEXT')
        self.ln(6)

    def footer(self):
        self.set_y(-18)
        self.set_font('ReportFont', '', 8)
        self.set_text_color(120, 130, 150)
        self.cell(0, 8, f"NeuroScan AI  |  Page {self.page_no()}", align='C')


def generate_pdf_report(scan, user, lang='en'):
    """
    Builds the PDF report according to strict styling and content requirements.
    Never prints DICOM patient metadata.
    """
    t = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    pdf = ScreeningReportPDF(lang=lang)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. Top Metadata Grid
    pdf.set_draw_color(214, 226, 245)
    pdf.set_fill_color(255, 255, 255)
    
    pdf.set_font('ReportFont', 'B', 9)
    pdf.set_text_color(27, 42, 74)

    # Info boxes
    col1_x = 14
    col2_x = 110
    start_y = 30

    pdf.set_xy(col1_x, start_y)
    pdf.cell(32, 6, f"{t['report_id']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(60, 6, f"NS-{scan.id:05d}", 0, 1)

    pdf.set_xy(col1_x, start_y + 6)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.cell(32, 6, f"{t['date_time']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(60, 6, scan.created_at.strftime('%Y-%m-%d %H:%M UTC'), 0, 1)

    pdf.set_xy(col1_x, start_y + 12)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.cell(32, 6, f"{t['file_type']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(60, 6, f"{scan.file_type.upper()} ({scan.original_filename})", 0, 1)

    pdf.set_xy(col2_x, start_y)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.cell(35, 6, f"{t['operator_name']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(50, 6, f"{user.name}", 0, 1)

    pdf.set_xy(col2_x, start_y + 6)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.cell(35, 6, f"{t['role']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    role_str = t['doctor_role'] if user.is_doctor else t['student_role']
    pdf.cell(50, 6, role_str, 0, 1)

    pdf.set_xy(col2_x, start_y + 12)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.cell(35, 6, "AI Engine:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(50, 6, "YOLOv8 + EigenCAM", 0, 1)

    pdf.ln(12)

    # 2. Results Summary Section
    pdf.set_fill_color(248, 250, 253)
    pdf.rect(14, 52, 182, 34, 'DF')

    pdf.set_xy(18, 55)
    pdf.set_font('ReportFont', 'B', 11)
    pdf.set_text_color(47, 111, 237)
    pdf.cell(0, 6, t['results_summary'], new_x='LMARGIN', new_y='NEXT')

    pdf.set_xy(18, 63)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.set_text_color(27, 42, 74)
    pdf.cell(50, 6, f"{t['detected_class']}:", 0, 0)
    pdf.set_font('ReportFont', 'B', 10)
    if scan.predicted_class == 'No tumor detected':
        pdf.set_text_color(15, 110, 86)
        pred_label = t['no_tumor_detected']
    else:
        pdf.set_text_color(226, 75, 74)
        pred_label = scan.predicted_class.capitalize()
    pdf.cell(40, 6, pred_label, 0, 0)

    pdf.set_font('ReportFont', 'B', 9)
    pdf.set_text_color(27, 42, 74)
    pdf.cell(45, 6, f"{t['confidence']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    pdf.cell(30, 6, f"{scan.confidence:.1f}%", 0, 1)

    # Sizing
    pdf.set_xy(18, 71)
    pdf.set_font('ReportFont', 'B', 9)
    pdf.set_text_color(27, 42, 74)
    pdf.cell(50, 6, f"{t['estimated_size']}:", 0, 0)
    pdf.set_font('ReportFont', '', 9)
    size_text = f"{scan.tumor_area_percent:.2f}% (Relative)" if scan.tumor_area_percent is not None else "N/A"
    if scan.tumor_size_mm:
        size_text += f" | {scan.tumor_size_mm}"
    pdf.cell(0, 6, size_text, 0, 1)

    pdf.set_xy(14, 90)

    # 3. Low Confidence Warning Banner if applicable
    if scan.confidence < 60.0 and scan.predicted_class != 'No tumor detected':
        pdf.set_fill_color(254, 247, 230)
        pdf.set_draw_color(249, 226, 175)
        pdf.rect(14, 90, 182, 10, 'DF')
        pdf.set_xy(18, 92)
        pdf.set_font('ReportFont', 'B', 8)
        pdf.set_text_color(183, 129, 3)
        pdf.cell(174, 6, t['low_conf_warning'], 0, 1)
        pdf.set_xy(14, 104)
    else:
        pdf.set_xy(14, 90)

    # 4. Screening Visualizations (Annotated & Heatmap)
    curr_y = pdf.get_y() + 4
    pdf.set_font('ReportFont', 'B', 11)
    pdf.set_text_color(27, 42, 74)
    pdf.set_xy(14, curr_y)
    pdf.cell(0, 6, t['images_title'], new_x='LMARGIN', new_y='NEXT')
    curr_y += 8

    from flask import current_app
    upload_dir = current_app.config['UPLOAD_FOLDER']

    has_annotated = scan.annotated_image_path and os.path.exists(os.path.join(upload_dir, scan.annotated_image_path))
    has_heatmap = scan.heatmap_image_path and os.path.exists(os.path.join(upload_dir, scan.heatmap_image_path))

    img_w = 85
    img_h = 75

    if has_annotated and has_heatmap:
        # Side by side
        ann_path = os.path.join(upload_dir, scan.annotated_image_path)
        hm_path = os.path.join(upload_dir, scan.heatmap_image_path)
        pdf.image(ann_path, x=14, y=curr_y, w=img_w, h=img_h)
        pdf.image(hm_path, x=111, y=curr_y, w=img_w, h=img_h)

        pdf.set_font('ReportFont', '', 8)
        pdf.set_text_color(91, 107, 140)
        pdf.set_xy(14, curr_y + img_h + 1)
        pdf.cell(img_w, 4, t['annotated_box'], align='C')
        pdf.set_xy(111, curr_y + img_h + 1)
        pdf.cell(img_w, 4, t['heatmap_overlay'], align='C')
        curr_y += img_h + 8
    elif has_annotated:
        ann_path = os.path.join(upload_dir, scan.annotated_image_path)
        pdf.image(ann_path, x=62, y=curr_y, w=img_w, h=img_h)
        pdf.set_font('ReportFont', '', 8)
        pdf.set_text_color(91, 107, 140)
        pdf.set_xy(62, curr_y + img_h + 1)
        pdf.cell(img_w, 4, t['annotated_box'], align='C')
        curr_y += img_h + 8

    # 5. Doctor Clinical Notes (Doctors only)
    if user.is_doctor:
        pdf.set_xy(14, curr_y)
        pdf.set_font('ReportFont', 'B', 10)
        pdf.set_text_color(27, 42, 74)
        pdf.cell(0, 6, t['clinical_notes_title'], new_x='LMARGIN', new_y='NEXT')
        curr_y += 6

        notes_content = scan.clinical_notes.strip() if scan.clinical_notes else t['no_notes']
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(214, 226, 245)
        pdf.rect(14, curr_y, 182, 18, 'DF')
        pdf.set_xy(18, curr_y + 2)
        pdf.set_font('ReportFont', '', 8.5)
        pdf.set_text_color(40, 50, 70)
        pdf.multi_cell(174, 4.5, notes_content)
        curr_y += 22

    # 6. Important Legal / Educational Disclaimer
    pdf.set_xy(14, curr_y)
    pdf.set_fill_color(255, 249, 235)
    pdf.set_draw_color(254, 229, 181)
    pdf.rect(14, curr_y, 182, 22, 'DF')

    pdf.set_xy(18, curr_y + 2)
    pdf.set_font('ReportFont', 'B', 8.5)
    pdf.set_text_color(146, 64, 14)
    pdf.cell(0, 4.5, t['disclaimer_title'], new_x='LMARGIN', new_y='NEXT')

    pdf.set_xy(18, curr_y + 7)
    pdf.set_font('ReportFont', '', 7.5)
    pdf.multi_cell(174, 4, t['disclaimer_body'])

    return pdf.output()
