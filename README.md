# RlAPI project = project name should be RlApi
export FLASK_APP=project
export FLASK_DEBUG=1
flask run




// Create DB
from project import db, create_app
db.create_all(app=create_app()) # pass the create_app result so Flask-SQLAlchemy gets the configuration.
