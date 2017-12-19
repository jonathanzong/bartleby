"""
this file should:

run once

1. initialize an Experiment id
2. Load list of Lumen names TODO
3. Load randomizations
"""

import yaml, csv, os, inspect

from sqlalchemy import inspect as sa_inspect

from app.models import *

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), "..","..")

ENV = os.environ['CS_ENV'] = "development" # TODO don't leave this

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
        # self.log.error("{0}: Failure loading experiment yaml {1}".format(
          # self.__class__.__name__, experiment_file_path), str(exc))
        sys.exit(1)
    if(ENV not in experiment_config_all.keys()):
      # self.log.error("{0}: Cannot find experiment settings for {1} in {2}".format(
      #   self.__class__.__name__, ENV, experiment_file_path))
      sys.exit(1)

    experiment_config = experiment_config_all[ENV]
    for key in required_keys:
      if key not in experiment_config.keys():
        # self.log.error("{0}: Value missing from {1}: {2}".format(
        #   self.__class__.__name__, experiment_file_path, key))
        sys.exit(1)
    return experiment_config

  def load_experiment_config(self, required_keys, experiment_name):
    experiment_config = self.get_experiment_config(required_keys, experiment_name)
    experiment = self.db_session.query(Experiment).filter(Experiment.name == experiment_name).first()
    if(experiment is None):
      condition_keys = []

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

      experiment = Experiment(
        name = experiment_name,
        controller = self.__class__.__name__,
        settings_json = json.dumps(experiment_config).encode('utf-8')
      )
      self.db_session.add(experiment)
      self.db_session.commit()

    ### SET UP INSTANCE PROPERTIES
    self.experiment = experiment
    self.experiment_settings = json.loads(self.experiment.settings_json)


    self.experiment_name = experiment_name


  def row_as_dict(self, obj):
    return {c.key: getattr(obj, c.key)
            for c in sa_inspect(obj).mapper.column_attrs}

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

    if results_dict['tweet_removed'] == 'true':
      randomization = self.db_session.query(Randomization).filter_by(stratum='Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    else:
      randomization = self.db_session.query(Randomization).filter_by(stratum='Not Removed').filter_by(assigned=False).order_by(Randomization.id).first()
    randomization.assigned = True
    twitter_user_metadata.assignment_json = json.dumps(self.row_as_dict(randomization)).encode('utf-8')
    self.db_session.commit()


  def has_completed_study(self, user):
    twitter_user_metadata = self.db_session.query(TwitterUserMetadata).filter_by(twitter_user_id=user['id']).first()
    if twitter_user_metadata is not None:
      return twitter_user_metadata.completed_study_at is not None
    else:
      return False
