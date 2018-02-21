"""
this file should:

1. initialize an Experiment id
2. Load list of eligible participant ids
3. Load randomizations
"""

import yaml, csv, os, inspect

from sqlalchemy import inspect as sa_inspect

from app.models import *

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), "..","..")

ENV = os.environ['CS_ENV']

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
      action.action_data = json.dumps(action_data_dict).encode('utf-8')
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


  def is_eligible(self, user):
    # twitter_user_eligibility = self.db_session.query(TwitterUserEligibility).filter_by(id=user['id']).first()
    # return twitter_user_eligibility is not None
    return True
