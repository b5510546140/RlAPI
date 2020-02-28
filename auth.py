# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
import json

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    print("login post")
    app = current_app._get_current_object()
    print(request.json)
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()
    data = {
        'res': 'Login suceesful',
        'isUser': True
	}
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        # flash('Please check your login details and try again.')
        data = {
            'res': 'Please check your login details and try again.',
            'isUser': False
	    }

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)

    
    response = app.response_class(
    	response=json.dumps(data),
	mimetype='application/json',
    )
    response.status_code = 200
    return response

    # return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    app = current_app._get_current_object()
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        data = {
            'status_code': 200,
            'res': 'Email address already exists',
            'user': []
	    }
        response = app.response_class(
        response=json.dumps(data),
        mimetype='application/json',
        )
        response.status_code = 200
        return response

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    if new_user:
        data = {
            'status_code': 201,
            'res': 'Sign up sucess',
            'user': [{
                'name':new_user.name,
                'email':new_user.email
            }]
	    }
    response = app.response_class(
    response=json.dumps(data),
	mimetype='application/json',
    )
    response.status_code = 201
    return response

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    app = current_app._get_current_object()
    print("logout")
    logout_user()
    response = app.response_class(
    response=json.dumps({
            'status_code': 201,
            'res': 'Logout sucessful'
	    }),
	mimetype='application/json',
    )
    response.status_code = 201
    return response