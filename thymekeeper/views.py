from thymekeeper import app
from flask import render_template
from flask_wtf import Form
from wtforms import StringField, DateField
from wtforms.validators import DataRequired

from .ical import scrape_ical


class CalDAVForm(Form):
    ical_url = StringField('iCal URL', validators=[DataRequired()])
    start    = DateField  ('Between',  validators=[DataRequired()])
    end      = DateField  ('And',      validators=[DataRequired()])


@app.route('/', methods=('GET', 'POST'))
def index():
    form = CalDAVForm()
    if form.validate_on_submit():
        scrape_ical(form.ical_url.data, form.start.data, form.end.data)
    return render_template('index.html', form=form)
