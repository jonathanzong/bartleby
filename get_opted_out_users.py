from app.controllers.debriefing_controller import *

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_engine = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV))

sce = DebriefingController(db_engine=db_engine)

url_id = ''

with open('opted_out_users', 'w') as out:
  for user_id in sce.get_opted_out_users(url_id):
    out.write(user_id + '\n')
