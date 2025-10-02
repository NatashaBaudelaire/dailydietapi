from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import config

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name='default'):
    '''Application factory pattern'''
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Register blueprints
    from app.routes.meals import meals_bp
    app.register_blueprint(meals_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.user import user_bp
    app.register_blueprint(user_bp)

    from app.routes.social import social_bp
    app.register_blueprint(social_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import jsonify
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': error.description}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': error.description}), 400