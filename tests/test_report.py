import re

from tests.conftest import create_sample_user
from app.models import db, Scan
from app.blueprints.report.pdf_service import generate_pdf_report

def test_pdf_report_generation_both_languages(app):
    with app.app_context():
        user = create_sample_user(email='doctor@test.com', role='doctor', name='Dr. Elena Rostova')
        scan = Scan(
            user_id=user.id,
            original_filename='brain_mri.jpg',
            file_type='jpg',
            predicted_class='glioma',
            confidence=88.5,
            tumor_area_percent=12.4,
            tumor_size_mm='24.0 mm x 18.5 mm (Approx)',
            clinical_notes='Hyperintense mass observed in frontal lobe.'
        )
        db.session.add(scan)
        db.session.commit()

        # 1. English PDF
        pdf_en = generate_pdf_report(scan, user, lang='en')
        assert pdf_en is not None
        assert len(pdf_en) > 1000
        assert pdf_en.startswith(b'%PDF-')

        # 2. Hindi PDF
        pdf_hi = generate_pdf_report(scan, user, lang='hi')
        assert pdf_hi is not None
        assert len(pdf_hi) > 1000
        assert pdf_hi.startswith(b'%PDF-')
        assert b'NotoSansDevanagari' in pdf_hi
        assert re.search(rb'/BaseFont /[A-Z]{6}\+NotoSans(?:\r?\n)', pdf_hi)
