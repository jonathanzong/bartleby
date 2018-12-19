import pytest
import tweepy
from app.controllers.twitter_debrief_experiment_controller import TwitterDebriefExperimentController
import os
import simplejson as json
from mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import glob, datetime
from app.models import *
from utils.common import *
from types import SimpleNamespace

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR  = os.path.join(TEST_DIR, "../")
ENV = os.environ['CS_ENV'] = "test"

db_session = DbEngine(os.path.join(TEST_DIR, "../", "config") + "/{env}.json".format(env=ENV)).new_session()

def clear_db():
    db_session.query(TwitterUser).delete()
    db_session.query(TwitterUserMetadata).delete()
    db_session.query(TwitterUserEligibility).delete()
    db_session.query(TwitterUserRecruitmentTweetAttempt).delete()
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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
    sce = TwitterDebriefExperimentController(
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

@patch('paypalrestsdk.Payout', autospec=True)
def test_send_paypal_payout(mock_paypal_api):
    sce = TwitterDebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }
    email_address = 'jz7@cs.princeton.edu'

    twitter_user = TwitterUser(id=user['id'])
    twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'])
    db_session.add(twitter_user)
    db_session.add(twitter_user_metadata)
    db_session.commit()

    error_msg = sce.send_paypal_payout(user, email_address, 0)
    assert error_msg is not None
    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.paypal_sender_batch_id == None

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

    twitter_user_metadata.initial_login_at = datetime.datetime.now() - datetime.timedelta(days=8)
    db_session.commit()

    error_msg = sce.send_paypal_payout(user, email_address, 0)
    assert error_msg is not None
    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.paypal_sender_batch_id == None

    twitter_user_metadata.initial_login_at = datetime.datetime.now() - datetime.timedelta(days=1)
    db_session.commit()

    payout = mock_paypal_api.return_value
    payout.create.side_effect = Exception('test payout create fails')

    error_msg = sce.send_paypal_payout(user, email_address, 0)
    assert error_msg is not None
    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.paypal_sender_batch_id == None

    payout.create.side_effect = None

    error_msg = sce.send_paypal_payout(user, email_address, 0)
    assert error_msg is None
    twitter_user_metadata = db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assert twitter_user_metadata.paypal_sender_batch_id == user['id']

    error_msg = sce.send_paypal_payout(user, email_address, 0)
    assert error_msg is not None

def test_is_eligible():
    sce = TwitterDebriefExperimentController(
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

def test_get_user_compensation_amount():
    sce = TwitterDebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    user = { 'id': '1234567', 'screen_name': 'hihihi', 'created_at': datetime.datetime.now().isoformat(), 'lang': 'en' }

    assert sce.get_user_compensation_amount(user) == 0

    attempt = TwitterUserRecruitmentTweetAttempt(twitter_user_id=user['id'], amount_dollars=5)
    db_session.add(attempt)
    db_session.commit()

    assert sce.get_user_compensation_amount(user) == 5

@patch('tweepy.API', autospec=True)
def test_send_recruitment_tweets(mock_twitter_api):
    sce = TwitterDebriefExperimentController(
        experiment_name='twitter_dmca_debrief_experiment',
        db_session=db_session,
        required_keys=['name', 'randomizations', 'eligible_ids']
      )

    db_session.query(TwitterUserEligibility).delete()
    db_session.add(TwitterUserEligibility(id='1234567'))
    db_session.add(TwitterUserEligibility(id='7654321'))
    db_session.commit()

    api = mock_twitter_api.return_value

    d = { 'lang': 'en', 'screen_name': 'hihihi' }
    n = SimpleNamespace(**d)
    api.get_user.return_value = n

    d = { 'created_at': datetime.datetime.now() }
    n = SimpleNamespace(**d)
    api.user_timeline.return_value = [ n ]

    sce.send_recruitment_tweets(is_test=True)

    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == True and all_recruitment_attempts[1].sent == True

    try:
        sce.send_recruitment_tweets(is_test=True)
    except:
        assert False

    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2

    db_session.query(TwitterUserRecruitmentTweetAttempt).delete()
    db_session.commit()

    d = { 'lang': 'ru', 'screen_name': 'hihihi' }
    n = SimpleNamespace(**d)
    api.get_user.return_value = n

    sce.send_recruitment_tweets(is_test=True)

    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == False and all_recruitment_attempts[1].sent == False
    assert all_recruitment_attempts[0].lang == 'ru' and all_recruitment_attempts[1].lang == 'ru'

    db_session.query(TwitterUserRecruitmentTweetAttempt).delete()
    db_session.commit()

    d = { 'created_at': datetime.datetime.now() - datetime.timedelta(days=8) }
    n = SimpleNamespace(**d)
    api.user_timeline.return_value = [ n ]

    sce.send_recruitment_tweets(is_test=True)
    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == False and all_recruitment_attempts[1].sent == False

    db_session.query(TwitterUserRecruitmentTweetAttempt).delete()
    db_session.commit()

    d = { 'lang': 'en', 'screen_name': 'hihihi' }
    n = SimpleNamespace(**d)
    api.get_user.return_value = n

    d = { 'created_at': datetime.datetime.now() }
    n = SimpleNamespace(**d)
    api.user_timeline.return_value = [ n ]

    api.update_status.side_effect = tweepy.TweepError('test update_status fails')
    sce.send_recruitment_tweets(is_test=True)
    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == False and all_recruitment_attempts[1].sent == False
    assert all_recruitment_attempts[0].error_message is not None and all_recruitment_attempts[1].error_message is not None

    api.user_timeline.side_effect = tweepy.TweepError('test user_timeline fails')
    sce.send_recruitment_tweets(is_test=True)
    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == False and all_recruitment_attempts[1].sent == False
    assert all_recruitment_attempts[0].error_message is not None and all_recruitment_attempts[1].error_message is not None

    api.get_user.side_effect = tweepy.TweepError('test get_user fails')
    sce.send_recruitment_tweets(is_test=True)
    all_recruitment_attempts = db_session.query(TwitterUserRecruitmentTweetAttempt).all()
    assert len(all_recruitment_attempts) == 2
    assert all_recruitment_attempts[0].sent == False and all_recruitment_attempts[1].sent == False
    assert all_recruitment_attempts[0].error_message is not None and all_recruitment_attempts[1].error_message is not None
