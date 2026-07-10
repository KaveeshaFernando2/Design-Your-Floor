from app import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime



class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('customer','supplier','vendor','mason','delivery','admin', name='role_enum'), nullable=False, default='customer')
    phone = db.Column(db.String(30))
    city = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = db.Column(db.String(150))
    address = db.Column(db.Text)
    
    # ADD THIS RELATIONSHIP
    user = db.relationship("User", backref="supplier", uselist=False)

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    sku = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    price = db.Column(db.Numeric(12,2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    width_mm = db.Column(db.Integer)
    height_mm = db.Column(db.Integer)
    thickness_mm = db.Column(db.Integer)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total = db.Column(db.Numeric(12,2), nullable=False)
    status = db.Column(db.Enum('pending','paid','processing','shipped','delivered','cancelled', name='order_status_enum'), default='pending')
    delivery_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
        # ➤ ADD THIS (backref for Payment)
    payments = db.relationship("Payment", backref="order", lazy=True)

    # ➤ OrderItems relation (optional but recommended)
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete")

    # DELIVERY FIELDS (matching your request)
    delivery_person_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    delivery_status = db.Column(
        db.Enum('pending','assigned','out_for_delivery','delivered','failed','returned',
                name='delivery_status_enum'),
        default='pending'
    )
    delivery_assigned_at = db.Column(db.DateTime)
    delivery_completed_at = db.Column(db.DateTime)
    # In Order model
    delivery_person = db.relationship("User", foreign_keys=[delivery_person_id])
    
class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    unit_price = db.Column(db.Numeric(12,2))
    qty = db.Column(db.Integer)
    
    # Add this relationship
    product = db.relationship("Product", backref="order_items")

class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    payment_method = db.Column(db.Enum('credit_card','bank_transfer','cash_on_delivery','online_wallet', name='payment_method_enum'), default='credit_card')
    payment_status = db.Column(db.Enum('pending','successful','failed','refunded', name='payment_status_enum'), default='pending')
    transaction_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

class Installer(db.Model):
    __tablename__ = "installers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255)) 
    rating = db.Column(db.Numeric(3,2), default=0)
    completed_jobs = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    
    
    # Relationships
    user = db.relationship("User", backref="installer", lazy=True)
    bookings = db.relationship("Booking", backref="installer", lazy=True)
    gallery = db.relationship("InstallerGallery", backref="installer", lazy=True)
    
    


class InstallerGallery(db.Model):
    __tablename__ = "installer_gallery"

    id = db.Column(db.Integer, primary_key=True)
    installer_id = db.Column(db.Integer, db.ForeignKey("installers.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    installer_id = db.Column(db.Integer, db.ForeignKey("installers.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    scheduled_date = db.Column(db.DateTime)
    status = db.Column(
        db.Enum(
            'requested', 'accepted', 'in_progress', 'completed', 'cancelled',
            name='booking_status_enum'
        ),
        default='requested'
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("User", backref="bookings")       # <-- Add this
    

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




