import os
import sys
import simplejson as json
from utils.common import *
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, Index
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
    id                  = Column(String(64), primary_key = True) # should be lowercase; if not found, # if not found, NOT_FOUND_TWITTER_USER_STR_[date]
    not_found_id        = Column(String(64), index = True, default=None)    # if a user ever goes between e.g. FOUND and NOT_FOUND (either direction), 
                                                                            # we want to be able to map between the actual id and the <NOT_FOUND>... id 
    screen_name         = Column(String(256), index = True) # if not found, # if not found, NOT_FOUND_TWITTER_USER_STR
    created_at          = Column(DateTime)
    record_created_at   = Column(DateTime, default=datetime.datetime.utcnow)
    lang                = Column(String(32))
    user_state          = Column(Integer) # utils/common.py
    CS_oldest_tweets_archived = Column(Integer, default=1) # see CS_JobState Enum
