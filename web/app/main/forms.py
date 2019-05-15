from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, SelectField
from wtforms.validators import Required,Optional

class LoginForm(FlaskForm):
    """Accepts a TV Show title to plot ratings."""
    title = StringField('TV Show', validators=[Required()])
    style = SelectField('Style',choices = [('bar','bar'),('line','line')], validators = [Required()])
    submit = SubmitField('Plot Ratings')
