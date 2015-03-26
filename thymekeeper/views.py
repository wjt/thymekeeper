import requests
from six.moves import StringIO

from flask import render_template, redirect, url_for, request
from flask_wtf import Form
from wtforms import StringField, DateField
from wtforms.validators import DataRequired

from thymekeeper import app, login_required, current_user, db, Calendar
from thymekeeper.utils import isodate, isomonth
from thymekeeper.ical import ICal, summarise_daily

from dateutil.relativedelta import relativedelta


class AddCalendarForm(Form):
    ical_url = StringField('iCal URL', validators=[DataRequired()])


@app.route('/calendar/add', methods=('POST',))
@login_required
def add_calendar():
    form = AddCalendarForm()
    if form.validate_on_submit():
        # TODO: deduplicate
        cal = Calendar(url=form.ical_url.data, user=current_user)
        db.session.add(cal)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return render_template('index.html',
                               form=form,
                               calendars=current_user.calendars)


@app.route('/', methods=('GET', 'POST'))
@login_required
def index():
    form = AddCalendarForm()
    if form.validate_on_submit():
        cal = Calendar(url=form.ical_url.data, user=current_user)
        db.session.add(cal)
        db.session.commit()

    return render_template('index.html',
                           form=form,
                           calendars=current_user.calendars)


def liftNone(f, m):
    if m is None:
        return None

    return f(m)





@app.route('/calendar/<int:id>')
@login_required
def show_calendar(id):
    cal = Calendar.query.get_or_404(id)
    if cal.user != current_user:
        return 403

    def get(field, f):
        return liftNone(f, request.args.get(field, None))

    start = get('start', isodate)
    end   = get('end',   isodate)
    month = get('month', isomonth)

    if month:
        if (start or end):
            app.logger.warning('TODO: reject')

        assert month.day == 1
        # TODO: surely dateutil
        start = month
        end = month + relativedelta(months=+1, days=-1)

    app.logger.info('fetching %s', cal.url)
    response = requests.get(cal.url, timeout=5)

    app.logger.info('parsing and slicing %s', cal.url)
    ical = ICal.from_fp(StringIO(response.text))
    vevents = ical[start:end]
    daily = summarise_daily(vevents)

    return render_template('calendar.html',
                           ical=ical,
                           start=start,
                           end=end,
                           daily=daily)


class CalDAVForm(Form):
    ical_url = StringField('iCal URL', validators=[DataRequired()])
    start    = DateField  ('Between',  validators=[DataRequired()])
    end      = DateField  ('And',      validators=[DataRequired()])


@app.route('/olde', methods=('GET', 'POST'))
@login_required
def olde():
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
