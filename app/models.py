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

class TwitterUser(Base):
    __tablename__ = 'twitter_users'
    id                  = Column(String(64), primary_key = True) # should be lowercase
    screen_name         = Column(String(256), index = True) # if not found, # if not found, NOT_FOUND_TWITTER_USER_STR
    created_at          = Column(DateTime)
    lang                = Column(String(32))
    record_created_at   = Column(DateTime, default=datetime.datetime.utcnow)
    user_state          = Column(Integer) # utils/common.py


class TwitterUserMetadata(Base):
    __tablename__ = 'twitter_user_metadata'
    twitter_user_id             = Column(String(64), primary_key = True)
    received_lumen_notice_at    = Column(DateTime)
    tweet_removed               = Column(Boolean)
    lumen_notice_id             = Column(String(64))
    user_json                   = Column(LargeBinary)
    assignment_json             = Column(LargeBinary)
    experiment_id               = Column(String(64))
    initial_login_at            = Column(DateTime, default=datetime.datetime.utcnow)
    completed_study_at          = Column(DateTime)


class TwitterUserMessageAttempt(Base):
    __tablename__ = 'twitter_user_message_attempt'
    id                  = Column(String(64), primary_key = True)
    created_at          = Column(DateTime)
    message_id          = Column(String(64))
    account_found       = Column(Boolean) #if we don't find the account, record the attempt and make other values except created_at and id to NONE


class Experiment(Base):
    __tablename__ = 'experiments'
    id                           = Column(Integer, primary_key = True)
    name                         = Column(String(64))
    controller                   = Column(String(64))
    settings_json                = Column(LargeBinary)

class Randomization(Base):
    __tablename__ = 'randomizations'
    id                           = Column(Integer, primary_key = True)
    randomization_id             = Column(String(64))
    stratum                      = Column(String(64), index = True)
    block_id                     = Column(String(64))
    block_size                   = Column(Integer)
    treatment                    = Column(Integer)
    assigned                     = Column(Boolean)

class ExperimentAction(Base):
    __tablename__ = 'experiment_actions'
    id                  = Column(String(64), primary_key = True)
    experiment_id       = Column(String(64))
    action_type         = Column(String(64))
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    twitter_user_id     = Column(String(64))
    action_data         = Column(LargeBinary)


class TwitterUserSurveyResult(Base):
    __tablename__ = 'twitter_user_survey_results'
    twitter_user_id     = Column(String(64), primary_key = True)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    survey_data         = Column(LargeBinary)

