from tests.conftest import create_sample_user
from app.models import User

def test_registration_and_login(client):
    # 1. Register new user
    res = client.post('/auth/register', data={
        'name': 'Dr. Alice Smith',
        'email': 'alice@hospital.com',
        'role': 'doctor',
        'password': 'strongpassword',
        'confirm_password': 'strongpassword'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Your account has been created!' in res.data

    user = User.query.filter_by(email='alice@hospital.com').first()
    assert user is not None
    assert user.is_doctor is True

    # 2. Login
    res = client.post('/auth/login', data={
        'email': 'alice@hospital.com',
        'password': 'strongpassword'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back, Dr. Alice Smith!' in res.data
    assert b'Log out' in res.data

    # 3. Logout
    res = client.get('/auth/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'You have been logged out.' in res.data


def test_duplicate_email_points_user_to_login(client):
    create_sample_user(email='existing@example.com')

    res = client.post('/auth/register', data={
        'name': 'Another User',
        'email': 'Existing@Example.com',
        'role': 'student',
        'password': 'strongpassword',
        'confirm_password': 'strongpassword'
    })

    assert res.status_code == 200
    assert b'An account with this email address already exists. Please log in instead.' in res.data
    assert User.query.filter_by(email='existing@example.com').count() == 1


def test_language_switch_persists_and_translates_registration(client):
    res = client.post(
        '/language',
        data={'language': 'hi'},
        headers={'Referer': 'http://localhost.localdomain/auth/register'}
    )

    assert res.status_code == 302
    assert res.headers['Location'] == 'http://localhost.localdomain/auth/register'

    res = client.get('/auth/register')
    assert res.status_code == 200
    assert 'हिन्दी'.encode() in res.data
    assert 'खाता बनाएँ'.encode() in res.data
