import os
from flask import Blueprint, request, jsonify, url_for
from datetime import datetime, timezone, date, timedelta
from app import db
from app.models.meal import Meal
from flask_pydantic import validate
from app.schemas.meal_schema import MealCreateSchema, MealUpdateSchema
from app.decorators import token_required
from app.services.s3_service import upload_file_to_s3
from app.services.email_service import send_email

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
            str(url_for('user.follow', username='<username>', _external=True)) + ' (token required)',
            str(url_for('user.unfollow', username='<username>', _external=True)) + ' (token required)',
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
            str(url_for('meals.get_meal_reports', _external=True)) + ' (token required)',
            str(url_for('meals.upload_meal_image', meal_id=1, _external=True)) + ' (token required)',
            str(url_for('meals.send_meal_reminders', _external=True)) + ' (token required)',
        'social_endpoints': [
            str(url_for('social.share_meals', _external=True)) + ' (token required)',
            str(url_for('social.get_shared_item', shared_item_id=1, _external=True)) + ' (token required)',
            str(url_for('social.get_feed', _external=True)) + ' (token required)',
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
@validate()
def create_meal(current_user, body: MealCreateSchema):
    '''Register a new meal for the authenticated user'''
    try:
        new_meal = Meal(
            name=body.name,
            description=body.description,
            datetime=body.datetime,
            is_on_diet=body.is_on_diet,
            user_id=current_user.id,
            category=body.category,
            calories=body.calories,
            protein_grams=body.protein_grams,
            carbohydrates_grams=body.carbohydrates_grams,
            fats_grams=body.fats_grams
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
@validate()
def update_meal(current_user, meal_id, body: MealUpdateSchema):
    '''Edit an existing meal, if it belongs to the user'''
    try:
        meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
        
        if not meal:
            return jsonify({'error': 'Meal not found or you do not have permission to edit it'}), 404
        
        update_data = body.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(meal, key, value)
        
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
        meal = Meal.query.filter_by(id=meal_id, user__id=current_user.id).first()
        
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

@meals_bp.route('/meals/reports', methods=['GET'])
@token_required
def get_meal_reports(current_user):
    '''Generate daily, weekly, or monthly meal reports'''
    try:
        period = request.args.get('period', 'daily', type=str)
        report_date_str = request.args.get('date', date.today().isoformat(), type=str)
        report_date = date.fromisoformat(report_date_str)

        if period == 'daily':
            start_date = datetime.combine(report_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = start_date + timedelta(days=1)
        elif period == 'weekly':
            start_date = datetime.combine(report_date - timedelta(days=report_date.weekday()), datetime.min.time(), tzinfo=timezone.utc)
            end_date = start_date + timedelta(days=7)
        elif period == 'monthly':
            start_date = datetime.combine(report_date.replace(day=1), datetime.min.time(), tzinfo=timezone.utc)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = datetime.combine(next_month - timedelta(days=next_month.day), datetime.min.time(), tzinfo=timezone.utc)
        else:
            return jsonify({'error': 'Invalid period specified. Use daily, weekly, or monthly.'}), 400

        meals = Meal.query.filter(
            Meal.user_id == current_user.id,
            Meal.datetime >= start_date,
            Meal.datetime < end_date
        ).all()

        total_meals = len(meals)
        total_calories = sum(meal.calories for meal in meals if meal.calories)
        total_protein = sum(meal.protein_grams for meal in meals if meal.protein_grams)
        total_carbs = sum(meal.carbohydrates_grams for meal in meals if meal.carbohydrates_grams)
        total_fats = sum(meal.fats_grams for meal in meals if meal.fats_grams)

        report = {
            'user_id': current_user.id,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_meals': total_meals,
            'total_calories': total_calories,
            'average_calories_per_meal': round(total_calories / total_meals, 2) if total_meals > 0 else 0,
            'total_protein_grams': total_protein,
            'total_carbohydrates_grams': total_carbs,
            'total_fats_grams': total_fats,
            'meals': [meal.to_dict() for meal in meals]
        }

        return jsonify(report), 200

    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@meals_bp.route('/meals/<int:meal_id>/image', methods=['POST'])
@token_required
def upload_meal_image(current_user, meal_id):
    '''Upload an image for a meal'''
    try:
        meal = Meal.query.filter_by(id=meal_id, user_id=current_user.id).first()
        if not meal:
            return jsonify({'error': 'Meal not found or you do not have permission to edit it'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            bucket_name = os.environ.get('S3_BUCKET_NAME')
            # create a unique filename for the image
            object_name = f"user_{current_user.id}_meal_{meal.id}_{file.filename}"
            image_url = upload_file_to_s3(file, bucket_name, object_name)
            if image_url:
                meal.image_url = image_url
                db.session.commit()
                return jsonify({'message': 'Image uploaded successfully', 'meal': meal.to_dict()}), 200
            else:
                return jsonify({'error': 'Failed to upload image to S3'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500

@meals_bp.route('/meals/reminders/send', methods=['POST'])
@token_required
def send_meal_reminders(current_user):
    '''Send meal reminders to the current user'''
    try:
        now = datetime.now(timezone.utc)
        end_of_day = now + timedelta(days=1)

        meals = Meal.query.filter(
            Meal.user_id == current_user.id,
            Meal.datetime >= now,
            Meal.datetime < end_of_day
        ).order_by(Meal.datetime.asc()).all()

        if not meals:
            return jsonify({'message': 'No upcoming meals in the next 24 hours.'}), 200

        subject = 'Your Upcoming Meal Reminders'
        html_content = '<h1>Your upcoming meals for the next 24 hours:</h1>'
        html_content += '<ul>'
        for meal in meals:
            html_content += f'<li><strong>{meal.name}</strong> at {meal.datetime.strftime("%Y-%m-%d %H:%M:%S")} UTC</li>'
        html_content += '</ul>'

        if send_email(current_user.email, subject, html_content):
            return jsonify({'message': 'Meal reminders sent successfully.'}), 200
        else:
            return jsonify({'error': 'Failed to send email.'}), 500

    except Exception as e:
        return jsonify({'error': f'Failed to send reminders: {str(e)}'}), 500