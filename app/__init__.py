from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import pymysql

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = 'supersecretkey'

    # MySQL database (XAMPP)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/dyf'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.customer import customer_bp
    from app.routes.supplier import supplier_bp
    from app.routes.installer import installer_bp
    from app.routes.delivery import delivery_bp
    

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(installer_bp)
    app.register_blueprint(delivery_bp)



    from app.routes.public_installer import public_installer_bp
    app.register_blueprint(public_installer_bp)
    
    
    return app
