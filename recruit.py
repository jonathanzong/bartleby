from app.controllers.twitter_debrief_experiment_controller import *

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

sce = TwitterDebriefExperimentController(
    experiment_name='twitter_academic_debrief_experiment',
    db_session=db_session,
    required_keys=['name', 'randomizations', 'eligible_ids']
  )

sce.send_recruitment_tweets(is_test=True)
