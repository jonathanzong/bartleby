"""Add experiment action

Revision ID: 4cdc61d39146
Revises: f9d14fb8ba9b
Create Date: 2017-12-03 23:47:50.804305

"""

# revision identifiers, used by Alembic.
revision = '4cdc61d39146'
down_revision = 'f9d14fb8ba9b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    op.create_table('experiment_action',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('experiment_id', sa.String(length=64), nullable=False),
    sa.Column('action_type', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=False),
    sa.Column('action_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade_development():
    op.drop_table('experiment_action')


def upgrade_test():
    op.create_table('experiment_action',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('experiment_id', sa.String(length=64), nullable=False),
    sa.Column('action_type', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=False),
    sa.Column('action_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade_test():
    op.drop_table('experiment_action')


def upgrade_production():
    op.create_table('experiment_action',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('experiment_id', sa.String(length=64), nullable=False),
    sa.Column('action_type', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=False),
    sa.Column('action_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade_production():
    op.drop_table('experiment_action')

