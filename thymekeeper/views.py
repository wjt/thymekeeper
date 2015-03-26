import requests
from six.moves import StringIO

from flask import render_template
from flask_wtf import Form
from wtforms import StringField, DateField
from wtforms.validators import DataRequired

from thymekeeper import app, login_required
from thymekeeper.ical import ICal, summarise_daily


class CalDAVForm(Form):
    ical_url = StringField('iCal URL', validators=[DataRequired()])
    start    = DateField  ('Between',  validators=[DataRequired()])
    end      = DateField  ('And',      validators=[DataRequired()])


@app.route('/', methods=('GET', 'POST'))
@login_required
def index():
    form = CalDAVForm()
    if form.validate_on_submit():
        url = form.ical_url.data

        app.logger.info('fetching %s', url)
        response = requests.get(url, timeout=5)

        app.logger.info('parsing and slicing %s', url)
        cal = ICal.from_fp(StringIO(response.text))
        vevents = cal[form.start.data:form.end.data]
        daily = summarise_daily(vevents)

        return render_template('index.html',
                               form=form,
                               cal_name=cal.name,
                               start=form.start.data,
                               end=form.end.data,
                               daily=daily)
    else:
        return render_template('index.html',
                               form=form)
