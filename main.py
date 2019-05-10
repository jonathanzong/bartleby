import twitter_api_keys
import tweepy
import json
import os
import datetime

from flask import Flask, session, request, redirect, url_for, render_template

from utils.common import DbEngine
from app.models import *
from app.forms import *

from app.controllers.twitter_debrief_experiment_controller import *

app = Flask(__name__)
app.secret_key = 'such secret very key!' # session key

consumer_key = twitter_api_keys.TWITTER_CONSUMER_KEY
consumer_secret = twitter_api_keys.TWITTER_CONSUMER_SECRET

ENV = os.environ['CS_ENV']

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
db_session = DbEngine(CONFIG_DIR + "/{env}.json".format(env=ENV)).new_session()

DEFAULT_STUDY = 'dmca'  # set default template for direct link to homepage here

sce = TwitterDebriefExperimentController(
    experiment_name='twitter_dmca_debrief_experiment',
    default_study=DEFAULT_STUDY,
    db_session=db_session,
    required_keys=['name', 'user_data_dir']
  )

def is_logged_in():
  return 'user' in session and sce.user_exists(session['user'])

@app.route('/')
def index():
  if is_logged_in():
    return redirect(url_for('debrief'))
  amount_dollars = int(request.args.get('c')) if request.args.get('c') else 0

  sce.record_user_action(None, 'page_view', {'page': 'index', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  study_template = request.args.get('t') if request.args.get('t') else DEFAULT_STUDY
  extra_data = json.loads(request.args.get('x')) if request.args.get('x') else None
  return render_template(study_template + '/01-index.html', amount_dollars=amount_dollars, extra_data=extra_data)

@app.route('/debrief', methods=('GET', 'POST'))
def debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  sce.record_user_action(user, 'page_view', {'page': 'debrief', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  # handle form submission
  form = SurveyForm()
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

    # return redirect(url_for('complete'))
  study_template = sce.get_user_study_template(user)
  return render_template(study_template + '/05-debrief.html', user=user, form=form)

@app.route('/ineligible')
def ineligible():
  if is_logged_in():
    return redirect(url_for('debrief'))
  user = session['user']

  if sce.is_eligible(user):
    return redirect(url_for('debrief'))

  sce.record_user_action(user, 'page_view', {'page': 'ineligible', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  return render_template('ineligible.html')

@app.route('/login')
def login():
  if is_logged_in():
    return redirect(url_for('debrief'))

  sce.record_user_action(None, 'login_attempt', None)

  callback_url = url_for('oauth_authorized', _external=True)
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
  try:
    redirect_url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(redirect_url)
  except tweepy.TweepError:
    return 'Error! Failed to get request token.'

@app.route('/logout')
def logout():
  if is_logged_in():
    user = session['user']
    sce.record_user_action(user, 'logout', None)
    del session['user']
  return redirect(url_for('index'))

@app.route('/oauth_authorized')
def oauth_authorized():
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

    if not sce.is_eligible(user):
      return redirect(url_for('ineligible'))

    study_data = sce.get_user_study_data(user)
    if study_data is not None:
      session['user'].update(study_data)

    # create user if not exists
    sce.create_user_if_not_exists(user)

    sce.record_user_action(user, 'login_success', None)

    return redirect(url_for('debrief'))
  except tweepy.TweepError:
    # return 'Error! Failed to get access token.'
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))
