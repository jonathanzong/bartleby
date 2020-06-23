from app.controllers.debriefing_controller import *

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_engine = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV))

sce = DebriefingController(db_engine=db_engine)

sce.send_debriefing_status_report('example@example.com')