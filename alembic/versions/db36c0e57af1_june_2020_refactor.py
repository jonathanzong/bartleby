"""june 2020 refactor

Revision ID: db36c0e57af1
Revises: 266fc2005daa
Create Date: 2020-06-08 02:49:46.538386

"""

# revision identifiers, used by Alembic.
revision = 'db36c0e57af1'
down_revision = '266fc2005daa'
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
    op.create_table('participant_eligibility',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('study_data_json', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('user_json', sa.LargeBinary(), nullable=True),
    sa.Column('initial_login_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_survey_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('survey_data', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.drop_table('twitter_user_eligibility')
    op.drop_table('twitter_user_metadata')
    op.drop_index('ix_twitter_users_screen_name', table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_table('twitter_user_survey_results')
    op.add_column('experiment_actions', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('participant_user_id', sa.String(length=64), nullable=True))
    op.drop_column('experiment_actions', 'experiment_id')
    op.drop_column('experiment_actions', 'twitter_user_id')
    op.add_column('experiments', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('study_template', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('url_id', sa.String(length=64), nullable=False))
    op.drop_index('ix_experiments_name', table_name='experiments')
    op.create_unique_constraint(None, 'experiments', ['study_template'])
    op.create_unique_constraint(None, 'experiments', ['experiment_name'])
    op.drop_column('experiments', 'name')
    op.drop_column('experiments', 'id')
    op.drop_column('experiments', 'settings_json')
    op.drop_column('experiments', 'controller')
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('participant_user_id', sa.String(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'twitter_user_id')
    # ### end Alembic commands ###


def downgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'participant_user_id')
    op.add_column('experiments', sa.Column('controller', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiments', sa.Column('settings_json', sa.BLOB(), nullable=True))
    op.add_column('experiments', sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False))
    op.add_column('experiments', sa.Column('name', mysql.VARCHAR(length=64), nullable=True))
    op.drop_constraint(None, 'experiments', type_='unique')
    op.drop_constraint(None, 'experiments', type_='unique')
    op.create_index('ix_experiments_name', 'experiments', ['name'], unique=False)
    op.drop_column('experiments', 'url_id')
    op.drop_column('experiments', 'study_template')
    op.drop_column('experiments', 'experiment_name')
    op.add_column('experiment_actions', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True))
    op.drop_column('experiment_actions', 'participant_user_id')
    op.drop_column('experiment_actions', 'experiment_name')
    op.create_table('twitter_user_survey_results',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_users',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('screen_name', mysql.VARCHAR(length=256), nullable=True),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('lang', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('user_state', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('record_created_at', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_twitter_users_screen_name', 'twitter_users', ['screen_name'], unique=False)
    op.create_table('twitter_user_metadata',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('received_lumen_notice_at', mysql.DATETIME(), nullable=True),
    sa.Column('lumen_notice_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('user_json', sa.BLOB(), nullable=True),
    sa.Column('assignment_json', sa.BLOB(), nullable=True),
    sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('initial_login_at', mysql.DATETIME(), nullable=True),
    sa.Column('completed_study_at', mysql.DATETIME(), nullable=True),
    sa.Column('tweet_removed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('paypal_sender_batch_id', mysql.VARCHAR(length=64), nullable=True),
    sa.CheckConstraint('(`tweet_removed` in (0,1))', name='twitter_user_metadata_chk_2'),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_user_eligibility',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('extra_data', sa.BLOB(), nullable=True),
    sa.Column('study_data_json', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('participant_survey_results')
    op.drop_table('participant_record')
    op.drop_table('participant_eligibility')
    # ### end Alembic commands ###


def upgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('participant_eligibility',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('study_data_json', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('user_json', sa.LargeBinary(), nullable=True),
    sa.Column('initial_login_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_survey_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('survey_data', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.drop_table('twitter_user_eligibility')
    op.drop_table('twitter_user_metadata')
    op.drop_index('ix_twitter_users_screen_name', table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_table('twitter_user_survey_results')
    op.add_column('experiment_actions', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('participant_user_id', sa.String(length=64), nullable=True))
    op.drop_column('experiment_actions', 'experiment_id')
    op.drop_column('experiment_actions', 'twitter_user_id')
    op.add_column('experiments', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('study_template', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('url_id', sa.String(length=64), nullable=False))
    op.drop_index('ix_experiments_name', table_name='experiments')
    op.create_unique_constraint(None, 'experiments', ['study_template'])
    op.create_unique_constraint(None, 'experiments', ['experiment_name'])
    op.drop_column('experiments', 'name')
    op.drop_column('experiments', 'id')
    op.drop_column('experiments', 'settings_json')
    op.drop_column('experiments', 'controller')
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('participant_user_id', sa.String(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'twitter_user_id')
    # ### end Alembic commands ###


def downgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'participant_user_id')
    op.add_column('experiments', sa.Column('controller', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiments', sa.Column('settings_json', sa.BLOB(), nullable=True))
    op.add_column('experiments', sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False))
    op.add_column('experiments', sa.Column('name', mysql.VARCHAR(length=64), nullable=True))
    op.drop_constraint(None, 'experiments', type_='unique')
    op.drop_constraint(None, 'experiments', type_='unique')
    op.create_index('ix_experiments_name', 'experiments', ['name'], unique=False)
    op.drop_column('experiments', 'url_id')
    op.drop_column('experiments', 'study_template')
    op.drop_column('experiments', 'experiment_name')
    op.add_column('experiment_actions', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True))
    op.drop_column('experiment_actions', 'participant_user_id')
    op.drop_column('experiment_actions', 'experiment_name')
    op.create_table('twitter_user_survey_results',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_users',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('screen_name', mysql.VARCHAR(length=256), nullable=True),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('lang', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('user_state', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('record_created_at', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_twitter_users_screen_name', 'twitter_users', ['screen_name'], unique=False)
    op.create_table('twitter_user_metadata',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('received_lumen_notice_at', mysql.DATETIME(), nullable=True),
    sa.Column('lumen_notice_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('user_json', sa.BLOB(), nullable=True),
    sa.Column('assignment_json', sa.BLOB(), nullable=True),
    sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('initial_login_at', mysql.DATETIME(), nullable=True),
    sa.Column('completed_study_at', mysql.DATETIME(), nullable=True),
    sa.Column('tweet_removed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('paypal_sender_batch_id', mysql.VARCHAR(length=64), nullable=True),
    sa.CheckConstraint('(`tweet_removed` in (0,1))', name='twitter_user_metadata_chk_2'),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_user_eligibility',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('extra_data', sa.BLOB(), nullable=True),
    sa.Column('study_data_json', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('participant_survey_results')
    op.drop_table('participant_record')
    op.drop_table('participant_eligibility')
    # ### end Alembic commands ###


def upgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('participant_eligibility',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('study_data_json', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('user_json', sa.LargeBinary(), nullable=True),
    sa.Column('initial_login_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.create_table('participant_survey_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experiment_name', sa.String(length=64), nullable=True),
    sa.Column('participant_user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('survey_data', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('experiment_name', 'participant_user_id', name='_experiment_participant_uc')
    )
    op.drop_table('twitter_user_eligibility')
    op.drop_table('twitter_user_metadata')
    op.drop_index('ix_twitter_users_screen_name', table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_table('twitter_user_survey_results')
    op.add_column('experiment_actions', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('participant_user_id', sa.String(length=64), nullable=True))
    op.drop_column('experiment_actions', 'experiment_id')
    op.drop_column('experiment_actions', 'twitter_user_id')
    op.add_column('experiments', sa.Column('experiment_name', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('study_template', sa.String(length=64), nullable=True))
    op.add_column('experiments', sa.Column('url_id', sa.String(length=64), nullable=False))
    op.drop_index('ix_experiments_name', table_name='experiments')
    op.create_unique_constraint(None, 'experiments', ['study_template'])
    op.create_unique_constraint(None, 'experiments', ['experiment_name'])
    op.drop_column('experiments', 'name')
    op.drop_column('experiments', 'id')
    op.drop_column('experiments', 'settings_json')
    op.drop_column('experiments', 'controller')
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('participant_user_id', sa.String(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'twitter_user_id')
    # ### end Alembic commands ###


def downgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('twitter_user_recruitment_tweet_attempt', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False))
    op.drop_column('twitter_user_recruitment_tweet_attempt', 'participant_user_id')
    op.add_column('experiments', sa.Column('controller', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiments', sa.Column('settings_json', sa.BLOB(), nullable=True))
    op.add_column('experiments', sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False))
    op.add_column('experiments', sa.Column('name', mysql.VARCHAR(length=64), nullable=True))
    op.drop_constraint(None, 'experiments', type_='unique')
    op.drop_constraint(None, 'experiments', type_='unique')
    op.create_index('ix_experiments_name', 'experiments', ['name'], unique=False)
    op.drop_column('experiments', 'url_id')
    op.drop_column('experiments', 'study_template')
    op.drop_column('experiments', 'experiment_name')
    op.add_column('experiment_actions', sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=True))
    op.add_column('experiment_actions', sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True))
    op.drop_column('experiment_actions', 'participant_user_id')
    op.drop_column('experiment_actions', 'experiment_name')
    op.create_table('twitter_user_survey_results',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('survey_data', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_users',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('screen_name', mysql.VARCHAR(length=256), nullable=True),
    sa.Column('created_at', mysql.DATETIME(), nullable=True),
    sa.Column('lang', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('user_state', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('record_created_at', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_twitter_users_screen_name', 'twitter_users', ['screen_name'], unique=False)
    op.create_table('twitter_user_metadata',
    sa.Column('twitter_user_id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('received_lumen_notice_at', mysql.DATETIME(), nullable=True),
    sa.Column('lumen_notice_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('user_json', sa.BLOB(), nullable=True),
    sa.Column('assignment_json', sa.BLOB(), nullable=True),
    sa.Column('experiment_id', mysql.VARCHAR(length=64), nullable=True),
    sa.Column('initial_login_at', mysql.DATETIME(), nullable=True),
    sa.Column('completed_study_at', mysql.DATETIME(), nullable=True),
    sa.Column('tweet_removed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('paypal_sender_batch_id', mysql.VARCHAR(length=64), nullable=True),
    sa.CheckConstraint('(`tweet_removed` in (0,1))', name='twitter_user_metadata_chk_2'),
    sa.PrimaryKeyConstraint('twitter_user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('twitter_user_eligibility',
    sa.Column('id', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('extra_data', sa.BLOB(), nullable=True),
    sa.Column('study_data_json', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('participant_survey_results')
    op.drop_table('participant_record')
    op.drop_table('participant_eligibility')
    # ### end Alembic commands ###

