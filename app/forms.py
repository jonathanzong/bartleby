from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, TextField, RadioField, BooleanField, validators

class SurveyForm(FlaskForm):
  opt_out              = BooleanField('Do not include my information in your research')

class CompensationForm(FlaskForm):
  email_address        = TextField('Email address (Paypal account not required)',
                                    [validators.DataRequired(), validators.Email()])
