def test_supplier_dashboard_requires_login(client):
    res = client.get("/supplier/dashboard")
    assert res.status_code in [302, 401]

def test_add_product_page(client):
    res = client.get("/supplier/add-product")
    assert res.status_code in [302, 401]
