from tests.conftest import create_sample_user
from app.models import db, Scan

def test_user_cannot_access_another_users_scan(client):
    # Create two distinct users
    user_a = create_sample_user(email='user_a@test.com', name='User A')
    user_b = create_sample_user(email='user_b@test.com', name='User B')

    # Create scan for User A
    scan_a = Scan(
        user_id=user_a.id,
        original_filename='scan_a.png',
        file_type='png',
        predicted_class='glioma',
        confidence=92.5
    )
    db.session.add(scan_a)
    db.session.commit()

    # Log in as User B
    client.post('/auth/login', data={'email': 'user_b@test.com', 'password': 'password123'})

    # User B attempts to access User A's scan via report URL
    res = client.get(f'/report/{scan_a.id}/en')
    assert res.status_code == 404

    # User B attempts to delete User A's scan
    res_del = client.post(f'/history/{scan_a.id}/delete')
    assert res_del.status_code == 404

    # Scan A must still exist in DB
    assert Scan.query.get(scan_a.id) is not None
