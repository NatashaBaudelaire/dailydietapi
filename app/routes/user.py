from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.decorators import token_required
import re

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    '''Get the current user's profile'''
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email
    }), 200

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    '''Update the current user's profile'''
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'username' in data:
        new_username = data['username']
        if User.query.filter_by(username=new_username).first() and new_username != current_user.username:
            return jsonify({'error': 'Username already taken'}), 400
        current_user.username = new_username

    if 'email' in data:
        new_email = data['email']
        if User.query.filter_by(email=new_email).first() and new_email != current_user.email:
            return jsonify({'error': 'Email address already registered'}), 400
        current_user.email = new_email

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@user_bp.route('/password', methods=['PUT'])
@token_required
def update_password(current_user):
    '''Update the current user's password'''
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing current_password or new_password'}), 400

    if not current_user.check_password(data['current_password']):
        return jsonify({'error': 'Invalid current password'}), 401

    new_password = data['new_password']
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    if not re.search(r'[A-Z]', new_password):
        return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
    if not re.search(r'[a-z]', new_password):
        return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
    if not re.search(r'[0-9]', new_password):
        return jsonify({'error': 'Password must contain at least one number'}), 400

    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200

@user_bp.route('/<username>/follow', methods=['POST'])
@token_required
def follow(current_user, username):
    '''Follow a user'''
    user_to_follow = User.query.filter_by(username=username).first()
    if not user_to_follow:
        return jsonify({'error': 'User not found'}), 404
    
    if user_to_follow.id == current_user.id:
        return jsonify({'error': 'You cannot follow yourself'}), 400

    current_user.follow(user_to_follow)
    db.session.commit()
    return jsonify({'message': f'You are now following {username}'}), 200

@user_bp.route('/<username>/unfollow', methods=['POST'])
@token_required
def unfollow(current_user, username):
    '''Unfollow a user'''
    user_to_unfollow = User.query.filter_by(username=username).first()
    if not user_to_unfollow:
        return jsonify({'error': 'User not found'}), 404

    if user_to_unfollow.id == current_user.id:
        return jsonify({'error': 'You cannot unfollow yourself'}), 400

    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    return jsonify({'message': f'You have unfollowed {username}'}), 200