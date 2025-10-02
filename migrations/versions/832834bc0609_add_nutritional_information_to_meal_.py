"""Add nutritional information to Meal model

Revision ID: 832834bc0609
Revises: 67a2c6df07f8
Create Date: 2025-10-02 11:17:43.313542

"""
from alembic import op
import sqlalchemy as sa



revision = '832834bc0609'
down_revision = '67a2c6df07f8'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('meals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('calories', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('protein_grams', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('carbohydrates_grams', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('fats_grams', sa.Float(), nullable=True))




def downgrade():

    with op.batch_alter_table('meals', schema=None) as batch_op:
        batch_op.drop_column('fats_grams')
        batch_op.drop_column('carbohydrates_grams')
        batch_op.drop_column('protein_grams')
        batch_op.drop_column('calories')
        batch_op.drop_column('category')

