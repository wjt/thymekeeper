#!/usr/bin/env python
import os
import errno
import subprocess
from flask.ext.script import Manager

from thymekeeper import app, db, user_datastore

manager = Manager(app)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


@manager.command
def syncdb():
    """
    Create the database.
    """
    mkdir_p(app.instance_path)
    db.create_all()


@manager.command
def reset():
    """
    Drops and recreates the database, IRREVOCABLY and WITHOUT CONFIRMATION.
    """
    db.drop_all()
    syncdb()


@manager.command
def createsuperuser(email, password):
    """
    Create a (normal) user.

    The name is cargo-culted from Django so tab-completing manage.py works ;-)
    """
    syncdb()
    user_datastore.create_user(email=email, password=password)
    db.session.commit()


@manager.command
def gensecret():
    """Ensure <instance_path>/secret.py exists."""
    try:
        with app.open_instance_resource('secret.py', 'r'):
            app.logger.info("(already exists)")
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

        print("(ignore the warning above, I'm generating it now)")
        mkdir_p(app.instance_path)
        with app.open_instance_resource('secret.py', 'wb') as f:
            f.write('SECRET_KEY = {!r}\n'.format(os.urandom(32)))


@manager.command
def celery():
    """
    Run some Celery workers.
    """
    subprocess.check_call(('celery', 'worker', '-A', 'thymekeeper.celery'))


if __name__ == "__main__":
    manager.run()
