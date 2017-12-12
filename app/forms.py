from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, RadioField, validators

class SurveyForm(FlaskForm):
  click_recruitment    = RadioField('How likely would you be to click the link in the second tweet? ',
                                    [validators.DataRequired()],
                                    choices=[(x[0], x) for x in ['1 (definitely not)', '2 (probably not)', '3 (possibly)', '4 (probably)', '5 (definitely)']])
  would_delete         = RadioField('In the debriefing webpage, we gave you a chance to have your data deleted from the study. How likely would you be to click the button to delete your data?',
                                    [validators.DataRequired()],
                                    choices=[(x[0], x) for x in ['1 (definitely not)', '2 (probably not)', '3 (possibly)', '4 (probably)', '5 (definitely)']])
  society_benefit      = RadioField('How beneficial to society would it be to learn the answer to this research question?',
                                    [validators.DataRequired()],
                                    choices=[(x[0], x) for x in ['1 (harmful)', '2 (somewhat harmful)', '3 (neutral)', '4 (somewhat beneficial)', '5 (beneficial)']])
  personal_benefit     = RadioField('How much might this answer benefit you personally?',
                                    [validators.DataRequired()],
                                    choices=[(x[0], x) for x in ['1 (harmful)', '2 (somewhat harmful)', '3 (neutral)', '4 (somewhat beneficial)', '5 (beneficial)']])
  collection_surprised = RadioField('Suppose you learned that you were one of the participants in this study. How surprised are you that we are able to collect this information about your public Twitter behavior?',
                                    [validators.DataRequired()],
                                    choices=[(x, x) for x in ["I didn't know any of my Twitter information was public",
                                             'I knew some data collection was possible, but not this much',
                                             'I expected something like this was possible',
                                             'I expected that even more of my data could be collected']])
  glad_in_study        = RadioField('Which of the following best describes how you would feel about being included in the study?',
                                    [validators.DataRequired()],
                                    choices=[(x, x) for x in ['I would be glad I was in the study',
                                             'I would rather not have been in the study',
                                             'I would not care either way']])
  share_results        = RadioField('What best describes how you might share the results of this research online with others:',
                                    [validators.DataRequired()],
                                    choices=[(x, x) for x in ['I would link to the results and mention that I was a participant',
                                             'I would link to the results',
                                             'I would not want people in my social network to know that I was part of this study']])
  vote_study           = RadioField('If you could vote on whether this study should happen, how would you vote?',
                                    [validators.DataRequired()],
                                    choices=[(x, x) for x in ['This should happen',
                                             'I would want some things to change',
                                             'This study should not happen']])
  improve_debrief      = TextAreaField('If we could make the research debriefing webpage different, what would you change? (optional)')
