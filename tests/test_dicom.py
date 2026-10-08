import os
from PIL import Image
from tests.conftest import create_dummy_dicom
from app.blueprints.detect.dicom_utils import is_valid_image_file, process_dicom_file

def test_dicom_to_png_conversion_and_privacy(tmp_path):
    dcm_stream = create_dummy_dicom(pixel_spacing=(0.75, 0.75))

    # Test validation
    valid, ext = is_valid_image_file(dcm_stream, 'sample.dcm')
    assert valid is True
    assert ext == 'dcm'

    # Test conversion to PNG
    output_png = str(tmp_path / 'converted.png')
    pixel_spacing, err = process_dicom_file(dcm_stream, output_png)

    assert err is None
    assert pixel_spacing == (0.75, 0.75)
    assert os.path.exists(output_png)

    # Verify converted image is valid RGB PNG
    with Image.open(output_png) as img:
        assert img.format == 'PNG'
        assert img.mode == 'RGB'
        assert img.size == (64, 64)
