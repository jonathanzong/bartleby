from app.controllers.twitter_debrief_experiment_controller import *

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

DEFAULT_STUDY = 'dmca'  # set default template for direct link to homepage here

sce = TwitterDebriefExperimentController(
    study_id='twitter_dmca_debrief_experiment',
    default_study=DEFAULT_STUDY,
    db_session=db_session,
    required_keys=['name', 'user_data_dir']
  )

with open('opted_out_users', 'w') as out:
  for user_id in sce.get_opted_out_users():
    out.write(user_id + '\n')
