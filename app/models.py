import os
import sys
import simplejson as json
from utils.common import *
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, Index, LargeBinary
from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import sqlalchemy
import datetime
import socket

Base = declarative_base()

# a record of a study participant in our system (someone who has logged into the debriefing website)
class ParticipantRecord(Base):
    __tablename__ = 'participant_record'
    id                          = Column(Integer, primary_key = True)
    experiment_id               = Column(String(64))
    participant_user_id         = Column(String(64))
    user_json                   = Column(LargeBinary)
    initial_login_at            = Column(DateTime, default=datetime.datetime.utcnow)
    __table_args__              = (UniqueConstraint('experiment_id', 'participant_user_id', name='_experiment_participant_uc'))

# a record of an eligible study participant (someone who we want to debrief)
class ParticipantEligibility(Base):
    __tablename__ = 'participant_eligibility'
    id                          = Column(Integer, primary_key = True)
    experiment_id               = Column(String(64))
    participant_user_id         = Column(String(64))
    extra_data                  = Column(LargeBinary) # data specific to a study_template, like which academic account followed
    study_data_json             = Column(LargeBinary) # data collected on a user from the main study, to show in debriefing interface
    __table_args__              = (UniqueConstraint('experiment_id', 'participant_user_id', name='_experiment_participant_uc'))

# a record of a study (each study has a different URL on the site to debrief a different set of participants)
class Experiment(Base):
    __tablename__ = 'experiments'
    name                         = Column(String(64), primary_key = True)
    url_id                       = Column(String(64), unique = True)
    settings_json                = Column(LargeBinary)

# a record of an action a user takes on our website (logging in, submitting the form, etc)
class ExperimentAction(Base):
    __tablename__ = 'experiment_actions'
    id                  = Column(Integer, primary_key = True)
    experiment_id       = Column(String(64))
    participant_user_id = Column(String(64))
    action_type         = Column(String(64))
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    action_data         = Column(LargeBinary)

# a record of a participant's debriefing survey results, including opt-out preference
class ParticipantSurveyResult(Base):
    __tablename__ = 'participant_survey_results'
    id                  = Column(Integer, primary_key = True)
    experiment_id       = Column(String(64))
    participant_user_id = Column(String(64))
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    survey_data         = Column(LargeBinary)
    __table_args__      = (UniqueConstraint('experiment_id', 'participant_user_id', name='_experiment_participant_uc'))




# TODO this has not been refactored. long term, figure out what to do about twitter recruitment and compensation
class TwitterUserRecruitmentTweetAttempt(Base):
    __tablename__ = 'twitter_user_recruitment_tweet_attempt'
    participant_user_id         = Column(String(64), primary_key = True)
    attempted_at                = Column(DateTime, default=datetime.datetime.utcnow)
    sent                        = Column(Boolean)
    lang                        = Column(String(32))
    last_tweeted_at             = Column(DateTime)
    error_message               = Column(String(64))
    amount_dollars              = Column(Integer)
    study_template              = Column(String(64)) # which study template to render, match the name of folder in templates
    tweet_body                  = Column(String(64))
    extra_data                  = Column(LargeBinary) # data specific to a study_template, like which academic account followed
