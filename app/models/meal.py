from datetime import datetime, timezone
from app import db


class Meal(db.Model):
    '''Meal model representing a daily diet entry'''
    __tablename__ = 'meals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    is_on_diet = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='meals')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    category = db.Column(db.String(50), nullable=True)
    calories = db.Column(db.Integer, nullable=True)
    protein_grams = db.Column(db.Float, nullable=True)
    carbohydrates_grams = db.Column(db.Float, nullable=True)
    fats_grams = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Meal {self.name} - User {self.user_id}>'
    
    def to_dict(self):
        '''Convert meal object to dictionary'''
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'datetime': self.datetime.isoformat(),
            'is_on_diet': self.is_on_diet,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'category': self.category,
            'calories': self.calories,
            'protein_grams': self.protein_grams,
            'carbohydrates_grams': self.carbohydrates_grams,
            'fats_grams': self.fats_grams,
            'image_url': self.image_url
        }