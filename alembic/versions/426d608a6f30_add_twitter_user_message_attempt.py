"""Add Twitter User Message Attempt

Revision ID: 426d608a6f30
Revises: b82c166efe70
Create Date: 2017-12-03 21:23:05.499876

"""

# revision identifiers, used by Alembic.
revision = '426d608a6f30'
down_revision = 'b82c166efe70'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('twitter_user_message_attempt',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('message_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('account_found', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###


def downgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('twitter_user_message_attempt')
    # ### end Alembic commands ###


def upgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('twitter_user_message_attempt',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('message_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('account_found', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###


def downgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('twitter_user_message_attempt')
    # ### end Alembic commands ###


def upgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('twitter_user_message_attempt',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('message_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('account_found', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###


def downgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('twitter_user_message_attempt')
    # ### end Alembic commands ###

