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

DEFAULT_STUDY = 'academic'  # set default template for direct link to homepage here

sce = TwitterDebriefExperimentController(
    experiment_name='twitter_academic_debrief_experiment',
    default_study=DEFAULT_STUDY,
    db_session=db_session,
    required_keys=['name', 'randomizations', 'eligible_ids']
  )

def is_logged_in():
  return 'user' in session and sce.user_exists(session['user'])

@app.route('/')
def index():
  if is_logged_in():
    return redirect(url_for('begin'))
  amount_dollars = int(request.args.get('c')) if request.args.get('c') else 0

  sce.record_user_action(None, 'page_view', {'page': 'index', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  study_template = request.args.get('t') if request.args.get('t') else DEFAULT_STUDY
  extra_data = json.loads(request.args.get('x')) if request.args.get('x') else None
  return render_template(study_template + '/01-index.html', amount_dollars=amount_dollars, extra_data=extra_data)

@app.route('/begin', methods=('GET', 'POST'))
def begin():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  sce.record_user_action(user, 'page_view', {'page': 'begin', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  # handle form submission
  form = TweetRemovedForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    if study_template is not None and study_template is 'dmca':
      # assign a randomization based on whether tweet_removed
      sce.assign_randomization(user, results_dict=results_dict)
      session['user']['conditions'] = sce.get_user_conditions(user)

    sce.record_user_action(user, 'form_submit', {'page': 'begin'})

    return redirect(url_for('tweet_intervention'))
  study_template = sce.get_user_study_template(user)
  if study_template is not None and study_template is not 'dmca':
    # only 'dmca' currently uses a stratified sample, so nothing else needs the /begin page
    return redirect(url_for('tweet_intervention'))
  return render_template(study_template + '/02-begin.html', user=user, form=form)

@app.route('/tweet-intervention')
def tweet_intervention():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  if study_template is not None and study_template is not 'dmca':
    # isn't dmca study so didn't assign in previous page, assign now
    sce.assign_randomization(user)
    session['user']['conditions'] = sce.get_user_conditions(user)

  conditions = user['conditions'] if 'conditions' in user else sce.get_user_conditions(user)

  sce.record_user_action(user, 'page_view', {'page': 'tweet-intervention', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  study_template = sce.get_user_study_template(user)
  extra_data = sce.get_user_extra_data(user)
  return render_template(study_template + '/03-tweet-intervention.html', user=user, in_control_group=conditions['in_control_group'], extra_data=extra_data)

@app.route('/tweet-debrief', methods=('GET', 'POST'))
def tweet_debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  sce.record_user_action(user, 'page_view', {'page': 'tweet-debrief', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  # handle form submission
  form = WouldClickTweetForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    sce.record_user_action(user, 'form_submit', {'page': 'tweet-debrief'})

    return redirect(url_for('debrief'))

  study_template = sce.get_user_study_template(user)
  return render_template(study_template + '/04-tweet-debrief.html', user=user, form=form)

@app.route('/debrief', methods=('GET', 'POST'))
def debrief():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  if sce.has_completed_study(user):
    return redirect(url_for('complete'))

  conditions = user['conditions'] if 'conditions' in user else sce.get_user_conditions(user)

  sce.record_user_action(user, 'page_view', {'page': 'debrief', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  # handle form submission
  form = SurveyForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']
    results_dict['twitter_user_id'] = user['id']

    sce.insert_or_update_survey_result(user, results_dict)

    sce.record_user_action(user, 'form_submit', {'page': 'debrief'})

    return redirect(url_for('complete'))
  study_template = sce.get_user_study_template(user)
  return render_template(study_template + '/05-debrief.html', user=user, form=form,
                          show_table=conditions['show_table'],
                          show_visualization=conditions['show_visualization'])

@app.route('/complete', methods=('GET', 'POST'))
def complete():
  if not is_logged_in():
    return redirect(url_for('index'))
  user = session['user']
  amount_dollars = sce.get_user_compensation_amount(user)

  if not sce.is_eligible(user):
    return redirect(url_for('ineligible'))

  if not sce.has_completed_study(user):
    did_complete = sce.mark_user_completed(user)
    if not did_complete:
      # how did they even get here
      return redirect(url_for('begin'))

  sce.record_user_action(user, 'page_view', {'page': 'complete', 'user_agent': request.user_agent.string, 'qs': request.query_string, 'referrer': request.referrer})

  has_sent_compensation = sce.has_sent_payout(user)

  error_msg = None
  if 'error_msg' in session:
    error_msg = session['error_msg']
    del session['error_msg']

  # handle form submission
  form = CompensationForm()
  if form.validate_on_submit():
    results_dict = request.form.to_dict()
    del results_dict['csrf_token']

    if not has_sent_compensation and amount_dollars > 0:
      session['error_msg'] = sce.send_paypal_payout(user, results_dict['email_address'], amount_dollars)

    sce.record_user_action(user, 'form_submit', {'page': 'complete'})

    return redirect(url_for('complete'))
  study_template = sce.get_user_study_template(user)
  return render_template(study_template + '/06-complete.html', user=user, form=form, has_sent_compensation=has_sent_compensation, error_msg=error_msg, amount_dollars=amount_dollars)

@app.route('/ineligible')
def ineligible():
  if is_logged_in():
    return redirect(url_for('begin'))
  user = session['user']

  if sce.is_eligible(user):
    return redirect(url_for('begin'))

  sce.record_user_action(user, 'page_view', {'page': 'ineligible', 'user_agent': request.user_agent.string, 'qs': request.query_string})

  return render_template('ineligible.html')

@app.route('/login')
def login():
  if is_logged_in():
    return redirect(url_for('begin'))

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

    # create user if not exists
    sce.create_user_if_not_exists(user)

    sce.record_user_action(user, 'login_success', None)

    return redirect(url_for('begin'))
  except tweepy.TweepError:
    # return 'Error! Failed to get access token.'
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))
