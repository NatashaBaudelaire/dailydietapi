from datetime import datetime


def validate_meal_data(data):

    errors = []
    
    required_fields = ['name', 'description', 'datetime', 'is_on_diet', 'user_id']
    for field in required_fields:
        if field not in data:
            errors.append(f'Missing required field: {field}')
    
    if not errors:

        if not isinstance(data.get('name'), str) or len(data['name'].strip()) == 0:
            errors.append('Name must be a non-empty string')
        

        if not isinstance(data.get('description'), str) or len(data['description'].strip()) == 0:
            errors.append('Description must be a non-empty string')
        

        try:
            datetime.fromisoformat(data['datetime'])
        except (ValueError, TypeError):
            errors.append('Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS')
        

        if not isinstance(data.get('is_on_diet'), bool):
            errors.append('is_on_diet must be a boolean')
        

        if not isinstance(data.get('user_id'), int) or data['user_id'] <= 0:
            errors.append('user_id must be a positive integer')
    
    return errors


def validate_meal_update(data):

    errors = []
    
    if 'name' in data:
        if not isinstance(data['name'], str) or len(data['name'].strip()) == 0:
            errors.append('Name must be a non-empty string')
    
    if 'description' in data:
        if not isinstance(data['description'], str) or len(data['description'].strip()) == 0:
            errors.append('Description must be a non-empty string')
    
    if 'datetime' in data:
        try:
            datetime.fromisoformat(data['datetime'])
        except (ValueError, TypeError):
            errors.append('Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS')
    
    if 'is_on_diet' in data:
        if not isinstance(data['is_on_diet'], bool):
            errors.append('is_on_diet must be a boolean')
    
    return errors