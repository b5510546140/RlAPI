# main.py

from flask import Blueprint, render_template, current_app, request
from flask_login import login_required, current_user
import json
from .rlMain import Rl

import yfinance as yf


main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


@main.route('/rl', methods=['POST'])
@login_required
def createModel():
    req = request.get_json()
    app = current_app._get_current_object()
    print(type(req))
    if 'symbol'in req:
        
        currencySymobol = req['symbol']
        data = yf.download(currencySymobol, start="2019-01-01", end="2019-06-30").reset_index()
        res = Rl.trainModel(data, currencySymobol, 1, 1000000, 90, 30)
        response = app.response_class(
            response=json.dumps({
                'status_code': 201,
                'res': {"symbol":currencySymobol}
            }),
            mimetype='application/json',
        )
        response.status_code = 201
    else:
        response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': {"symbol":"Symbol not found"}
            }),
            mimetype='application/json',
        )
        response.status_code = 200
    # print(req['condition'][0])


    return response
    
    # return render_template('profile.html', name=current_user.name)