import numpy as np
from app.blueprints.detect.yolo_service import estimate_brain_area

def test_size_estimate_function():
    # Synthetic image: 200x200 black background with a 100x100 white square in middle
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[50:150, 50:150] = 255

    brain_area = estimate_brain_area(img)
    # Expected area should be approximately 100 * 100 = 10,000 px
    assert 9000 <= brain_area <= 11000

    # Total area fallback check on completely blank image
    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    fallback_area = estimate_brain_area(blank)
    assert fallback_area == 10000.0
