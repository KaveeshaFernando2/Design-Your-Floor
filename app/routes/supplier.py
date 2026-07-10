from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Product, Supplier, Order, OrderItem, User
from datetime import datetime
import os
from flask import current_app
from werkzeug.utils import secure_filename

from sqlalchemy import func, desc
import calendar
from datetime import datetime, timedelta
from flask import send_file
import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from flask import send_file
from io import BytesIO

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@supplier_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'supplier':
        flash("Access denied!")
        return redirect(url_for('main.home'))
    
    # Fetch supplier profile
    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("No supplier profile found. Contact admin.", "danger")
        return redirect(url_for('main.home'))

    # Fetch all products added by this supplier
    products = Product.query.filter_by(supplier_id=supplier.id).all()

    # **Normalize image paths to use forward slashes**
    for product in products:
        if product.image_path:
            product.image_path = product.image_path.replace('\\', '/')

    return render_template('dashboards/supplier_dashboard.html', products=products)


@supplier_bp.route('/add-product', methods=['GET','POST'])
@login_required
def add_product():
    if current_user.role != 'supplier':
        flash("Access denied!")
        return redirect(url_for('main.home'))

    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("No supplier profile found. Contact admin.", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        # Get data from form
        sku = request.form['sku']
        name = request.form['name']
        description = request.form['description']
        brand = request.form['brand']
        price = request.form['price']
        stock = request.form['stock']
        width_mm = request.form['width_mm']
        height_mm = request.form['height_mm']
        thickness_mm = request.form['thickness_mm']

        # Handle file upload with validation
        image_file = request.files.get('image_file')
        image_path = None
        if image_file and image_file.filename != '':
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('images', filename)
                save_path = os.path.join(current_app.static_folder, 'images', filename)
                image_file.save(save_path)
            else:
                flash("Invalid file type. Allowed types: png, jpg, jpeg, gif", "danger")
                return redirect(request.url)

        # Save product
        product = Product(
            supplier_id=supplier.id,
            sku=sku,
            name=name,
            description=description,
            brand=brand,
            price=price,
            stock=stock,
            width_mm=width_mm,
            height_mm=height_mm,
            thickness_mm=thickness_mm,
            image_path=image_path
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully!")
        return redirect(url_for('supplier.dashboard'))

    return render_template('dashboards/add_product.html')


@supplier_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        # Update basic fields
        product.sku = request.form['sku']
        product.name = request.form['name']
        product.description = request.form['description']
        product.brand = request.form['brand']
        product.price = request.form['price']
        product.stock = request.form['stock']
        product.width_mm = request.form['width_mm']
        product.height_mm = request.form['height_mm']
        product.thickness_mm = request.form['thickness_mm']

        # Handle image upload
        image_file = request.files.get('image_file')

        if image_file and image_file.filename != '':
            if allowed_file(image_file.filename):

                # Save new image
                filename = secure_filename(image_file.filename)
                new_image_path = os.path.join('images', filename)
                save_path = os.path.join(current_app.static_folder, 'images', filename)
                image_file.save(save_path)

                # Update DB path
                product.image_path = new_image_path.replace('\\', '/')

            else:
                flash("Invalid file type. Allowed: png, jpg, jpeg, gif", "danger")
                return redirect(request.url)

        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for('supplier.dashboard'))

    # Normalize path for preview
    if product.image_path:
        product.image_path = product.image_path.replace('\\', '/')

    return render_template('dashboards/edit_product.html', product=product)



@supplier_bp.route('/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)

    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted successfully!", "success")  # ✅ Flash message
    
    return redirect(url_for('supplier.dashboard'))


@supplier_bp.route('/view/<int:id>')
@login_required
def view_product(id):
    product = Product.query.get_or_404(id)

    # Normalize path
    if product.image_path:
        product.image_path = product.image_path.replace('\\', '/')

    return render_template('dashboards/view_product.html', product=product)


@supplier_bp.route('/orders')
@login_required
def supplier_orders():
    if current_user.role != 'supplier':
        flash("Access denied!")
        return redirect(url_for('main.home'))

    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("Supplier profile not found!", "danger")
        return redirect(url_for('main.home'))

    # 🔥 Supplier products list
    supplier_products = Product.query.filter_by(supplier_id=supplier.id).all()
    supplier_product_ids = [p.id for p in supplier_products]

    # 🔥 Orders containing supplier products
    orders = Order.query.join(Order.items).filter(
        OrderItem.product_id.in_(supplier_product_ids)
    ).all()

    # 🔥 Delivery people list
    delivery_people = User.query.filter_by(role="delivery").all()

    return render_template(
        'dashboards/supplier_orders.html',
        orders=orders,
        users=delivery_people
    )

@supplier_bp.route('/assign-delivery/<int:order_id>', methods=['POST'])
@login_required
def assign_delivery(order_id):
    if current_user.role != 'supplier':
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))

    order = Order.query.get_or_404(order_id)
    delivery_person_id = request.form.get("delivery_person")

    if not delivery_person_id:
        flash("Please select a delivery person!", "danger")
        return redirect(url_for('supplier.supplier_orders'))

    order.delivery_person_id = delivery_person_id
    order.delivery_status = 'assigned'
    order.delivery_assigned_at = datetime.utcnow()

    db.session.commit()
    flash("Delivery assigned successfully!", "success")
    return redirect(url_for('supplier.supplier_orders'))

@supplier_bp.route('/update-delivery/<int:order_id>', methods=['POST'])
@login_required
def update_delivery(order_id):
    new_status = request.form.get("status")

    order = Order.query.get_or_404(order_id)

    order.delivery_status = new_status
    if new_status == "delivered":
        order.delivery_completed_at = datetime.utcnow()

    db.session.commit()

    flash("Delivery status updated!", "success")
    return redirect(url_for('supplier.supplier_orders'))

@supplier_bp.route('/delivery-orders')
@login_required
def delivery_orders():
    if current_user.role != 'supplier':
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))

    # Get supplier profile
    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("Supplier profile not found!", "danger")
        return redirect(url_for('main.home'))

    # Get all products of this supplier
    supplier_products = Product.query.filter_by(supplier_id=supplier.id).all()
    supplier_product_ids = [p.id for p in supplier_products]

    # Get all orders for these products that have been assigned to delivery
    orders = (
        Order.query
        .join(Order.items)
        .filter(
            OrderItem.product_id.in_(supplier_product_ids),
            Order.delivery_person_id.isnot(None)  # only assigned deliveries
        )
        .all()
    )

    return render_template('dashboards/supplier_delivery_orders.html', orders=orders)

# -------------------------
# Supplier Analytics
# -------------------------
@supplier_bp.route('/analytics')
@login_required
def analytics():
    if current_user.role != 'supplier':
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))

    # get supplier
    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("Supplier profile not found!", "danger")
        return redirect(url_for('main.home'))

    # supplier product ids
    supplier_products = Product.query.filter_by(supplier_id=supplier.id).all()
    supplier_product_ids = [p.id for p in supplier_products]

    # If supplier has no products, return empty / zeroed dashboard
    if not supplier_product_ids:
        return render_template('dashboards/supplier_analytics.html',
                               supplier=supplier,
                               total_revenue=0,
                               total_orders=0,
                               avg_order_value=0,
                               top_products=[],
                               monthly_labels=[],
                               monthly_values=[],
                               low_stock=[],
                               delivery_stats={},
                               pie_labels=[],
                               pie_values=[]
                               )

    # -------- KPIs --------
    total_revenue = db.session.query(
        func.coalesce(func.sum(OrderItem.unit_price * OrderItem.qty), 0)
    ).join(Order, OrderItem.order_id == Order.id) \
     .filter(OrderItem.product_id.in_(supplier_product_ids)).scalar() or 0

    total_orders = db.session.query(func.count(func.distinct(Order.id))) \
        .join(OrderItem, OrderItem.order_id == Order.id) \
        .filter(OrderItem.product_id.in_(supplier_product_ids)).scalar() or 0

    avg_order_value = float(total_revenue) / int(total_orders) if total_orders else 0.0

    # -------- Top products --------
    top_products_q = db.session.query(
        Product.id,
        Product.name,
        func.coalesce(func.sum(OrderItem.qty), 0).label('qty_sold'),
        func.coalesce(func.sum(OrderItem.qty * OrderItem.unit_price), 0).label('revenue')
    ).join(OrderItem, OrderItem.product_id == Product.id) \
     .filter(Product.id.in_(supplier_product_ids)) \
     .group_by(Product.id, Product.name) \
     .order_by(desc('qty_sold')) \
     .limit(8).all()

    top_products_list = [{
        "id": p.id,
        "name": p.name,
        "qty_sold": int(p.qty_sold or 0),
        "revenue": float(p.revenue or 0)
    } for p in top_products_q]

    # -------- Pie Chart Data --------
    top_products_for_pie = db.session.query(
        Product.name,
        func.coalesce(func.sum(OrderItem.qty), 0).label("qty_sold")
    ).join(OrderItem, Product.id == OrderItem.product_id) \
     .filter(Product.supplier_id == supplier.id) \
     .group_by(Product.id, Product.name) \
     .order_by(desc("qty_sold")) \
     .limit(5).all()

    pie_labels = [row[0] for row in top_products_for_pie]
    pie_values = [int(row[1]) for row in top_products_for_pie]

    # -------- Monthly sales last 6 months --------
    def month_delta(dt, delta):
        m = dt.month - 1 + delta
        y = dt.year + m // 12
        m = m % 12 + 1
        return datetime(y, m, 1)

    today = datetime.utcnow()
    monthly_labels = []
    monthly_values = []
    for delta in range(-5, 1):
        start = month_delta(today, delta)
        end = month_delta(today, delta + 1)
        monthly_labels.append(start.strftime("%b %Y"))

        month_sum = db.session.query(
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.qty), 0)
        ).join(Order, OrderItem.order_id == Order.id) \
         .filter(
             OrderItem.product_id.in_(supplier_product_ids),
             Order.created_at >= start,
             Order.created_at < end
         ).scalar() or 0
        monthly_values.append(float(month_sum))

    # -------- Low stock --------
    LOW_STOCK_THRESHOLD = 5
    low_stock_q = Product.query.filter(
        Product.supplier_id == supplier.id,
        Product.stock <= LOW_STOCK_THRESHOLD
    ).order_by(Product.stock.asc()).all()

    low_stock_list = [{"id": p.id, "name": p.name, "stock": int(p.stock or 0)} for p in low_stock_q]

    # -------- Delivery stats --------
    delivery_stats_q = db.session.query(
        Order.delivery_status,
        func.count(Order.id)
    ).join(OrderItem, Order.id == OrderItem.order_id) \
     .filter(OrderItem.product_id.in_(supplier_product_ids)) \
     .group_by(Order.delivery_status).all()

    delivery_stats_dict = {row[0]: int(row[1]) for row in delivery_stats_q}

    return render_template(
        'dashboards/supplier_analytics.html',
        supplier=supplier,
        total_revenue=float(total_revenue),
        total_orders=int(total_orders),
        avg_order_value=float(avg_order_value),
        top_products=top_products_list,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        low_stock=low_stock_list,
        delivery_stats=delivery_stats_dict,
        pie_labels=pie_labels,
        pie_values=pie_values
    )

# -------------------------
# Export Excel
# -------------------------
# -------------------------
# Export Excel (real supplier data)
# -------------------------
@supplier_bp.route('/analytics/download_excel')
@login_required
def download_analytics_excel():
    if current_user.role != 'supplier':
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))

    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("Supplier profile not found!", "danger")
        return redirect(url_for('main.home'))

    products = Product.query.filter_by(supplier_id=supplier.id).all()
    
    # Prepare data for Excel
    data = []
    for p in products:
        sold_qty = db.session.query(func.coalesce(func.sum(OrderItem.qty), 0)) \
                    .filter(OrderItem.product_id==p.id).scalar() or 0
        revenue = db.session.query(func.coalesce(func.sum(OrderItem.qty * OrderItem.unit_price), 0)) \
                    .filter(OrderItem.product_id==p.id).scalar() or 0
        data.append({
            "Product Name": p.name,
            "Stock": p.stock,
            "Quantity Sold": int(sold_qty),
            "Revenue (Rs.)": float(revenue)
        })

    df = pd.DataFrame(data)

    # Create in-memory Excel
    output = BytesIO()
    
    # Use context manager to ensure writer is properly closed
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Top Products')
    except ModuleNotFoundError:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Top Products')

    output.seek(0)  # Go back to the start of the file

    return send_file(
        output,
        download_name="supplier_analytics.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



# -------------------------
# Export PDF
# -------------------------
# -------------------------
# Export PDF (no external font needed)
# -------------------------

def pdf_safe(text: str) -> str:
    """
    Remove or convert unsupported characters so FPDF won't crash.
    """
    replacements = {
        "–": "-",   # en dash
        "—": "-",   # em dash
        "•": "-",   # bullet
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "•": "-", 
        "₹": "Rs."  # just in case
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # remove any remaining unsupported unicode safely
    return text.encode('latin-1', 'replace').decode('latin-1')


@supplier_bp.route('/analytics/download/pdf')
@login_required
def download_analytics_pdf():
    supplier = Supplier.query.filter_by(user_id=current_user.id).first()
    if not supplier:
        flash("Supplier not found!", "danger")
        return redirect(url_for('supplier.analytics'))

    pdf = FPDF()
    pdf.add_page()
    
    # HEADER
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, pdf_safe("Supplier Analytics Report"), 0, 1, 'C')

    pdf.ln(4)
    pdf.set_font("Arial", '', 12)

    products = Product.query.filter_by(supplier_id=supplier.id).all()
    for p in products:
        sold_qty = db.session.query(func.coalesce(func.sum(OrderItem.qty), 0)) \
                        .filter(OrderItem.product_id == p.id).scalar() or 0
        revenue = db.session.query(
                    func.coalesce(func.sum(OrderItem.qty * OrderItem.unit_price), 0)
                 ).filter(OrderItem.product_id == p.id).scalar() or 0
        
        line = f"{p.name} | Stock: {p.stock} | Sold: {sold_qty} | Revenue: Rs. {revenue:.2f}"
        pdf.cell(0, 8, pdf_safe(line), 0, 1)

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, as_attachment=True,
                     download_name="supplier_analytics.pdf",
                     mimetype="application/pdf")
