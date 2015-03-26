import os

from flask import Flask
from flask.ext import assets
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

app = Flask(__name__)
app.config.from_pyfile('../settings.py')

#### Database
db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))


#### Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


#### Asserts
env = assets.Environment(app)

env.load_path = [
    os.path.join(os.path.dirname(__file__), 'sass'),
    os.path.join(os.path.dirname(__file__), 'coffee'),
    os.path.join(os.path.dirname(__file__), '../bower_components'),
]

env.register(
    'js_all',
    assets.Bundle(
        'jquery/dist/jquery.min.js',
        'bootstrap/dist/js/bootstrap.min.js',
        'bootstrap-datepicker/dist/js/bootstrap-datepicker.min.js',
        assets.Bundle(
            'all.coffee',
            filters=['coffeescript']
        ),
        output='js_all.js'
    )
)

env.register(
    'css_all',
    assets.Bundle(
        'bootstrap/dist/css/bootstrap.min.css',
        'bootstrap-datepicker/dist/css/bootstrap-datepicker3.min.css',
        assets.Bundle(
            'all.sass',
            filters=['sass']
        ),
        output='css_all.css'
    )
)


import thymekeeper.views
