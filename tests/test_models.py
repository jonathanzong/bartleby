import pytest, os
from mock import Mock, patch
import simplejson as json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_
import datetime

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ENV = os.environ['CS_ENV'] ="test"

from utils.common import DbEngine

### LOAD THE CLASSES TO TEST
from app.models import *

db_session = DbEngine(os.path.join(TEST_DIR, "../", "config") + "/{env}.json".format(env=ENV)).new_session()

@pytest.fixture
def populate_twitter_users():
    fixture_dir = os.path.join(TEST_DIR, "fixtures")
    counter = 0
    with open(os.path.join(fixture_dir, "twitter_users.json")) as f:
        twitter_users = json.loads(f.read())
        for user in twitter_users:
            created_at = user['created_at']
            if(created_at == "NOW"):
                created_at = datetime.datetime.now()
            twitter_user = TwitterUser(id = user['id'],
                                       created_at = created_at,
                                       screen_name = user['screen_name'],
                                       account_created_at = user['account_created_at'],
                                       lang = user['lang'],
                                       user_state = user['user_state']
                                       )
            db_session.add(twitter_user)
            counter += 1

        db_session.commit()
    return counter

def test_twitter_users(populate_twitter_users):
    all_users = db_session.query(TwitterUser).all()
    assert len(all_users) == 3
