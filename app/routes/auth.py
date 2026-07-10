from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User, Supplier,Installer
from app.forms import RegistrationForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --------------------------
# User loader
# --------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------
# Login route
# --------------------------
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully!", "success")

            # Redirect based on role
            if user.role == 'customer':
                return redirect(url_for('customer.dashboard'))
            elif user.role == 'supplier':
                return redirect(url_for('supplier.dashboard'))
            elif user.role == 'mason':
                return redirect(url_for('installer.dashboard'))
            elif user.role == 'delivery':
                return redirect(url_for('delivery.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

# --------------------------
# Logout route
# --------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('main.home'))

# --------------------------
# Registration route
# --------------------------
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('auth.register'))

        # Create new user
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            phone=form.phone.data,
            city=form.city.data
        )
        db.session.add(user)
        db.session.commit()  # commit to generate user.id

        # Supplier creation
        if user.role == 'supplier':
            if not form.company_name.data or not form.address.data:
                flash("Company Name and Address are required for suppliers.", "danger")
                db.session.delete(user)
                db.session.commit()
                return redirect(url_for('auth.register'))

            supplier = Supplier(
                user_id=user.id,
                company_name=form.company_name.data,
                address=form.address.data
            )
            db.session.add(supplier)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                db.session.delete(user)
                db.session.commit()
                flash(f"Error creating supplier profile: {str(e)}", "danger")
                return redirect(url_for('auth.register'))

        # Installer (mason) creation
        if user.role == 'mason':
            installer = Installer(
                user_id=user.id,
                bio="",          # Optional: you can let user fill later
                rating=0,
                completed_jobs=0,
                verified=False
            )
            db.session.add(installer)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                db.session.delete(user)
                db.session.commit()
                flash(f"Error creating installer profile: {str(e)}", "danger")
                return redirect(url_for('auth.register'))

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)
