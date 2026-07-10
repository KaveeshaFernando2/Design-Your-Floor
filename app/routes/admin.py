from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import *
from app import db
from sqlalchemy import func, desc
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ----------------------
# ADMIN DASHBOARD
# ----------------------
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('main.home'))

    # Total stats
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(
        func.coalesce(func.sum(Order.total), 0)
    ).scalar()

    # New users in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = User.query.filter(User.created_at >= week_ago).count()

    # Order status chart
    order_status_q = db.session.query(
        Order.status, func.count(Order.id)
    ).group_by(Order.status).all()

    order_status_labels = [row[0] for row in order_status_q]
    order_status_values = [int(row[1]) for row in order_status_q]

    # Best selling products
    top_products_q = db.session.query(
        Product.name,
        func.sum(OrderItem.qty).label('qty')
    ).join(OrderItem).group_by(Product.id).order_by(desc('qty')).limit(5).all()

    top_products_labels = [p[0] for p in top_products_q]
    top_products_values = [int(p[1]) for p in top_products_q]

    # Low stock alert
    low_stock = Product.query.filter(Product.stock <= 5).all()
    
    # Recent orders
    orders = Order.query.order_by(Order.id.desc()).limit(10).all()
    
    # Suppliers, installers
    suppliers = Supplier.query.limit(10).all()
    installers = Installer.query.limit(10).all()

    return render_template("dashboards/admin_dashboard.html",
                           total_users=total_users,
                           total_orders=total_orders,
                           total_revenue=float(total_revenue),
                           new_users=new_users,
                           order_status_labels=order_status_labels,
                           order_status_values=order_status_values,
                           top_products_labels=top_products_labels,
                           top_products_values=top_products_values,
                           low_stock=low_stock,
                           orders=orders,
                           suppliers=suppliers,
                           installers=installers)

# -------------------------
# Admin Excel Export
# -------------------------
@admin_bp.route('/dashboard/download/excel')
@login_required
def dashboard_excel():
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for('main.home'))

    # Fetch all users
    users = User.query.all()

    # Prepare data
    data = [{
        "Full Name": u.full_name,
        "Email": u.email,
        "Role": u.role,
        "Created": u.created_at.strftime("%Y-%m-%d")
    } for u in users]

    df = pd.DataFrame(data)

    # Create Excel in memory
    output = BytesIO()
    
    # Use context manager and fallback for engines
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Users")
    except ModuleNotFoundError:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Users")

    output.seek(0)  # Go back to start of the file

    return send_file(
        output,
        download_name="admin_report.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@admin_bp.route('/dashboard/download/pdf')
@login_required
def dashboard_pdf():
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for('main.home'))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Admin Report", 0, 1, 'C')

    pdf.set_font("Arial", '', 12)

    users = User.query.all()
    pdf.ln(5)
    pdf.cell(0, 10, "User Accounts", 0, 1)

    for u in users:
        pdf.cell(0, 8,
                 f"{u.full_name} | {u.email} | {u.role}",
                 0, 1)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    return send_file(output,
                     download_name="admin_report.pdf",
                     as_attachment=True,
                     mimetype="application/pdf")
