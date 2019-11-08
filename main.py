import twitter_api_keys
import reddit_api_keys
import pybrake_key
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

from app.controllers.twitter_debrief_experiment_controller import *

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key
app.config['PYBRAKE'] = dict(
    host=pybrake_key.PYBRAKE_HOST,
    project_id=1212,
    project_key=pybrake_key.PYBRAKE_KEY,
)
app = pybrake.flask.init_app(app)

consumer_key = twitter_api_keys.TWITTER_CONSUMER_KEY
consumer_secret = twitter_api_keys.TWITTER_CONSUMER_SECRET

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

R_FEMINISM_STUDY_ID = '77ef689a7e9b-r-feminism'

def is_logged_in():
  return 'user' in session and sce.user_exists(session['user'])

@app.route('/', defaults={'study_id': None})
@app.route('/<study_id>')
def index(study_id):
  session['study_id'] = study_id
  if is_logged_in():
    return redirect(url_for_study('debrief'))

  amount_dollars = int(request.args.get('c')) if request.args.get('c') else 0

  sce.record_user_action(None, 'page_view', {'page': 'index', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  study_template = request.args.get('t') if request.args.get('t') else DEFAULT_STUDY
  if study_id == R_FEMINISM_STUDY_ID: # TODO
    study_template = 'r-feminism'
  extra_data = json.loads(request.args.get('x')) if request.args.get('x') else None
  return render_template(study_template + '/index.html', amount_dollars=amount_dollars, extra_data=extra_data)

@app.route('/debrief', methods=('GET', 'POST'), defaults={'study_id': None})
@app.route('/debrief/<study_id>', methods=('GET', 'POST'))
def debrief(study_id):
  session['study_id'] = study_id
  if not is_logged_in():
    return redirect(url_for_study('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  sce.record_user_action(user, 'page_view', {'page': 'debrief', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  # handle form submission (ajax call)
  form = SurveyForm()
  if request.data:
    results_dict = json.loads(request.data)
    results_dict['twitter_user_id'] = user['id']

    if 'opt_out' in results_dict and results_dict['opt_out']:
      results_dict['opt_out'] = 'true'
    else:
      results_dict['opt_out'] = 'false'

    sce.insert_or_update_survey_result(user, results_dict)

    sce.record_user_action(user, 'form_submit', {'page': 'debrief'})
  # handle form submission (submit button)
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    if 'opt_out' in results_dict:
      results_dict['opt_out'] = 'true'
    else:
      results_dict['opt_out'] = 'false'

    sce.insert_or_update_survey_result(user, results_dict)

    sce.record_user_action(user, 'form_submit', {'page': 'debrief'})

  study_template = sce.get_user_study_template(user)
  if study_id == R_FEMINISM_STUDY_ID: # TODO
    study_template = 'r-feminism'
  return render_template(study_template + '/debrief.html', user=user, form=form, url_for_study=url_for_study)

@app.route('/ineligible')
def ineligible():
  if not 'user' in session:
    return redirect(url_for_study('index'))
  user = session['user']

  if sce.is_eligible(user):
    return redirect(url_for_study('debrief'))

  sce.record_user_action(user, 'page_view', {'page': 'ineligible', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  return render_template('ineligible.html')

@app.route('/login/<platform>')
def login(platform):
  if is_logged_in():
    return redirect(url_for_study('debrief'))

  sce.record_user_action(None, 'login_attempt', None)

  if platform == 'reddit':
    redirect_uri = url_for('oauth_authorized', platform='reddit', _external=True)
    reddit = praw.Reddit(client_id=reddit_api_keys.REDDIT_CLIENT_ID,
                       client_secret=reddit_api_keys.REDDIT_CLIENT_SECRET,
                       redirect_uri=redirect_uri,
                       user_agent='debriefing.media.mit.edu')

    state_string = str(uuid.uuid4())
    session['state_string'] = state_string

    auth_url = reddit.auth.url(['identity'], state_string, 'permanent')
    return redirect(auth_url)
  elif platform == 'twitter':
    callback_url = url_for('oauth_authorized', platform='twitter', _external=True)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
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
    sce.record_user_action(user, 'logout', None)
    del session['user']
  return redirect(url_for_study('index'))

@app.route('/oauth_authorized', defaults={'platform': 'twitter'})
@app.route('/oauth_authorized/<platform>')
def oauth_authorized(platform):
  if platform == 'reddit':
    user = authorize_reddit_user()
  elif platform == 'twitter':
    user = authorize_twitter_user()
  if user is None:
    return redirect(url_for_study('index'))
  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  study_data = sce.get_user_study_data(user)
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
    old_user = session['user'].copy()
    session['user'].update(study_data)
    session['user'].update(old_user) # don't let study_data columns overwrite user properties

  # create user if not exists
  sce.create_user_if_not_exists(user)

  sce.record_user_action(user, 'login_success', None)

  return redirect(url_for_study('debrief'))

def authorize_twitter_user():
  verifier = request.args.get('oauth_verifier')

  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
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
  reddit = praw.Reddit(client_id=reddit_api_keys.REDDIT_CLIENT_ID,
                     client_secret=reddit_api_keys.REDDIT_CLIENT_SECRET,
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
  user = session['user']
  return user

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for_study('index'))

def url_for_study(route):
  study_id = session['study_id'] if 'study_id' in session else None
  return url_for(route, study_id=study_id)
