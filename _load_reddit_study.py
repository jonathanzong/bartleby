from app.controllers.debriefing_controller import *

import csv
import json

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

## create experiment record

experiment = Experiment(
  url_id='',
  experiment_name='',
  study_template='')
db_session.add(experiment)

## create participant eligibility records

data = {}

with open('r-feminism-study-data-merged-05.12.2020.csv') as datafile:
  reader = csv.DictReader(datafile)
  for row in reader:
    data[row["id"]] = json.dumps(row)

with open('r-feminism-account-mapping-05.12.2020.csv') as mappingfile:
  reader = csv.DictReader(mappingfile)
  for row in reader:
    name = row['username'].casefold()
    uid = row['uuid']
    study_data_json = data[uid]
    del study_data_json['id']
    maybe_participant_eligibility = db_session.query(ParticipantEligibility).filter_by(experiment_name=experiment_name, participant_user_id=name).first()
    if not maybe_participant_eligibility:
      participant_eligibility = ParticipantEligibility(experiment_name=experiment_name, participant_user_id = name, study_data_json = study_data_json.encode('utf-8'))
      db_session.add(participant_eligibility)
  db_session.commit()
