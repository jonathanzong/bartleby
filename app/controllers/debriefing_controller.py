import yaml, csv, os, inspect, tweepy
import simplejson as json

from time import sleep
from random import randint
from datetime import datetime
from string import printable
import urllib

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.sql import exists

from app.models import *

# BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), "..","..")

ENV = os.environ['CS_ENV']

class DebriefingController:
  def __init__(self, db_engine):
    self.db_engine = db_engine

  def user_exists(self, user, url_id):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    maybe_participant = db_session.query(ParticipantRecord).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    return maybe_participant is not None

  def create_user_if_not_exists(self, user, url_id):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    maybe_participant = db_session.query(ParticipantRecord).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    if maybe_participant is None:
      participant = ParticipantRecord(participant_user_id=user['id'],
                                 experiment_name=experiment_name,
                                 user_json=json.dumps(user).encode('utf-8'))
      db_session.add(participant)
      db_session.commit()

  def insert_or_update_survey_result(self, user, url_id, results_dict):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    res = db_session.query(ParticipantSurveyResult).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()

    if res is not None:
      # load pre-existing response and merge in new answers
      data = json.loads(res.survey_data)
      merged_results = data.copy()
      merged_results.update(results_dict)
      res.survey_data = json.dumps(merged_results).encode('utf-8')

      db_session.commit()
    else:
      # create new entry
      res = ParticipantSurveyResult(experiment_name=experiment_name, participant_user_id=user['id'],
                                    survey_data=json.dumps(results_dict).encode('utf-8'))
      db_session.add(res)
      db_session.commit()

  def record_user_action(self, user, url_id, action_type, action_data_dict=None):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    action = ExperimentAction(
      experiment_name=experiment_name,
      participant_user_id=user['id'] if user is not None else None,
      action_type=action_type,
    )
    if action_data_dict is not None:
      action_str = json.dumps(action_data_dict)
      if 'check_http' in action_str:
        return
      action.action_data = action_str.encode('utf-8')
    db_session.add(action)
    db_session.commit()

  def is_eligible(self, user, url_id):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    participant_eligibility = db_session.query(ParticipantEligibility).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    if ENV == "production":
      return participant_eligibility is not None
    else:
      return participant_eligibility is not None # or user['id'] == 393724541 or user['id'] == 'jzmit'

  def get_study_template(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    maybe_experiment = db_session.query(Experiment).filter_by(url_id=url_id).first()
    if maybe_experiment is not None:
      return maybe_experiment.study_template
    return None

  def is_url_id_valid(self, url_id):
    if not isinstance(url_id, str):
      return False
    db_session = self.db_engine.new_session()
    match = db_session.query(Experiment).filter_by(url_id=url_id).first()
    return match is not None

  def get_experiment_name(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    match = db_session.query(Experiment).filter_by(url_id=url_id).first()
    if match is not None:
      return match.experiment_name
    return None

  def get_experiment_platform(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    maybe_experiment = db_session.query(Experiment).filter_by(url_id=url_id).first()
    if maybe_experiment is not None:
      return maybe_experiment.platform
    return None

  def get_user_study_data(self, user, url_id):
    experiment_name = self.get_experiment_name(url_id)
    db_session = self.db_engine.new_session()
    participant_eligibility = db_session.query(ParticipantEligibility).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    if participant_eligibility is not None:
      return json.loads(participant_eligibility.study_data_json) if participant_eligibility.study_data_json is not None else None
    return None

  ####

  def get_opted_out_users(self, url_id):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    res = db_session.query(ParticipantSurveyResult).filter_by(experiment_name=experiment_name)
    opted_out_users = []
    for row in res:
      data = json.loads(row.survey_data)
      if data['opt_out'] == "true":
        opted_out_users.append(row.participant_user_id)
    return opted_out_users


