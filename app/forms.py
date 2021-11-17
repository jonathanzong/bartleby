from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, TextField, RadioField, BooleanField, validators

class SurveyForm(FlaskForm):
  opt_out              = BooleanField('Do not include my information in your research', [validators.Optional()])
  collection_surprised_twitter = RadioField('How surprised are you that we are able to collect this information about your public Twitter behavior?',
                                   [validators.Optional()],
                                    choices=[(x, x) for x in ["I didn't know any of my Twitter information was public",
                                             'I knew some data collection was possible, but not this much',
                                             'I expected something like this was possible',
                                             'I expected that even more of my data could be collected']])
  collection_surprised_reddit = RadioField('How surprised are you that we are able to collect this information about your public Reddit behavior?',
                                   [validators.Optional()],
                                    choices=[(x, x) for x in ["I didn't know any of my Reddit information was public",
                                             'I knew some data collection was possible, but not this much',
                                             'I expected something like this was possible',
                                             'I expected that even more of my data could be collected']])
  glad_in_study        = RadioField('Which of the following best describes how you feel about being included in the study?',
                                   [validators.Optional()],
                                    choices=[(x, x) for x in ['I would be glad I was in the study',
                                             'I would rather not have been in the study',
                                             'I would not care either way']])
  share_results        = RadioField('What best describes how you might share the results of this research online with others?',
                                   [validators.Optional()],
                                    choices=[(x, x) for x in ['I would link to the results and mention that I was a participant',
                                             'I would link to the results',
                                             'I would not want people in my social network to know that I was part of this study']])
  vote_study           = RadioField('If you could vote on whether this study should happen, how would you vote?',
                                   [validators.Optional()],
                                    choices=[(x, x) for x in ['This should happen',
                                             'I would want some things to change',
                                             'This study should not happen']])
  improve_debrief      = TextAreaField('If we could make the research debriefing webpage different, what would you change?', [validators.Optional()])

# class CompensationForm(FlaskForm):
#   email_address        = TextField('Email address (Paypal account not required)',
#                                     [validators.DataRequired(), validators.Email()])
