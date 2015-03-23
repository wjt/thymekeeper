import os

from flask import Flask
from flask.ext import assets

app = Flask(__name__)
app.config.from_pyfile('../settings.py')

env = assets.Environment(app)


# Tell flask-assets where to look for our coffeescript and sass files.
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
