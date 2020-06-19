import debriefing_api_keys
import tweepy
import json
import os
import datetime
import praw
import uuid

from flask import Flask, session, request, redirect, url_for, render_template

from utils.common import DbEngine
from app.models import *
from app.forms import *

import pybrake.flask

from app.controllers.debriefing_controller import *

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key
app.config['PYBRAKE'] = dict(
    host=debriefing_api_keys.PYBRAKE_HOST,
    project_id=1212,
    project_key=debriefing_api_keys.PYBRAKE_KEY,
)
app = pybrake.flask.init_app(app)

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

sce = DebriefingController(db_session=db_session)

def is_logged_in():
  return 'user' in session and 'url_id' in session and sce.user_exists(session['user'], session['url_id'])

@app.route('/')
def no_experiment():
  if 'url_id' in session:
    return redirect(url_for_experiment('index'))
  return render_template('index.html')

@app.route('/<url_id>')
def index(url_id):
  if not sce.is_url_id_valid(url_id):
    return redirect(url_for('no_experiment'))

  session['url_id'] = url_id
  if is_logged_in():
    return redirect(url_for_experiment('debrief'))

  amount_dollars = int(request.args.get('c')) if request.args.get('c') else 0

  sce.record_user_action(None, url_id, 'page_view', {'page': 'index', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  extra_data = json.loads(request.args.get('x')) if request.args.get('x') else None

  study_template = sce.get_study_template(url_id)
  return render_template(study_template + '/index.html', amount_dollars=amount_dollars, extra_data=extra_data)

@app.route('/<url_id>/debrief', methods=('GET', 'POST'))
def debrief(url_id):
  if not sce.is_url_id_valid(url_id):
    return redirect(url_for('no_experiment'))

  session['url_id'] = url_id
  if not is_logged_in():
    return redirect(url_for_experiment('index'))
  user = session['user']

  if not sce.is_eligible(user, url_id):
    return redirect(url_for_experiment('ineligible'))

  sce.record_user_action(user, url_id, 'page_view', {'page': 'debrief', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  populate_user_session(user, url_id)

  # handle form submission (ajax call)
  form = SurveyForm()
  if request.data:
    results_dict = json.loads(request.data)
    results_dict['participant_user_id'] = user['id']

    if 'opt_out' in results_dict and results_dict['opt_out']:
      results_dict['opt_out'] = 'true'
    else:
      results_dict['opt_out'] = 'false'

    sce.insert_or_update_survey_result(user, url_id, results_dict)

    sce.record_user_action(user, url_id, 'form_submit', {'page': 'debrief'})
  # handle form submission (submit button)
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['participant_user_id'] = user['id']

    if 'opt_out' in results_dict:
      results_dict['opt_out'] = 'true'
    else:
      results_dict['opt_out'] = 'false'

    sce.insert_or_update_survey_result(user, url_id, results_dict)

    sce.record_user_action(user, url_id, 'form_submit', {'page': 'debrief'})

  study_template = sce.get_study_template(url_id)
  return render_template(study_template + '/debrief.html', user=user, form=form, url_for_experiment=url_for_experiment)

@app.route('/<url_id>/ineligible')
def ineligible(url_id):
  if not sce.is_url_id_valid(url_id):
    return redirect(url_for('no_experiment'))

  session['url_id'] = url_id
  if not 'user' in session:
    return redirect(url_for_experiment('index'))
  user = session['user']

  if sce.is_eligible(user, url_id):
    return redirect(url_for_experiment('debrief'))

  sce.record_user_action(user, url_id, 'page_view', {'page': 'ineligible', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  return render_template('ineligible.html')

@app.route('/login/<platform>')
def login(platform):
  if is_logged_in():
    return redirect(url_for_experiment('debrief'))

  sce.record_user_action(None, session['url_id'] if 'url_id' in session else None, 'login_attempt', None)

  if platform == 'reddit':
    redirect_uri = url_for('oauth_authorized', platform='reddit', _external=True)
    reddit = praw.Reddit(client_id=debriefing_api_keys.REDDIT_CLIENT_ID,
                       client_secret=debriefing_api_keys.REDDIT_CLIENT_SECRET,
                       redirect_uri=redirect_uri,
                       user_agent='debriefing.media.mit.edu') #TODO maybe not hardcode the debriefing site url in places

    state_string = str(uuid.uuid4())
    session['state_string'] = state_string

    auth_url = reddit.auth.url(['identity'], state_string, 'permanent')
    return redirect(auth_url)
  elif platform == 'twitter':
    callback_url = url_for('oauth_authorized', platform='twitter', _external=True)
    auth = tweepy.OAuthHandler(debriefing_api_keys.TWITTER_CONSUMER_KEY, debriefing_api_keys.TWITTER_CONSUMER_SECRET, callback_url)
    try:
      auth_url = auth.get_authorization_url()
      session['request_token'] = auth.request_token
      return redirect(auth_url)
    except tweepy.TweepError:
      return 'Error! Failed to get request token.'

@app.route('/logout')
def logout():
  if is_logged_in():
    user = session['user']
    sce.record_user_action(user, session['url_id'] if 'url_id' in session else None, 'logout', None)
    del session['user']
  return redirect(url_for_experiment('index'))

@app.route('/oauth_authorized', defaults={'platform': 'twitter'})
@app.route('/oauth_authorized/<platform>')
def oauth_authorized(platform):
  url_id = session['url_id']
  if platform == 'reddit':
    user = authorize_reddit_user()
  elif platform == 'twitter':
    user = authorize_twitter_user()
  if user is None:
    return redirect(url_for_experiment('index'))
  if not sce.is_eligible(user, url_id):
    return redirect(url_for_experiment('ineligible'))

  # create user if not exists
  sce.create_user_if_not_exists(user, url_id)

  sce.record_user_action(user, url_id, 'login_success', None)

  return redirect(url_for_experiment('debrief'))

def authorize_twitter_user():
  verifier = request.args.get('oauth_verifier')

  auth = tweepy.OAuthHandler(debriefing_api_keys.TWITTER_CONSUMER_KEY, debriefing_api_keys.TWITTER_CONSUMER_SECRET)
  token = session['request_token']
  del session['request_token']
  auth.request_token = token

  try:
    auth.get_access_token(verifier)
    api = tweepy.API(auth)
    user = api.me()

    today = datetime.datetime.now()
    created = user.created_at
    account_age = today.year - created.year - ((today.month, today.day) < (created.month, created.day))

    session['user'] = {
      'id': user.id,
      'screen_name': user.screen_name,
      'default_profile_image': "yes" if user.default_profile_image else "no",
      'statuses_count': user.statuses_count,
      'verified': "yes" if user.verified else "no",
      'created_at': user.created_at.isoformat(),
      'lang': user.lang,
      'account_age': account_age
    }
    session['auth_user'] = session['user'].copy()
    user = session['user']
    return user
  except tweepy.TweepError:
    # return 'Error! Failed to get access token.'
    return None

def authorize_reddit_user():
  if 'state_string' not in session:
    return None

  error = request.args.get('error')
  if error == 'access_denied':
    return None

  state = request.args.get('state')
  sent_state = session['state_string']
  del session['state_string']
  if not sent_state == state:
    return None

  redirect_uri = url_for('oauth_authorized', platform='reddit', _external=True)
  reddit = praw.Reddit(client_id=debriefing_api_keys.REDDIT_CLIENT_ID,
                     client_secret=debriefing_api_keys.REDDIT_CLIENT_SECRET,
                     redirect_uri=redirect_uri,
                     user_agent='debriefing.media.mit.edu')

  authorization_code = request.args.get('code')
  refresh_token = reddit.auth.authorize(authorization_code)

  user = reddit.user.me() # PRAW Redditor instance

  today = datetime.datetime.now()
  created = datetime.datetime.fromtimestamp(user.created_utc)
  account_age = today.year - created.year - ((today.month, today.day) < (created.month, created.day))

  session['user'] = {
    'id': user.name.casefold(), # reddit usernames cannot be changed. use username normalized to lowercase as id
    'screen_name': user.name,
    'created_at': created.isoformat(),
    'account_age': account_age
  }
  session['auth_user'] = session['user'].copy()
  user = session['user']
  return user

def populate_user_session(user, url_id):
  platform = sce.get_experiment_platform(url_id)
  study_data = sce.get_user_study_data(user, url_id)
  if study_data is not None: # TODO: this needs to be generalized somehow to be configurable per study
    if platform == 'reddit':
      study_data["assignment_datetime"] = datetime.datetime.strptime(study_data["assignment_datetime"], "%Y-%m-%d %H:%M:%S")
      study_data["assignment_datetime"] = study_data["assignment_datetime"].strftime("%B %-d, %Y")
      pass
    elif platform == 'twitter':
      study_data["account_created_at"] = study_data["created_at"]
      del study_data["created_at"]
      study_data["account_created_at"] = datetime.datetime.strptime(study_data["account_created_at"], "%Y-%m-%d %H:%M:%S")
      study_data["notice_date"] = datetime.datetime.strptime(study_data["notice_date"], "%Y-%m-%d %H:%M:%S")
      study_data["start_date"] = study_data["notice_date"] - datetime.timedelta(days=23)
      study_data["end_date"] = study_data["notice_date"] + datetime.timedelta(days=23)
      study_data["account_created_at"] = study_data["account_created_at"].strftime("%B %-d, %Y")
      study_data["notice_date"] = study_data["notice_date"].strftime("%B %-d, %Y")
      study_data["start_date"] = study_data["start_date"].strftime("%B %-d, %Y")
      study_data["end_date"] = study_data["end_date"].strftime("%B %-d, %Y")
    session['user'].update(study_data)
    session['user'].update(session['auth_user']) # don't let study_data columns overwrite user properties

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for_experiment('index'))

def url_for_experiment(route):
  url_id = session['url_id'] if 'url_id' in session else None
  if url_id is not None:
    return url_for(route, url_id=url_id)
  else:
    return url_for('no_experiment')