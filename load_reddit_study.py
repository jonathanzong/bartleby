from app.controllers.twitter_debrief_experiment_controller import *

import csv
import json

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()


data = {}

with open('r-feminism-study-data-merged-10.17.2019.txt') as datafile:
  reader = csv.DictReader(datafile)
  for row in reader:
    data[row["id"]] = json.dumps(row)

with open('r-feminism-account-mapping-10.17.2019.csv') as mappingfile:
  reader = csv.DictReader(mappingfile)
  for row in reader:
    name = row['username'].casefold()
    uid = row['uuid']
    study_data_json = data[uid]
    del study_data_json['id']
    maybe_twitter_user_eligibility = db_session.query(TwitterUserEligibility).filter_by(id=name).first()
    if not maybe_twitter_user_eligibility:
      twitter_user_eligibility = TwitterUserEligibility(id = name, study_data_json = study_data_json.encode('utf-8'))
      db_session.add(twitter_user_eligibility)
  db_session.commit()
