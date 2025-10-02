from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.models.meal import Meal
from app.models.shared_item import SharedItem
from app.decorators import token_required

social_bp = Blueprint('social', __name__, url_prefix='/social')

@social_bp.route('/share', methods=['POST'])
@token_required
def share_meals(current_user):
    '''Share a meal or a list of meals'''
    data = request.get_json()
    if not data or not data.get('title') or not data.get('meal_ids'):
        return jsonify({'error': 'Missing title or meal_ids'}), 400

    shared_item = SharedItem(
        user_id=current_user.id,
        title=data['title'],
        description=data.get('description'),
        is_public=data.get('is_public', False)
    )

    meals = Meal.query.filter(Meal.id.in_(data['meal_ids']), Meal.user_id == current_user.id).all()
    if len(meals) != len(data['meal_ids']):
        return jsonify({'error': 'One or more meals not found or do not belong to the user'}), 404
    
    for meal in meals:
        shared_item.meals.append(meal)

    db.session.add(shared_item)
    db.session.commit()

    return jsonify({'message': 'Meals shared successfully', 'shared_item': shared_item.to_dict()}), 201

@social_bp.route('/share/<int:shared_item_id>', methods=['GET'])
@token_required
def get_shared_item(current_user, shared_item_id):
    '''Get a shared item by ID'''
    shared_item = SharedItem.query.get(shared_item_id)
    if not shared_item:
        return jsonify({'error': 'Shared item not found'}), 404

    if not shared_item.is_public:
        if shared_item.user_id != current_user.id and not current_user.is_following(shared_item.user):
             return jsonify({'error': 'You do not have permission to view this item'}), 403
    
    return jsonify(shared_item.to_dict()), 200

@social_bp.route('/feed', methods=['GET'])
@token_required
def get_feed(current_user):
    '''Get the feed of shared items from followed users'''
    followed_users_ids = [user.id for user in current_user.followed]
    shared_items = SharedItem.query.filter(SharedItem.user_id.in_(followed_users_ids)).order_by(SharedItem.created_at.desc()).all()
    
    return jsonify([item.to_dict() for item in shared_items]), 200
