"""add index to experiment name

Revision ID: 0b6e7324eded
Revises: 8c09a746d436
Create Date: 2017-12-19 19:00:34.111091

"""

# revision identifiers, used by Alembic.
revision = '0b6e7324eded'
down_revision = '8c09a746d436'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_experiments_name'), 'experiments', ['name'], unique=False)
    # ### end Alembic commands ###


def downgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_experiments_name'), table_name='experiments')
    # ### end Alembic commands ###


def upgrade_test():
    pass


def downgrade_test():
    pass


def upgrade_production():
    pass


def downgrade_production():
    pass

