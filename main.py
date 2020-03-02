# main.py

from flask import Blueprint, render_template, current_app, request
from flask_login import login_required, current_user
import json
from .rlMain import Rl
from .models import Log
from .models import Model
from .models import User
from . import db

import yfinance as yf
import datetime



main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@main.route('/data', methods=['POST'])
@login_required
def getData():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    if 'startDate' not in req:
        notFoundParam = 'startDate not found'
        isParam = True
    elif 'endDate'not in req:
        notFoundParam = 'endDate not found'
        isParam = True
    elif 'symbol'not in req:
        notFoundParam = 'symbol not found'
        isParam = True

    currencySymobol = req['symbol']
    startDate = req['startDate']
    endDate = req['endDate']
    data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
    del data['Adj Close']
    del data['Volume']
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    if isParam:
        response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': {"symbol":notFoundParam}
            }),
            mimetype='application/json',
        )
        response.status_code = 200
    else:
        response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': {"symbol":currencySymobol,
                    "data":data.to_json(orient='records')}
            }),
            mimetype='application/json',
        )
        response.status_code = 200
    
    return response

@main.route('/rl', methods=['POST'])
@login_required
def createModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
    print(userId)
    notFoundParam = ''
    if 'startDate' not in req:
        notFoundParam = 'startDate not found'
    elif 'endDate'not in req:
        notFoundParam = 'endDate not found'
    elif 'symbol'not in req:
        notFoundParam = 'symbol not found'
    elif 'modelName'not in req:
        notFoundParam = 'modelName not found'
    elif 'startBalance'not in req:
        notFoundParam = 'startBalance not found'
    elif 'episodeCount'not in req:
        notFoundParam = 'episodeCount not found'
    elif 'trainingDay'not in req:
        notFoundParam = 'trainingDay not found'
    elif 'testDay'not in req:
        notFoundParam = 'testDay not found'
    else:
        currencySymobol = req['symbol']
        startDate = req['startDate']
        endDate = req['endDate']
        modelName = req['modelName']
        startBalance = req['startBalance']
        episodeCount = req['episodeCount']
        trainDay = req['trainingDay']
        testDay = req['testDay']
        data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
        if len(data) < trainDay + testDay:
            notFoundParam = 'train and testDay more than data ' + str(len(data))
        else:
            newLog = Log(user_id = userId, created_at = now, log_text = "")
            db.session.add(newLog)
            db.session.commit()
            res = Rl.trainModel(data, currencySymobol, episode_count= episodeCount, start_balance=startBalance, training=trainDay, test=testDay, model_name=modelName, log=newLog)
            response = app.response_class(
                response=json.dumps({
                    'status_code': 201,
                    'res': {"symbol":currencySymobol}
                }),
                mimetype='application/json',
            )
            response.status_code = 201
            isParam = False
            new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, log_id = newLog.id)
            db.session.add(new_Rlmodel)
            db.session.commit()
    if isParam:
        response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': {"symbol":notFoundParam}
            }),
            mimetype='application/json',
        )
        response.status_code = 200


    return response
    
    # return render_template('profile.html', name=current_user.name)

@main.route('/log', methods=['POST'])
@login_required
def getLog():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    print(userId)
    log = Log.query.filter_by(user_id=userId).\
        order_by(db.desc(Log.created_at)).first()
    print(log.log_text)

    # currencySymobol = req['symbol']
    # startDate = req['startDate']
    # endDate = req['endDate']
    # data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
    # del data['Adj Close']
    # del data['Volume']
    # data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    # if isParam:
    #     response = app.response_class(
    #         response=json.dumps({
    #             'status_code': 200,
    #             'res': {"symbol":notFoundParam}
    #         }),
    #         mimetype='application/json',
    #     )
    #     response.status_code = 200
    # else:
    response = app.response_class(
        response=json.dumps({
            'status_code': 200,
            'res': {
                "data":log.log_text}
        }),
        mimetype='application/json',
    )
    response.status_code = 200
    
    return response