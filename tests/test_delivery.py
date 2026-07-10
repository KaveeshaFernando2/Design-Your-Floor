def test_delivery_dashboard_access(client):
    res = client.get("/delivery/dashboard")
    assert res.status_code in [302, 401]
