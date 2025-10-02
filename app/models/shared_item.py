from datetime import datetime, timezone
from app import db

shared_item_meals = db.Table('shared_item_meals',
    db.Column('shared_item_id', db.Integer, db.ForeignKey('shared_items.id')),
    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id'))
)

class SharedItem(db.Model):
    __tablename__ = 'shared_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User')
    meals = db.relationship('Meal', secondary=shared_item_meals, lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'meals': [meal.to_dict() for meal in self.meals]
        }
