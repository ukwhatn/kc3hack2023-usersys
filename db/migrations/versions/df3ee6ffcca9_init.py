"""init

Revision ID: df3ee6ffcca9
Revises: 
Create Date: 2023-01-28 22:21:15.898806

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df3ee6ffcca9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sessions',
    sa.Column('id', sa.String(length=50), autoincrement=False, nullable=False),
    sa.Column('value', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name_first', sa.String(length=50), nullable=True),
    sa.Column('name_last', sa.String(length=50), nullable=True),
    sa.Column('name_first_kana', sa.String(length=50), nullable=True),
    sa.Column('name_last_kana', sa.String(length=50), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('registered_email', sa.String(length=100), nullable=True),
    sa.Column('univ_name', sa.String(length=50), nullable=True),
    sa.Column('univ_year', sa.Integer(), nullable=True),
    sa.Column('circle_name', sa.String(length=50), nullable=True),
    sa.Column('github_user_id', sa.Integer(), nullable=True),
    sa.Column('github_user_name', sa.String(length=50), nullable=True),
    sa.Column('discord_user_id', sa.BigInteger(), nullable=True),
    sa.Column('discord_user_name', sa.String(length=50), nullable=True),
    sa.Column('discord_avatar_hash', sa.String(length=50), nullable=True),
    sa.Column('team_id', sa.String(length=5), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('is_supporter', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('sessions')
    # ### end Alembic commands ###