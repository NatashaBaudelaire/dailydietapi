from flask import Blueprint, request, jsonify, url_for
from datetime import datetime, timezone
from app import db
from app.models.meal import Meal
from app.schemas.meal_schema import validate_meal_data, validate_meal_update
from app.decorators import token_required

meals_bp = Blueprint('meals', __name__, url_prefix='')

@meals_bp.route('/', methods=['GET'])
def index():
    '''API landing page with a list of available endpoints'''
    return jsonify({
        'message': 'Welcome to the Daily Diet API!',
        'auth_endpoints': [
            str(url_for('auth.register', _external=True)),
            str(url_for('auth.login', _external=True)),
        ],
        'user_endpoints': [
            str(url_for('user.get_profile', _external=True)) + ' (token required)',
            str(url_for('user.update_profile', _external=True)) + ' (token required)',
            str(url_for('user.update_password', _external=True)) + ' (token required)',
        ],
        'meal_endpoints': [
            str(url_for('meals.health_check', _external=True)),
            str(url_for('meals.create_meal', _external=True)) + ' (token required)',
            str(url_for('meals.get_meals', _external=True)) + ' (token required)',
            str(url_for('meals.get_meal', meal_id=1, _external=True)) + ' (token required)',
            str(url_for('meals.update_meal', meal_id=1, _external=True)) + ' (token required)',
            str(url_for('meals.delete_meal', meal_id=1, _external=True)) + ' (token required)',
            str(url_for('meals.get_user_stats', _external=True)) + ' (token required)',
            str(url_for('meals.get_best_diet_sequence', _external=True)) + ' (token required)',
        ]
    }), 200


@meals_bp.route('/health', methods=['GET'])
def health_check():
    '''Health check endpoint'''
    return jsonify({
        'status': 'healthy',
        'message': 'Daily Diet API is running'
    }), 200


@meals_bp.route('/meals', methods=['POST'])
@token_required
def create_meal(current_user):
    '''Register a new meal for the authenticated user'''
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_meal_data(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        meal_datetime = datetime.fromisoformat(data['datetime'])
        
        new_meal = Meal(
            name=data['name'].strip(),
            description=data['description'].strip(),
            datetime=meal_datetime,
            is_on_diet=data['is_on_diet'],
            user_id=current_user.id
        )
        
        db.session.add(new_meal)
        db.session.commit()
        
        return jsonify({
            'message': 'Meal registered successfully',
            'meal': new_meal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to register meal: {str(e)}'}), 500

@meals_bp.route('/meals', methods=['GET'])
@token_required
def get_meals(current_user):
    '''List all meals for the authenticated user'''
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtering
        query = Meal.query.filter_by(user_id=current_user.id)
        
        start_date = request.args.get('start_date')
        if start_date:
            query = query.filter(Meal.datetime >= datetime.fromisoformat(start_date))
            
        end_date = request.args.get('end_date')
        if end_date:
            query = query.filter(Meal.datetime <= datetime.fromisoformat(end_date))
            
        on_diet = request.args.get('on_diet')
        if on_diet is not None:
            query = query.filter(Meal.is_on_diet == (on_diet.lower() == 'true'))
            
        meals_pagination = query.order_by(Meal.datetime.desc()).paginate(page=page, per_page=per_page, error_out=False)
        meals = meals_pagination.items
        
        return jsonify({
            'user_id': current_user.id,
            'total_meals': meals_pagination.total,
            'page': meals_pagination.page,
            'per_page': meals_pagination.per_page,
            'total_pages': meals_pagination.pages,
            'has_next': meals_pagination.has_next,
            'has_prev': meals_pagination.has_prev,
            'meals': [meal.to_dict() for meal in meals]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve meals: {str(e)}'}), 500


@meals_bp.route('/meals/<int:meal_id>', methods=['GET'])
@token_required
def get_meal(current_user, meal_id):
    '''Retrieve a single meal by ID, if it belongs to the user'''
    try:
        meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
        
        if not meal:
            return jsonify({'error': 'Meal not found or you do not have permission to view it'}), 404
        
        return jsonify({'meal': meal.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve meal: {str(e)}'}), 500


@meals_bp.route('/meals/<int:meal_id>', methods=['PUT'])
@token_required
def update_meal(current_user, meal_id):
    '''Edit an existing meal, if it belongs to the user'''
    try:
        meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
        
        if not meal:
            return jsonify({'error': 'Meal not found or you do not have permission to edit it'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_meal_update(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        if 'name' in data:
            meal.name = data['name'].strip()
        
        if 'description' in data:
            meal.description = data['description'].strip()
        
        if 'datetime' in data:
            meal.datetime = datetime.fromisoformat(data['datetime'])
        
        if 'is_on_diet' in data:
            meal.is_on_diet = data['is_on_diet']
        
        meal.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Meal updated successfully',
            'meal': meal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update meal: {str(e)}'}), 500


@meals_bp.route('/meals/<int:meal_id>', methods=['DELETE'])
@token_required
def delete_meal(current_user, meal_id):
    '''Delete a meal, if it belongs to the user'''
    try:
        meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
        
        if not meal:
            return jsonify({'error': 'Meal not found or you do not have permission to delete it'}), 404
        
        db.session.delete(meal)
        db.session.commit()
        
        return jsonify({'message': 'Meal deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete meal: {str(e)}'}), 500


@meals_bp.route('/meals/stats', methods=['GET'])
@token_required
def get_user_stats(current_user):
    '''Get diet statistics for the authenticated user'''
    try:
        meals = Meal.query.filter_by(user_id=current_user.id).all()
        
        total_meals = len(meals)
        on_diet_meals = sum(1 for meal in meals if meal.is_on_diet)
        off_diet_meals = total_meals - on_diet_meals
        
        on_diet_percentage = (on_diet_meals / total_meals * 100) if total_meals > 0 else 0
        
        return jsonify({
            'user_id': current_user.id,
            'total_meals': total_meals,
            'on_diet_meals': on_diet_meals,
            'off_diet_meals': off_diet_meals,
            'on_diet_percentage': round(on_diet_percentage, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve statistics: {str(e)}'}), 500


@meals_bp.route('/meals/best-sequence', methods=['GET'])
@token_required
def get_best_diet_sequence(current_user):
    '''Get the best sequence of meals on diet for the authenticated user'''
    try:
        meals = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.datetime.asc()).all()
        
        if not meals:
            return jsonify({
                'user_id': current_user.id,
                'best_sequence': 0,
                'meals': []
            }), 200

        best_sequence = 0
        current_sequence = 0
        best_sequence_meals = []
        current_sequence_meals = []

        for meal in meals:
            if meal.is_on_diet:
                current_sequence += 1
                current_sequence_meals.append(meal.to_dict())
            else:
                if current_sequence > best_sequence:
                    best_sequence = current_sequence
                    best_sequence_meals = current_sequence_meals
                current_sequence = 0
                current_sequence_meals = []
        
        if current_sequence > best_sequence:
            best_sequence = current_sequence
            best_sequence_meals = current_sequence_meals

        return jsonify({
            'user_id': current_user.id,
            'best_sequence': best_sequence,
            'meals': best_sequence_meals
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve best sequence: {str(e)}'}), 500