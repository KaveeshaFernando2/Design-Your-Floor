from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Product, Order, OrderItem, Payment
from app.models import db
from flask import Blueprint, render_template, session



from flask import Blueprint, render_template, request, url_for, send_file, current_app, abort
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from flask_login import login_required, current_user
from app.models import Product, db

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Booking, Installer, Review


customer_bp = Blueprint('customer', __name__, url_prefix='/customer')


# ------------ helper: normalize image paths ------------
def normalize_image_paths(products):
    for p in products:
        if p.image_path:
            p.image_path = p.image_path.replace('\\', '/')
    return products


# ------------------- Dashboard -------------------
@customer_bp.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    products = normalize_image_paths(products)
    return render_template('dashboards/customer_dashboard.html', products=products)


# ------------------- View All Products -------------------
from flask import request
from math import ceil

@customer_bp.route('/products')
@login_required
def products():
    # Query params
    search = request.args.get('search', '').strip()
    brand_filter = request.args.get('brand', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 12  # products per page

    # Base query
    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if brand_filter:
        query = query.filter(Product.brand == brand_filter)

    # Pagination
    total = query.count()
    pages = ceil(total / per_page)
    products = query.order_by(Product.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    products = normalize_image_paths(products)

    # Unique brands for filter dropdown
    brands = [b[0] for b in db.session.query(Product.brand).distinct()]

    return render_template(
        'dashboards/products.html',
        products=products,
        search=search,
        brand_filter=brand_filter,
        page=page,
        pages=pages,
        brands=brands
    )



# ------------------- Single Product Page -------------------
@customer_bp.route('/product/<int:id>')
@login_required
def product_detail(id):
    product = Product.query.get_or_404(id)
    if product.image_path:
        product.image_path = product.image_path.replace('\\', '/')
    return render_template('dashboards/product_detail.html', product=product)



# ------------------- ADD TO CART -------------------
@customer_bp.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for('customer.products'))

    if product.stock == 0:
        flash("This product is out of stock!", "warning")
        return redirect(url_for('customer.products'))

    # Initialize cart in session if empty
    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if str(product_id) in cart:
        cart[str(product_id)]["qty"] += 1
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.price),
            "image": product.image_path.replace("\\", "/"),
            "qty": 1
        }

    session.modified = True
    flash("Added to cart!", "success")
    return redirect(url_for('customer.products'))


# ------------------- VIEW CART -------------------
@customer_bp.route('/cart')
@login_required
def view_cart():
    cart = session.get("cart", {})

    total = sum(item["price"] * item["qty"] for item in cart.values())

    return render_template("dashboards/cart.html", cart=cart, total=total)


# ------------------- UPDATE QUANTITY -------------------
@customer_bp.route('/cart/update/<int:product_id>', methods=["POST"])
@login_required
def update_cart(product_id):
    qty = int(request.form.get("qty", 1))

    if "cart" not in session:
        return redirect(url_for('customer.view_cart'))

    cart = session["cart"]
    pid = str(product_id)

    if pid in cart:
        if qty <= 0:
            del cart[pid]
        else:
            cart[pid]["qty"] = qty

    session.modified = True
    return redirect(url_for('customer.view_cart'))


# ------------------- REMOVE ITEM -------------------
@customer_bp.route('/cart/remove/<int:product_id>')
@login_required
def remove_cart_item(product_id):
    if "cart" in session:
        cart = session["cart"]
        pid = str(product_id)

        if pid in cart:
            del cart[pid]

    session.modified = True
    return redirect(url_for('customer.view_cart'))


# ------------------- CLEAR CART -------------------
@customer_bp.route('/cart/clear')
@login_required
def clear_cart():
    session["cart"] = {}
    session.modified = True
    return redirect(url_for('customer.view_cart'))



# ------------------- Checkout -------------------
@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # cart data
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty!", "danger")
        return redirect(url_for('customer.view_cart'))

    items_total = sum(item["price"] * item["qty"] for item in cart.values())
    delivery = 1200   # example
    installation = 2500  # example
    total = items_total + delivery + installation

    if request.method == 'POST':
        address = request.form.get('address')
        payment_method = request.form.get('payment_method')

        # Create Order
        new_order = Order(
            user_id=current_user.id,
            total=total,
            delivery_address=address,
            status='pending'
        )
        db.session.add(new_order)
        db.session.commit()

        # Add Order Items
        for product_id, item in cart.items():
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=int(product_id),
                unit_price=item["price"],
                qty=item["qty"]
            )
            db.session.add(order_item)

        # Create Payment
        payment = Payment(
            order_id=new_order.id,
            user_id=current_user.id,
            amount=total,
            payment_method=payment_method,
            payment_status='pending'
        )
        db.session.add(payment)
        db.session.commit()

        # Clear cart
        session['cart'] = {}

        # If COD → Order complete
        if payment_method == "cash_on_delivery":
            flash("Order placed successfully! Pay on delivery.", "success")
            return redirect(url_for('customer.orders'))

        # Other methods → Go to payment gateway page
        return redirect(url_for('customer.payment_gateway', order_id=new_order.id))

    return render_template(
        'dashboards/checkout.html',
        items_total=items_total,
        delivery=delivery,
        installation=installation,
        total=total
    )
# ------------------- Payment Gateway (Mock) -------------------
@customer_bp.route('/payment_gateway/<int:order_id>')
@login_required
def payment_gateway(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("dashboards/payment_gateway.html", order=order)

@customer_bp.route('/payment_success/<int:order_id>', methods=['POST'])
@login_required
def payment_success(order_id):
    payment = Payment.query.filter_by(order_id=order_id).first()

    if not payment:
        abort(404)

    payment.payment_status = "successful"
    payment.transaction_id = "TXN-" + str(order_id)
    payment.order.status = "paid"

    db.session.commit()

    flash("Payment completed successfully!", "success")
    return redirect(url_for('customer.order_success', order_id=order_id))

# ------------------- Order Success -------------------
@customer_bp.route('/order_success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return "Order not found", 404

    items = OrderItem.query.filter_by(order_id=order_id).all()

    return render_template("dashboards/order_success.html", order=order, items=items)


# ------------------- My Orders -------------------

@customer_bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboards/orders.html', orders=orders)


@customer_bp.route("/order/<int:order_id>")
@login_required
def order_details(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return "Order Not Found", 404

    items = OrderItem.query.filter_by(order_id=order.id).all()

    return render_template("dashboards/order_details.html", order=order, items=items)


@customer_bp.route("/download_invoice/<int:order_id>")
@login_required
def download_invoice(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return "Not Found", 404

    items = OrderItem.query.filter_by(order_id=order.id).all()

    # Use Flask's static folder correctly
    invoice_folder = os.path.join(current_app.root_path, 'static', 'invoices')
    os.makedirs(invoice_folder, exist_ok=True)

    filename = f"invoice_{order.id}.pdf"
    filepath = os.path.join(invoice_folder, filename)

    # Generate PDF
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    c.drawString(50, y, f"Invoice for Order #{order.id}")
    y -= 30
    for item in items:
        product_name = getattr(item, 'product_name', None) or getattr(item, 'product', None) and item.product.name or "Unknown"
        c.drawString(50, y, f"{product_name} - Qty: {item.qty} - Rs.{item.unit_price}")
        y -= 20
    y -= 20
    c.drawString(50, y, f"Total: Rs. {order.total}")

    c.save()

    return send_file(filepath, as_attachment=True)





# ------------------- My Orders -------------------
@customer_bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    cart = session.get("cart", {})

    if not cart:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('customer.products'))

    # Form data
    address = request.form.get("address")

    # Calculate totals
    items_total = 0
    for pid, item in cart.items():
        items_total += float(item["price"]) * int(item["qty"])

    delivery = 1500
    installation = 3000
    grand_total = items_total + delivery + installation

    # Create Order
    new_order = Order(
        user_id=current_user.id,
        total=grand_total,
        status='pending',
        delivery_address=address
    )
    db.session.add(new_order)
    db.session.commit()  # commit to generate order.id

    # Create Order Items
    for pid, item in cart.items():
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=int(pid),
            unit_price=item["price"],
            qty=item["qty"]
        )
        db.session.add(order_item)

    db.session.commit()

    # Clear cart
    session["cart"] = {}
    session.modified = True

    flash("Order placed successfully!", "success")
    return redirect(url_for('customer.order_success', order_id=new_order.id))




# ------------------- Invoice -------------------
@customer_bp.route('/invoice/<int:order_id>')
@login_required
def invoice(order_id):
    order = Order.query.get_or_404(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()

    for i in items:
        if i.product.image_path:
            i.product.image_path = i.product.image_path.replace('\\', '/')

    return render_template('dashboards/invoice.html', order=order, items=items)



# PDF route
@customer_bp.route('/product/<int:product_id>/pdf')
def product_pdf(product_id):
    # Fetch product from DB (replace with your real query)
    product = get_product_by_id(product_id)  # implement this to return a dict/object
    if not product:
        abort(404)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 50
    y = height - margin

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, y, str(product.name))
    y -= 30

    # Basic info
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Brand: {product.brand or '-'}")
    y -= 16
    c.drawString(margin, y, f"Price: LKR {product.price}")
    y -= 16
    c.drawString(margin, y, f"Stock: {product.stock}")
    y -= 22

    # Description (wrap)
    text = c.beginText(margin, y)
    text.setFont("Helvetica", 10)
    desc = product.description or "No description available."
    for line in split_text(desc, 90):  # helper below
        text.textLine(line)
        y -= 12
    c.drawText(text)
    y = text.getY() - 10

    # Insert image if exists
    if product.image_path:
        try:
            # image stored in your static folder e.g. 'uploads/products/...'
            image_full_path = os.path.join(current_app.static_folder, product.image_path)
            if os.path.exists(image_full_path):
                img = ImageReader(image_full_path)
                # scale to fit width (A4 minus margins)
                img_w, img_h = img.getSize()
                max_w = width - 2 * margin
                max_h = 220
                scale = min(max_w / img_w, max_h / img_h, 1)
                draw_w = img_w * scale
                draw_h = img_h * scale
                c.drawImage(img, margin, y - draw_h, width=draw_w, height=draw_h)
                y -= draw_h + 12
        except Exception as e:
            current_app.logger.exception("PDF image error: %s", e)

    # Footer / generated note
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin, 30, "Generated from  Design Your Floor / Product Portal")

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"{product.name.replace(' ', '_')}.pdf",
                     mimetype='application/pdf')


# small helpers
def split_text(text, length):
    """Split text into chunks (naive, preserves words) for reportlab text lines."""
    words = text.split()
    lines, cur = [], []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) > length:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + (1 if cur else 0)
    if cur:
        lines.append(" ".join(cur))
    return lines


# placeholder: implement this to fetch product (dict or object with attributes used above)
def get_product_by_id(pid):
    prod = Product.query.get(pid)
    if not prod:
        return None
    
    # normalize image path
    if prod.image_path:
        prod.image_path = prod.image_path.replace("\\", "/")
    
    return prod

    
    
    
# --------------------------
# Book Installer
# --------------------------
@customer_bp.route("/book/<int:installer_id>", methods=["GET", "POST"])
@login_required
def book_installer(installer_id):

    installer = Installer.query.get_or_404(installer_id)

    if request.method == "POST":
        date = request.form.get("date")

        new_booking = Booking(
            customer_id=current_user.id,
            installer_id=installer.id,
            scheduled_date=date,
            status="requested"
        )
        db.session.add(new_booking)
        db.session.commit()

        flash("Booking request sent to installer!", "success")
        return redirect(url_for("customer.dashboard"))

    return render_template(
        "installers/book.html",
        installer=installer
    )
    
    
@customer_bp.route("/installers/<int:installer_id>/review/<int:booking_id>", methods=["GET", "POST"])
@login_required
def leave_review(installer_id, booking_id):
    installer = Installer.query.get_or_404(installer_id)
    booking = Booking.query.get_or_404(booking_id)

    # Only allow review if booking is completed
    if booking.customer_id != current_user.id or booking.status != "completed":
        flash("You cannot review this installer yet.", "warning")
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")
        review = Review(
            author_id=current_user.id,
            target_user_id=installer.user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash("Review submitted successfully!", "success")
        return redirect(url_for("customer.dashboard"))

    return render_template(
        "installers/review_form.html",
        installer=installer,
        booking=booking  # ⚠ Pass booking here
    )

@customer_bp.route("/submit_review/<int:booking_id>", methods=["POST"])
@login_required
def submit_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status != "completed":
        flash("You can only review after the booking is completed!", "danger")
        return redirect(url_for("customer.dashboard"))

    rating = int(request.form.get("rating"))
    comment = request.form.get("comment")

    new_review = Review(
        author_id=current_user.id,
        target_user_id=booking.installer.user_id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    flash("Review submitted successfully!", "success")
    return redirect(url_for("customer.dashboard"))


# ---------------------------------------------------------
# CUSTOMER – VIEW ALL REVIEWS THEY HAVE WRITTEN
# ---------------------------------------------------------
@customer_bp.route("/my-reviews")
@login_required
def my_reviews():
    page = request.args.get("page", 1, type=int)

    reviews_query = (
        Review.query
        .filter_by(author_id=current_user.id)
        .order_by(Review.created_at.desc())
    )

    reviews = reviews_query.paginate(page=page, per_page=5)

    # Attach installer info (target_user_id = installer's user_id)
    enriched_reviews = []
    for r in reviews.items:
        installer = Installer.query.filter_by(user_id=r.target_user_id).first()
        enriched_reviews.append({
            "review": r,
            "installer": installer
        })

    return render_template(
        "customer/my_reviews.html",
        reviews=enriched_reviews,
        pagination=reviews
    )
    
# ---------------------------
# EDIT REVIEW
# ---------------------------
@customer_bp.route("/review/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    # Only review author can edit
    if review.author_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for("customer.my_reviews"))

    if request.method == "POST":
        review.rating = request.form.get("rating")
        review.comment = request.form.get("comment")
        db.session.commit()

        flash("Review updated successfully!", "success")
        return redirect(url_for("customer.my_reviews"))

    return render_template("customer/edit_review.html", review=review)



# ---------------------------
# DELETE REVIEW
# ---------------------------
@customer_bp.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    if review.author_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for("customer.my_reviews"))

    db.session.delete(review)
    db.session.commit()

    flash("Review deleted successfully!", "success")
    return redirect(url_for("customer.my_reviews"))


@customer_bp.route('/3d-room')
def three_d_room():
    img = request.args.get("img")   # receives ?img=URL
    return render_template('dashboards/3D_Room.html', product_image=img)

@customer_bp.route('/360-room')
def three60_room():
    img = request.args.get("img")
    return render_template('dashboards/360_room.html', product_image=img)

@customer_bp.route('/360-roomwithfurniture')
def three60_room_with_furniture():
    img = request.args.get("img")
    return render_template('dashboards/360RoomPreviewwithFurniture.html', product_image=img)