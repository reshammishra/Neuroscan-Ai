import os
import io
import pytest
import numpy as np
from PIL import Image
import pydicom
from pydicom.dataset import Dataset, FileDataset
from app import create_app, db
from app.models import User, Scan
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

@pytest.fixture
def app():
    test_app = create_app(TestConfig)
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def create_sample_user(email='test@example.com', password='password123', role='student', name='Test User'):
    user = User(email=email, role=role, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def create_dummy_dicom(pixel_spacing=(0.5, 0.5)):
    """Creates an in-memory valid DICOM file."""
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'  # Implicit VR Little Endian

    ds = FileDataset("test.dcm", {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientName = "SensitiveName^Secret"
    ds.PatientID = "SECRET-12345"
    ds.Rows = 64
    ds.Columns = 64
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    if pixel_spacing:
        ds.PixelSpacing = list(pixel_spacing)

    # Pixel array
    arr = (np.ones((64, 64), dtype=np.uint16) * 1000)
    ds.PixelData = arr.tobytes()

    buf = io.BytesIO()
    ds.save_as(buf)
    buf.seek(0)
    return buf
