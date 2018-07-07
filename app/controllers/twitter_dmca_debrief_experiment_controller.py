"""
this file should:

1. initialize an Experiment id
2. Load list of eligible participant ids
3. Load randomizations
"""

import yaml, csv, os, inspect, tweepy
import simplejson as json
import paypal_api_keys
import twitter_sender_api_keys

from time import sleep
from random import randint
from datetime import datetime
from string import printable

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.sql import exists

from app.models import *

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), "..","..")

ENV = os.environ['CS_ENV']

import paypalrestsdk
paypalrestsdk.configure({
  "mode": "live" if ENV == "production" else "sandbox",
  'client_id': paypal_api_keys.PAYPAL_CLIENT_ID,
  'client_secret': paypal_api_keys.PAYPAL_CLIENT_SECRET })

class TwitterDMCADebriefExperimentController:
  def __init__(self, experiment_name, db_session, required_keys):
    self.db_session = db_session

    self.load_experiment_config(required_keys, experiment_name)

  def get_experiment_config(self, required_keys, experiment_name):
    experiment_file_path = os.path.join(BASE_DIR, "config", "experiments", experiment_name) + ".yml"
    with open(experiment_file_path, 'r') as f:
      try:
        experiment_config_all = yaml.load(f)
      except yaml.YAMLError as exc:
        print("{0}: Failure loading experiment yaml {1}".format(
          self.__class__.__name__, experiment_file_path), str(exc))
        sys.exit(1)
    if(ENV not in experiment_config_all.keys()):
      print("{0}: Cannot find experiment settings for {1} in {2}".format(
        self.__class__.__name__, ENV, experiment_file_path))
      sys.exit(1)

    experiment_config = experiment_config_all[ENV]
    for key in required_keys:
      if key not in experiment_config.keys():
        print("{0}: Value missing from {1}: {2}".format(
          self.__class__.__name__, experiment_file_path, key))
        sys.exit(1)
    return experiment_config

  def load_experiment_config(self, required_keys, experiment_name):
    experiment_config = self.get_experiment_config(required_keys, experiment_name)
    experiment = self.db_session.query(Experiment).filter_by(name=experiment_name).first()

    if experiment is None:
      condition_keys = []

      experiment = Experiment(
        name = experiment_name,
        controller = self.__class__.__name__,
        settings_json = json.dumps(experiment_config).encode('utf-8')
      )
      self.db_session.add(experiment)
      self.db_session.commit()

      ## LOAD RANDOMIZED CONDITIONS (see CivilServant-Analysis)
      with open(os.path.join(BASE_DIR, "config", "experiments", experiment_config['randomizations']), "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
          randomization = Randomization(
            randomization_id = row['id'],
            stratum          = row['stratum'],
            block_id         = row['block.id'],
            block_size       = row['block.size'],
            treatment        = row['treatment'],
            assigned         = False
          )
          self.db_session.add(randomization)

      ## LOAD eligible twitter user ids
      with open(os.path.join(BASE_DIR, "config", "experiments", experiment_config['eligible_ids']), "r") as f:
        reader = csv.reader(f)
        for row in reader:
          twitter_user_eligibility = TwitterUserEligibility(id = row[0])
          self.db_session.add(twitter_user_eligibility)

      self.db_session.commit()

    ### SET UP INSTANCE PROPERTIES
    self.experiment = experiment
    self.experiment_settings = json.loads(self.experiment.settings_json)


    self.experiment_name = experiment_name


  def row_as_dict(self, obj):
    return {c.key: getattr(obj, c.key)
            for c in sa_inspect(obj).mapper.column_attrs}

  def user_exists(self, user):
    maybe_twitter_user = self.db_session.query(TwitterUser).filter_by(id=user['id']).first()
    maybe_twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    return maybe_twitter_user is not None and maybe_twitter_user_metadata is not None

  def create_user_if_not_exists(self, user):
    maybe_twitter_user = self.db_session.query(TwitterUser).filter_by(id=user['id']).first()
    if maybe_twitter_user is None:
      twitter_user = TwitterUser(id=user['id'],
                                 screen_name=user['screen_name'],
                                 created_at=user['created_at'],
                                 lang=user['lang'])
      self.db_session.add(twitter_user)
    maybe_twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    if maybe_twitter_user_metadata is None:
      twitter_user_metadata = TwitterUserMetadata(twitter_user_id=user['id'],
                                                  experiment_id=self.experiment.id,
                                                  user_json=json.dumps(user).encode('utf-8'))
      self.db_session.add(twitter_user_metadata)
    if maybe_twitter_user is None or maybe_twitter_user_metadata is None:
      self.db_session.commit()

  def insert_or_update_survey_result(self, user, results_dict):
    res = self.db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()

    if res is not None:
      # load pre-existing response and merge in new answers
      data = json.loads(res.survey_data)
      merged_results = data.copy()
      merged_results.update(results_dict)
      res.survey_data = json.dumps(merged_results).encode('utf-8')

      self.db_session.commit()
    else:
      # create new entry
      res = TwitterUserSurveyResult(twitter_user_id=user['id'],
                                    survey_data=json.dumps(results_dict).encode('utf-8'))
      self.db_session.add(res)
      self.db_session.commit()

  def assign_randomization(self, user, results_dict):
    twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    twitter_user_metadata.tweet_removed = (results_dict['tweet_removed'] == 'true')
    if twitter_user_metadata.assignment_json is not None:
      assignment = json.loads(twitter_user_metadata.assignment_json)
      if (assignment['stratum'] == 'Removed') is not (results_dict['tweet_removed'] == 'true'):
        # changed their answer, clear the old assignment and continue
        randomization = self.db_session.query(Randomization).filter_by(id=assignment['id']).first()
        randomization.assigned = False
        twitter_user_metadata.assignment_json = None
        self.db_session.commit()
      else:
        # same answer, keep randomization
        return

    if results_dict['tweet_removed'] == 'true':
      randomization = self.db_session.query(Randomization).filter_by(stratum='Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    else:
      randomization = self.db_session.query(Randomization).filter_by(stratum='Not Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    randomization.assigned = True
    twitter_user_metadata.assignment_json = json.dumps(self.row_as_dict(randomization)).encode('utf-8')
    self.db_session.commit()

  def get_user_conditions(self, user):
    twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    assignment = json.loads(twitter_user_metadata.assignment_json)
    treatment = assignment['treatment']
    treatment_binary = format(treatment, '03b') # convert int to binary string

    return {
      'in_control_group': treatment_binary[0] == '1',
      'show_table': treatment_binary[1] == '1',
      'show_visualization': treatment_binary[2] == '1',
    }

  def record_user_action(self, user, action_type, action_data_dict):
    action = ExperimentAction(
      experiment_id=self.experiment.id,
      action_type=action_type,
      twitter_user_id=user['id'] if user is not None else None,
    )
    if action_data_dict is not None:
      action_str = json.dumps(action_data_dict)
      if 'check_http' in action_str:
        return
      action.action_data = action_str.encode('utf-8')
    self.db_session.add(action)
    self.db_session.commit()

  def mark_user_completed(self, user):
    survey_result = self.db_session.query(TwitterUserSurveyResult).filter_by(twitter_user_id=user['id']).first()
    if survey_result is not None:
      # mark user complete
      results = json.loads(survey_result.survey_data)
      required_fields = ["tweet_removed", "click_tweet", "would_delete", "society_benefit", "personal_benefit", "collection_surprised", "glad_in_study", "share_results", "vote_study","improve_debrief"]
      completed = all([(field in results) for field in required_fields])
      if completed:
        twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
        twitter_user_metadata.completed_study_at = datetime.datetime.now()
        self.db_session.commit()
        return True
      else:
        return False
    else:
      return False

  def has_completed_study(self, user):
    twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    if twitter_user_metadata is not None:
      return twitter_user_metadata.completed_study_at is not None
    else:
      return False

  # return value is an error message
  def send_paypal_payout(self, user, email_address, amount_dollars):
    sender_batch_id = user['id']
    payout = paypalrestsdk.Payout({
      "sender_batch_header": {
        "sender_batch_id": sender_batch_id,
        "email_subject": "You have a payment"
      },
      "items": [
        {
          "recipient_type": "EMAIL",
          "amount": {
            "value": amount_dollars,
            "currency": "USD"
          },
          "receiver": email_address,
          "note": "Thank you for participating in our research!",
          "sender_item_id": "item_1"
        }
      ]
    })
    try:
      twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
      if twitter_user_metadata.completed_study_at is None:
        return 'The survey has not been submitted yet. If this is in error, please contact Jonathan at jz7@cs.princeton.edu'

      days_since_started = (datetime.datetime.now() - twitter_user_metadata.initial_login_at).days

      if days_since_started > 7:
        return 'The 7 day window to complete the survey for compensation has expired. If this is in error, please contact Jonathan at jz7@cs.princeton.edu'
      if twitter_user_metadata.paypal_sender_batch_id is not None:
        return 'The compensation email has been sent through Paypal. If you do not receive it within 24 hours, please contact Jonathan at jz7@cs.princeton.edu'

      payout.create()

      # store sender_batch_id
      twitter_user_metadata.paypal_sender_batch_id = sender_batch_id
      self.db_session.add(twitter_user_metadata)
      self.db_session.commit()
    except Exception as e:
      # TODO log e
      return 'An error occured while sending the compensation. If this happens repeatedly, please contact Jonathan at jz7@cs.princeton.edu'

  def has_sent_payout(self, user):
    twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    if twitter_user_metadata is not None:
      return twitter_user_metadata.paypal_sender_batch_id is not None
    else:
      return False

  def is_eligible(self, user):
    twitter_user_eligibility = self.db_session.query(TwitterUserEligibility).filter_by(id=user['id']).first()
    if ENV == "production":
      return twitter_user_eligibility is not None
    else:
      return twitter_user_eligibility is not None or user['id'] == 393724541
    # TODO update the list
    # return True

  def get_user_compensation_amount(self, user):
    attempt = self.db_session.query(TwitterUserRecruitmentTweetAttempt).filter_by(twitter_user_id=user['id']).first()
    if attempt is not None:
      return attempt.amount_dollars
    else:
      return 0

  def get_user_study_template(self, user):
    attempt = self.db_session.query(TwitterUserRecruitmentTweetAttempt).filter_by(twitter_user_id=user['id']).first()
    if attempt is not None:
      return attempt.study_template if attempt.study_template is not None else "dmca"
    else:
      return "dmca"

  #####

  def send_recruitment_tweets(self, amount_dollars=0, study_template=None, is_test=False):
    auth = tweepy.OAuthHandler(twitter_sender_api_keys.consumer_key, twitter_sender_api_keys.consumer_secret)
    auth.set_access_token(twitter_sender_api_keys.access_token, twitter_sender_api_keys.access_token_secret)
    api = tweepy.API(auth)

    # TODO factor this out into a conf file or model property or something
    if study_template == 'marvel':
      if amount_dollars:
        tweet_body = "Are you a fan of the Marvel Cinematic Universe movies? 🎥 Answer a few questions for @ohnobackspace’s research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Are you a fan of the Marvel Cinematic Universe movies? 🎥 Answer a few questions for @ohnobackspace’s research to help us learn more"
    elif study_template == 'munger':
      if amount_dollars:
        tweet_body = "Have you been part of an exchange on Twitter with racially-charged comments? Answer a few questions for @ohnobackspace’s research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Have you been part of an exchange on Twitter with racially-charged comments? Answer a few questions for @ohnobackspace’s research to help us learn more"
    elif study_template == 'pacsocial':
      if amount_dollars:
        tweet_body = "Do you interact with bots on Twitter? Answer a few questions for @ohnobackspace’s research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Do you interact with bots on Twitter? Answer a few questions for @ohnobackspace’s research to help us learn more"
    elif study_template == 'academic':
      if amount_dollars:
        tweet_body = "Are you a social science and/or computing researcher? Answer a few questions for @ohnobackspace’s research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Are you a social science and/or computing researcher? Answer a few questions for @ohnobackspace’s research to help us learn more"
    elif study_template == 'advocacy':
      if amount_dollars:
        tweet_body = "Do you follow advocacy NGOs on Twitter? Answer a few questions for @ohnobackspace’s research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Do you follow advocacy NGOs on Twitter? Answer a few questions for @ohnobackspace’s research to help us learn more"
    else: # default to dmca
      if amount_dollars:
        tweet_body = "Have your tweets ever been taken down for copyright reasons? ©💥 Answer a few questions for @ohnobackspace's research, and we'll compensate you ${0} on Paypal–credit you can use for your next cup of coffee".format(amount_dollars)
      else:
        tweet_body = "Have your tweets ever been taken down for copyright reasons? ©💥 Answer a few questions for @ohnobackspace's research to help others like you"

    on_time = datetime.time(9,30)
    off_time = datetime.time(21,30)

    while True:
      if not is_test:
        now_time = datetime.datetime.now().time()
        if now_time < on_time or now_time > off_time:
          sleep(60 * 60)
          continue

      next_eligible_twitter_user = self.db_session.query(TwitterUserEligibility).filter(~ exists().where(TwitterUserRecruitmentTweetAttempt.twitter_user_id==TwitterUserEligibility.id)).first()

      if next_eligible_twitter_user is None:
        break

      u_id = next_eligible_twitter_user.id

      emojiless_body = ''.join(filter(lambda x: x in printable, tweet_body))
      attempt = TwitterUserRecruitmentTweetAttempt(twitter_user_id=u_id, tweet_body=emojiless_body, amount_dollars=amount_dollars, study_template=study_template)
      attempt.sent = False

      try:
        if not is_test:
          sleep(10)
        user_object = api.get_user(user_id=u_id)
      except tweepy.TweepError as e:
        attempt.error_message=e.reason
        self.db_session.add(attempt)
        self.db_session.commit()
        continue

      should_tweet = True

      attempt.lang = user_object.lang

      if user_object.lang != 'en':
        should_tweet = False

      try:
        if not is_test:
          sleep(10)
        user_statuses = api.user_timeline(user_id=u_id, count=1)
      except tweepy.TweepError as e:
        attempt.error_message=e.reason
        self.db_session.add(attempt)
        self.db_session.commit()
        continue

      if len(user_statuses) > 0:
        attempt.last_tweeted_at = user_statuses[0].created_at
        last_tweet_days = (datetime.datetime.now() - user_statuses[0].created_at).days
        if last_tweet_days > 7:
          should_tweet = False

      if should_tweet:
        try:
          if not is_test:
            send_text = '@' + user_object.screen_name + ' ' + tweet_body + ' http://debrief.cs.princeton.edu/?u=' + u_id
            if amount_dollars:
              send_text += '&c=' + str(amount_dollars)
            if study_template is not None:
              send_text += '&t=' + study_template
            api.update_status(send_text)
          attempt.sent = True
        except tweepy.TweepError as e:
          attempt.error_message=e.reason

      print('attempted user id %s' % u_id)
      self.db_session.add(attempt)
      self.db_session.commit()

      if not is_test:
        delay = randint(13 * 60, 15 * 60)
        sleep(delay)


