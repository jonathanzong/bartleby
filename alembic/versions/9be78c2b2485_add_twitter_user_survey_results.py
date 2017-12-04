"""Add twitter user survey results

Revision ID: 9be78c2b2485
Revises: 4cdc61d39146
Create Date: 2017-12-04 00:14:11.826577

"""

# revision identifiers, used by Alembic.
revision = '9be78c2b2485'
down_revision = '4cdc61d39146'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    op.create_table('twitter_user_survey_results',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id')
    )


def downgrade_development():
    op.drop_table('twitter_user_survey_results')


def upgrade_test():
    op.create_table('twitter_user_survey_results',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id')
    )


def downgrade_test():
    op.drop_table('twitter_user_survey_results')


def upgrade_production():
    op.create_table('twitter_user_survey_results',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('twitter_user_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id')
    )


def downgrade_production():
    op.drop_table('twitter_user_survey_results')

