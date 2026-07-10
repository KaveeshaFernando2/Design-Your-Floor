from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Order
from datetime import datetime

delivery_bp = Blueprint('delivery', __name__, url_prefix='/delivery')


# ⭐ DELIVERY DASHBOARD (SHOW ASSIGNED + AVAILABLE ORDERS)
@delivery_bp.route('/dashboard')
@login_required
def dashboard():

    # Orders that are not yet assigned to a delivery person
    unassigned_orders = Order.query.filter(
        Order.status.in_(["processing", "shipped"]),
        Order.delivery_status == "pending"
    ).all()

    # Orders already assigned to this delivery person
    my_orders = Order.query.filter_by(delivery_person_id=current_user.id).all()

    return render_template(
        'dashboards/delivery_dashboard.html',
        unassigned_orders=unassigned_orders,
        my_orders=my_orders
    )


# ⭐ ACCEPT ORDER
@delivery_bp.route('/assign/<int:order_id>', methods=['POST'])
@login_required
def assign_order(order_id):
    order = Order.query.get_or_404(order_id)

    if order.delivery_status != "pending":
        flash("This order is already assigned.", "warning")
        return redirect(url_for('delivery.dashboard'))

    order.delivery_person_id = current_user.id
    order.delivery_status = "assigned"
    order.delivery_assigned_at = datetime.utcnow()

    db.session.commit()
    flash("Order assigned successfully!", "success")
    return redirect(url_for('delivery.dashboard'))


# ⭐ START DELIVERY
@delivery_bp.route('/start/<int:order_id>', methods=['POST'])
@login_required
def start_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    order.delivery_status = "out_for_delivery"
    db.session.commit()
    flash("Delivery started!", "info")
    return redirect(url_for('delivery.dashboard'))


# ⭐ COMPLETE DELIVERY
@delivery_bp.route('/complete/<int:order_id>', methods=['POST'])
@login_required
def complete_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    order.delivery_status = "delivered"
    order.delivery_completed_at = datetime.utcnow()
    order.status = "delivered"  # update main order status
    db.session.commit()
    flash("Order delivered successfully!", "success")
    return redirect(url_for('delivery.dashboard'))


# ⭐ MARK FAILED
@delivery_bp.route('/failed/<int:order_id>', methods=['POST'])
@login_required
def failed_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    order.delivery_status = "failed"
    db.session.commit()
    flash("Order marked as failed!", "danger")
    return redirect(url_for('delivery.dashboard'))
