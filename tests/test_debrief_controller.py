import pytest
from app.controllers.twitter_dmca_debrief_experiment_controller import TwitterDMCADebriefExperimentController
import os
import simplejson as json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import glob, datetime
from app.models import *
from utils.common import *

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR  = os.path.join(TEST_DIR, "../")
ENV = os.environ['CS_ENV'] = "test"

db_session = DbEngine(os.path.join(TEST_DIR, "../", "config") + "/{env}.json".format(env=ENV)).new_session()

def clear_db():
    db_session.query(TwitterUser).delete()
    db_session.query(TwitterUserMetadata).delete()
    db_session.query(TwitterUserEligibility).delete()
    db_session.query(Experiment).delete()
    db_session.query(Randomization).delete()
    db_session.query(ExperimentAction).delete()
    db_session.query(TwitterUserSurveyResult).delete()
    db_session.commit()

def setup_function(function):
    clear_db()

def teardown_function(function):
    clear_db()

def test_experiment_initialization():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    all_experiments = db_session.query(Experiment).all()
    assert len(all_experiments) == 1

    all_randomizations = db_session.query(Randomization).all()
    assert len(all_randomizations) == 8032

    all_eligible_ids = db_session.query(TwitterUserEligibility).all()
    assert len(all_eligible_ids) > 0

def test_user_exists():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }

    assert sce.user_exists(user) == False

    twitter_user = TwitterUser(id=user['id'])
    db_session.add(twitter_user)
    db_session.commit()

    assert sce.user_exists(user) == False

    twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'])
    db_session.add(twitter_user_metadata)
    db_session.commit()

    assert sce.user_exists(user) == True

def test_create_user_if_not_exists():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }

    assert sce.user_exists(user) == False

    sce.create_user_if_not_exists(user)

    assert sce.user_exists(user) == True

    try:
        sce.create_user_if_not_exists(user)
    except:
        assert False

    assert sce.user_exists(user) == True

def test_insert_or_update_survey_result():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }
    results_dict = { 'q1': 'a1', 'q2': 'a2' }

    maybe_survey_result = db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()
    assert maybe_survey_result is None

    sce.insert_or_update_survey_result(user, results_dict)

    maybe_survey_result = db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()
    assert maybe_survey_result is not None
    data_dict = json.loads(maybe_survey_result.survey_data)
    assert 'q1' in data_dict and 'q2' in data_dict and data_dict['q1'] == 'a1' and data_dict['q2'] == 'a2'

    results_dict = { 'q1': 'a1-2', 'q2': 'a2', 'q3': 'a3' }
    try:
        sce.insert_or_update_survey_result(user, results_dict)
    except:
        assert False

    maybe_survey_result = db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()
    assert maybe_survey_result is not None
    data_dict = json.loads(maybe_survey_result.survey_data)
    assert 'q1' in data_dict and 'q2' in data_dict and 'q3' in data_dict and data_dict['q1'] == 'a1-2' and data_dict['q2'] == 'a2' and data_dict['q3'] == 'a3'

def test_assign_randomization():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    # removed tweet
    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }
    results_dict = { 'tweet_removed': 'true' }

    twitter_user = TwitterUser(id=user['id'])
    twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'])
    db_session.add(twitter_user)
    db_session.add(twitter_user_metadata)
    db_session.commit()

    sce.assign_randomization(user, results_dict)

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.tweet_removed == True
    assignment_dict = json.loads(twitter_user_metadata.assignment_json)
    assert assignment_dict['stratum'] == 'Removed'
    randomization = db_session.query(Randomization).filter_by(id=assignment_dict['id']).first()
    assert randomization is not None
    assert randomization.assigned == True

    # didn't remove tweet
    user = { 'id': '7654321', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }
    results_dict = { 'tweet_removed': 'false' }

    twitter_user = TwitterUser(id=user['id'])
    twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'])
    db_session.add(twitter_user)
    db_session.add(twitter_user_metadata)
    db_session.commit()

    sce.assign_randomization(user, results_dict)

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.tweet_removed == False

    assignment_dict = json.loads(twitter_user_metadata.assignment_json)
    assert assignment_dict['stratum'] == 'Not Removed'
    randomization = db_session.query(Randomization).filter_by(id=assignment_dict['id']).first()
    assert randomization is not None
    assert randomization.assigned == True

    # repeat call

    try:
        sce.assign_randomization(user, results_dict)
    except:
        assert False

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.tweet_removed == False

    assignment_dict = json.loads(twitter_user_metadata.assignment_json)
    assert assignment_dict['stratum'] == 'Not Removed'
    randomization = db_session.query(Randomization).filter_by(id=assignment_dict['id']).first()
    assert randomization is not None
    assert randomization.assigned == True

    # changed survey answer
    results_dict = { 'tweet_removed': 'true' }

    sce.assign_randomization(user, results_dict)

    randomization = db_session.query(Randomization).filter_by(id=assignment_dict['id']).first()
    assert randomization is not None
    assert randomization.assigned == False

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.tweet_removed == True

    assignment_dict = json.loads(twitter_user_metadata.assignment_json)
    assert assignment_dict['stratum'] == 'Removed'
    randomization = db_session.query(Randomization).filter_by(id=assignment_dict['id']).first()
    assert randomization is not None
    assert randomization.assigned == True

def test_get_user_conditions():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    all_experiment_actions = db_session.query(ExperimentAction).all()
    assert len(all_experiment_actions) == 0

    sce.record_user_action(None, 'page_view', {'page': 'index', 'user_agent': 'check_http blah blah', 'qs': ''})

    all_experiment_actions = db_session.query(ExperimentAction).all()
    assert len(all_experiment_actions) == 0

    sce.record_user_action(None, 'page_view', {'page': 'index', 'user_agent': 'Mozilla blah blah', 'qs': ''})

    all_experiment_actions = db_session.query(ExperimentAction).all()
    assert len(all_experiment_actions) == 1


def test_mark_user_completed():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }
    results_dict = { }

    twitter_user = TwitterUser(id=user['id'])
    twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'])
    db_session.add(twitter_user)
    db_session.add(twitter_user_metadata)
    db_session.commit()

    sce.insert_or_update_survey_result(user, results_dict)
    sce.mark_user_completed(user)

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.completed_study_at is None

    results_dict = { "tweet_removed": "hi",
                     "click_tweet": "hi",
                     "would_delete": "hi",
                     "society_benefit": "hi",
                     "personal_benefit": "hi",
                     "collection_surprised": "hi",
                     "glad_in_study": "hi",
                     "share_results": "hi",
                     "vote_study": "hi",
                     "improve_debrief": "hi" }

    sce.insert_or_update_survey_result(user, results_dict)
    sce.mark_user_completed(user)

    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.completed_study_at is not None

    assert sce.has_completed_study(user) == True


def test_send_paypal_payout():
    # TODO
    pass

def test_is_eligible():
    sce = TwitterDMCADebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    all_eligible_ids = db_session.query(TwitterUserEligibility).all()
    assert len(all_eligible_ids) > 0

    user = {'id': all_eligible_ids[0].id}

    assert sce.is_eligible(user) == True

    user = {'id': 'not a real id'}

    assert sce.is_eligible(user) == False

def test_send_recruitment_tweets():
    # TODO sorry
    pass
