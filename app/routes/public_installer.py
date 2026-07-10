from flask import Blueprint, render_template
from app.models import Installer, InstallerGallery, User, Booking

public_installer_bp = Blueprint("public_installer", __name__, url_prefix="/installers")

# List all installers
from flask_login import current_user

@public_installer_bp.route("/")
def list_installers():
    installers = Installer.query.all()

    customer_bookings = []
    if current_user.is_authenticated:
        customer_bookings = Booking.query.filter_by(customer_id=current_user.id).all()

    return render_template(
        "installers/list.html",
        installers=installers,
        customer_bookings=customer_bookings
    )


# Single installer profile
@public_installer_bp.route("/<int:installer_id>")
def view_installer(installer_id):
    installer = Installer.query.get_or_404(installer_id)
    user = User.query.get(installer.user_id)
    gallery = InstallerGallery.query.filter_by(installer_id=installer.id).all()
    
    return render_template(
        "installers/view.html",
        installer=installer,
        user=user,
        gallery=gallery
    )

