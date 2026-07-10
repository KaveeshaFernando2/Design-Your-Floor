from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Installer, Booking, Review, InstallerGallery
from werkzeug.utils import secure_filename
import os

# Correct Blueprint
installer_bp = Blueprint("installer", __name__, url_prefix="/installer")


# ------------------------------
# Installer Dashboard
# ------------------------------
@installer_bp.route("/dashboard")
@login_required
def dashboard():

    # Get installer profile for logged-in user
    installer = Installer.query.filter_by(user_id=current_user.id).first()

    # If not registered as installer → prevent crash
    if installer is None:
        flash("You are not registered as an installer yet!", "danger")
        return redirect(url_for("main.home"))  # or auth.register

    bookings = Booking.query.filter_by(installer_id=installer.id).all()
    reviews = Review.query.filter_by(target_user_id=current_user.id).all()
    
     # Dynamically calculate completed jobs
    completed_jobs_count = Booking.query.filter_by(installer_id=installer.id, status="completed").count()

    return render_template(
        "dashboards/installer_dashboard.html",
        installer=installer,
        bookings=bookings,
        reviews=reviews,
        completed_jobs_count=completed_jobs_count
    )

    

# ------------------------------
# Update Installer Profile
# ------------------------------
@installer_bp.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    installer = Installer.query.filter_by(user_id=current_user.id).first()

    if installer is None:
        flash("Installer profile not found!", "danger")
        return redirect(url_for("installer.dashboard"))

    installer.bio = request.form.get("bio")
    db.session.commit()

    flash("Profile updated successfully!", "success")
    return redirect(url_for("installer.dashboard"))


# ------------------------------
# Upload Gallery Photos
# ------------------------------
@installer_bp.route("/upload_photo", methods=["POST"])
@login_required
def upload_photo():
    installer = Installer.query.filter_by(user_id=current_user.id).first()

    if installer is None:
        flash("Installer profile not found!", "danger")
        return redirect(url_for("installer.dashboard"))

    photo = request.files["photo"]
    filename = secure_filename(photo.filename)

    save_path = os.path.join("app/static/installer_gallery", filename)
    photo.save(save_path)

    new_img = InstallerGallery(
        installer_id=installer.id,
        image_path=f"/static/installer_gallery/{filename}"
    )

    db.session.add(new_img)
    db.session.commit()

    flash("Photo uploaded successfully!", "success")
    return redirect(url_for("installer.dashboard"))


# ------------------------------
# Accept / Cancel Booking
# ------------------------------
@installer_bp.route("/update_booking/<int:booking_id>/<status>")
@login_required
def update_booking(booking_id, status):
    booking = Booking.query.get_or_404(booking_id)
    
    # Only the installer assigned can update
    if booking.installer.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('installer.dashboard'))
    
    # Update booking status
    booking.status = status
    db.session.add(booking)

    # If booking is completed, update Installer's completed_jobs dynamically
    if status == "completed":
        installer = booking.installer
        # Count all completed bookings for this installer
        completed_count = Booking.query.filter_by(installer_id=installer.id, status="completed").count()
        installer.completed_jobs = completed_count
        db.session.add(installer)

    db.session.commit()
    flash(f"Booking status updated to {status}", "success")
    return redirect(url_for("installer.dashboard"))





# ------------------------------
# Update Profile Image
# ------------------------------
# ------------------------------
# Update Profile Image
# ------------------------------
@installer_bp.route("/update_profile_image", methods=["POST"])
@login_required
def update_profile_image():
    installer = Installer.query.filter_by(user_id=current_user.id).first()

    if installer is None:
        flash("Installer profile not found!", "danger")
        return redirect(url_for("installer.dashboard"))

    if "profile_image" not in request.files:
        flash("No file selected!", "danger")
        return redirect(url_for("installer.dashboard"))

    file = request.files["profile_image"]

    if file.filename == "":
        flash("Please select a valid image!", "warning")
        return redirect(url_for("installer.dashboard"))

    filename = secure_filename(file.filename)

    upload_folder = "app/static/profile_images"
    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)

    installer.profile_image = f"/static/profile_images/{filename}"
    db.session.commit()

    flash("Profile picture updated!", "success")
    return redirect(url_for("installer.dashboard"))




