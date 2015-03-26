#!/usr/bin/env python
from flask.ext.script import Manager

from thymekeeper import app, db, user_datastore

manager = Manager(app)

@manager.command
def syncdb():
    """
    Create the database.
    """
    db.create_all()

@manager.command
def dropdb():
    """
    Drops the database, IRREVOCABLY and WITHOUT CONFIRMATION.
    """
    db.drop_all()

@manager.command
def createsuperuser(email, password):
    """
    Create a (normal) user.

    The name is cargo-culted from Django so tab-completing manage.py works ;-)
    """
    user_datastore.create_user(email=email, password=password)
    db.session.commit()

if __name__ == "__main__":
    manager.run()
