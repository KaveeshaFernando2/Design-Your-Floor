def test_register_user(client):
    res = client.post("/register", data={
        "username": "testuser",
        "email": "test@test.com",
        "password": "123456",
        "confirm_password": "123456"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Login" in res.data

def test_login_user(client):
    client.post("/register", data={
        "username": "testuser",
        "email": "test@test.com",
        "password": "123456",
        "confirm_password": "123456"
    })

    res = client.post("/login", data={
        "email": "test@test.com",
        "password": "123456"
    }, follow_redirects=True)

    assert res.status_code == 200
