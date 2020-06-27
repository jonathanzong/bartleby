import yaml, csv, os, inspect, tweepy
import simplejson as json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import debriefing_api_keys

from time import sleep
from random import randint
from datetime import datetime
from string import printable
import urllib

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.sql import exists
from sqlalchemy import func

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
    db_session.close() 
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
    db_session.close() 

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
    db_session.close() 

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
    db_session.close() 

  def is_eligible(self, user, url_id):
    db_session = self.db_engine.new_session()
    experiment_name = self.get_experiment_name(url_id)
    participant_eligibility = db_session.query(ParticipantEligibility).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    db_session.close() 
    if ENV == "production":
      return participant_eligibility is not None
    else:
      return participant_eligibility is not None # or user['id'] == 393724541 or user['id'] == 'jzmit'

  def get_study_template(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    maybe_experiment = db_session.query(Experiment).filter_by(url_id=url_id).first()
    db_session.close() 
    if maybe_experiment is not None:
      return maybe_experiment.study_template
    return None

  def is_url_id_valid(self, url_id):
    if not isinstance(url_id, str):
      return False
    db_session = self.db_engine.new_session()
    match = db_session.query(Experiment).filter_by(url_id=url_id).first()
    db_session.close() 
    return match is not None

  def get_experiment_name(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    match = db_session.query(Experiment).filter_by(url_id=url_id).first()
    db_session.close() 
    if match is not None:
      return match.experiment_name
    return None

  def get_experiment_platform(self, url_id):
    if not isinstance(url_id, str):
      return None
    db_session = self.db_engine.new_session()
    maybe_experiment = db_session.query(Experiment).filter_by(url_id=url_id).first()
    db_session.close() 
    if maybe_experiment is not None:
      return maybe_experiment.platform
    return None

  def get_user_study_data(self, user, url_id):
    experiment_name = self.get_experiment_name(url_id)
    db_session = self.db_engine.new_session()
    participant_eligibility = db_session.query(ParticipantEligibility).filter_by(experiment_name=experiment_name, participant_user_id=user['id']).first()
    db_session.close() 
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
    db_session.close() 
    return opted_out_users

  def send_debriefing_status_report(self, from_email, to_email):
    db_session = self.db_engine.new_session()
    experiments = db_session.query(Experiment)
    for experiment in experiments:
      experiment_name = experiment.experiment_name
      login_count = db_session.query(func.count(ParticipantRecord.id)).filter_by(experiment_name=experiment_name).scalar()
      results = db_session.query(ParticipantSurveyResult).filter_by(experiment_name=experiment_name)
      results_json = [json.loads(row.survey_data) for row in results]
      form_completions = len(results_json)
      opt_outs = len([data for data in results_json if data['opt_out'] == "true" ])
      freeform_responses = len([data for data in results_json if 'improve_debrief' in data and data['improve_debrief']])

      content = f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>Logins: {login_count}<br/>Form completions: {form_completions}<br/>Opt outs: {opt_outs}<br/>Freeform responses: {freeform_responses}'
      print(content)
      print(debriefing_api_keys.SENDGRID_API_KEY)

      message = Mail(
          from_email=from_email,
          to_emails=to_email,
          subject=f'Debriefing Status Report: {experiment_name}',
          html_content=content)
      try:
          sg = SendGridAPIClient(debriefing_api_keys.SENDGRID_API_KEY)
          response = sg.send(message)
          print(response.status_code)
          print(response.body)
          print(response.headers)
      except Exception as e:
          print(e.message)
    db_session.close() 