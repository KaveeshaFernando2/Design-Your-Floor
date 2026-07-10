from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/get_quote')
def get_quote():
    return render_template('get_quote.html')

@main_bp.route('/services')
def services():
    return render_template('services.html')

@main_bp.route('/gallery')
def gallery():
    return render_template('gallery.html')