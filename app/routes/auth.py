import jwt
import re
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
from app import db, limiter
from app.models.user import User
from app.decorators import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({'error': 'Missing username, email or password'}), 400

    # Password strength validation
    password = data['password']
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({'error': 'Password must contain at least one number'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email address already registered'}), 400
    
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username already taken'}), 400

    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user is None or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    refresh_token = user.generate_refresh_token()
    db.session.commit()

    return jsonify({'access_token': access_token, 'refresh_token': refresh_token})

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Missing refresh token'}), 400

    refresh_token = data['refresh_token']
    user = User.query.filter_by(refresh_token=refresh_token).first()

    if not user:
        return jsonify({'error': 'Invalid refresh token'}), 401

    if user.refresh_token_expiration < datetime.now(timezone.utc):
        return jsonify({'error': 'Refresh token expired'}), 401

    access_token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'access_token': access_token})

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    current_user.revoke_refresh_token()
    db.session.commit()
    return jsonify({'message': 'Successfully logged out'}), 200