# main.py

from flask import Blueprint, render_template, current_app, request, make_response
from flask_login import login_required, current_user
import json
import pandas as pd
import os
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
    if isParam:
        response = make_response(json.dumps({
                'status_code': 422,
                'res': {"symbol":notFoundParam}
        }),422)
    else:
        currencySymobol = req['symbol']
        startDate = req['startDate']
        endDate = req['endDate']
        data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
        del data['Adj Close']
        del data['Volume']
        data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
        response = make_response(data.to_json(orient = "records"),200)

    response.mimetype = 'application/json'
    return response

@main.route('/rl', methods=['POST'])
@login_required
def createModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
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
        if 'gamma'not in req:
            gamma = None
        else:
            gamma = req['gamma']
        md = Model.query.filter_by(user_id=userId,).\
        filter_by(model_name = modelName).first()
        if md:
            notFoundParam = 'modelName already exist'
        else :
            data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            if len(data) < trainDay + testDay:
                notFoundParam = 'train and testDay more than data ' + str(len(data))
            else:
                newLog = Log(user_id = userId, created_at = now, log_text = "")
                db.session.add(newLog)
                db.session.commit()
                fileName = Rl.trainModel(data, currencySymobol, episode_count= episodeCount, start_balance=startBalance, training=trainDay, test=testDay, model_name=modelName, log=newLog)
                response = app.response_class(
                    response=json.dumps({
                        'status_code': 201,
                        'res': {"symbol":currencySymobol}
                    }),
                    mimetype='application/json',
                )
                response.status_code = 201
                isParam = False
                new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, log_id = newLog.id, model_path = fileName,  start_balance=startBalance, gamma = gamma)
                db.session.add(new_Rlmodel)
                db.session.commit()
    if isParam:
        response = app.response_class(
            response=json.dumps({
                'status_code': 422,
                'res': {"symbol":notFoundParam}
            }),
            mimetype='application/json',
        )
        response.status_code = 422


    return response
    
    # return render_template('profile.html', name=current_user.name)

@main.route('/log', methods=['GET'])
@login_required
def getLog():
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    print(userId)
    log = Log.query.filter_by(user_id=userId).\
        order_by(db.desc(Log.created_at)).first()
    if log is not None:
        response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': {
                    "userId":log.user_id,
                    "data":log.log_text}
            }),
            mimetype='application/json',
        )
        response.status_code = 200
    else:
        response = app.response_class(
            response=json.dumps({
                'status_code': 404,
                'res': {
                    "error":'Not Found'}
            }),
            mimetype='application/json',
        )
        response.status_code = 404
    return response


@main.route('/models', methods=['GET'])
@login_required
def getModels():
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    models = Model.query.filter_by(user_id=userId).\
        order_by(db.desc(Model.created_at)).all()
    print(len(models))
    df = pd.DataFrame(columns = ["id","user_id","created_at","updated_at","num_train_date","num_test_date","gamma","epsilon","epsilon_min","epsilon_decay","episode_count","model_name","currency_symobol","start_balance","currency_amount","avg_currency_rate","log_id","model_path"])
    if len(models) > 0:
        for model in models:
            df = df.append({'id': model.id,'user_id' : model.user_id,'created_at' : model.created_at,'updated_at' : model.updated_at,'num_train_date' : model.num_train_date,'num_test_date' : model.num_test_date,'gamma' : model.gamma,'epsilon' : model.epsilon,'epsilon_min' : model.epsilon_min,'epsilon_decay' : model.epsilon_decay,'episode_count' : model.episode_count,'model_name' : model.model_name,'currency_symobol' : model.currency_symobol,'start_balance' : model.start_balance,'currency_amount' : model.currency_amount,'avg_currency_rate' : model.avg_currency_rate,'log_id' : model.log_id,'model_path' : model.model_path} , ignore_index=True)

        response = make_response(df.to_json(orient = "records"),200)
        response.mimetype = 'application/json'
    else:
        response = make_response(df.to_json(orient = "records"),404)
        response.mimetype = 'application/json'
    return  response

@main.route('/updaterl', methods=['POST'])
@login_required
def updateModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
    notFoundParam = ''

    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
    elif 'startDate' not in req:
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
        model = Model.query.get(req['modelId'])
        if 'gamma'not in req:
            gamma = None
        else:
            gamma = req['gamma']
        isParam = False
        isUpdate = False
        isNotError = True
        if str(model.user_id) == userId:
            Log.query.filter(Log.id == model.log_id).delete()
            if str(model.model_name) == modelName:
                isUpdate = True
            else :
                md = Model.query.filter_by(user_id=userId,).\
                filter_by(model_name = modelName).first()
                if md:
                    isParam = True
                    notFoundParam = 'modelName already exist'
                    isNotError = False

            if isNotError:
                data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
                if len(data) < trainDay + testDay:
                    notFoundParam = 'train and testDay more than data ' + str(len(data))
                else:
                    newLog = Log(user_id = userId, created_at = now, log_text = "")
                    db.session.add(newLog)
                    db.session.commit()
                    fileName = Rl.trainModel(data, currencySymobol, episode_count= episodeCount, start_balance=startBalance, training=trainDay, test=testDay, model_name=modelName, log=newLog, isUpdate = isUpdate, OldmodelPath= model.model_path)
                    print("File Name")
                    print(fileName)
                    response = app.response_class(
                        response=json.dumps({
                            'status_code': 201,
                            'res': {"symbol":currencySymobol}
                        }),
                        mimetype='application/json',
                    )
                    response.status_code = 201
                    if isUpdate:
                        model.updated_at = now
                        model.num_train_date = trainDay
                        model.num_test_date = testDay
                        model.episode_count = episodeCount 
                        model.currency_symobol = currencySymobol
                        model.log_id = newLog.id # Todo delete old log
                        model.model_path = fileName
                        model.start_balance=startBalance
                    else:
                        new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, log_id = newLog.id, model_path = fileName, start_balance=startBalance)
                        db.session.add(new_Rlmodel)
                    db.session.commit()
        else :
            response = app.response_class(
            response=json.dumps({
                'status_code': 401,
                'res': {"error":"Unauthorize model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 401

    if isParam:
        response = app.response_class(
            response=json.dumps({
                'status_code': 422,
                'res': {"symbol":notFoundParam}
            }),
            mimetype='application/json',
        )
        response.status_code = 422


    return response


@main.route('/delmodel', methods=['POST'])
@login_required
def delModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
    notFoundParam = ''

    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
    else:
        modelId = req['modelId']
        model = Model.query.filter_by(id = modelId).first()
        if str(model.user_id) == str(userId):
            Model.query.filter_by(user_id=userId).\
        filter_by(id = modelId).delete()
            Log.query.filter_by(id=model.log_id).delete()
            db.session.commit()
            response = app.response_class(
                response=json.dumps({
                    'status_code': 200,
                            'res': "Delete Succesful"
                        }),
                        mimetype='application/json',
                    )
            response.status_code = 200       
        else:
            response = app.response_class(
            response=json.dumps({
                'status_code': 401,
                'res': {"error":"Unauthorize model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 401


    return  response



@main.route('/testmodel', methods=['POST'])
@login_required
def testModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
    notFoundParam = ''
    if 'startDate' not in req:
        notFoundParam = 'startDate not found'
    elif 'endDate'not in req:
        notFoundParam = 'endDate not found'
    elif 'symbol'not in req:
        notFoundParam = 'symbol not found'
    elif 'currencyAmount'not in req:
        notFoundParam = 'currencyAmount not found'
    elif 'avgCurrencyRate'not in req:
        notFoundParam = 'avgCurrencyRate not found'
    elif 'startBalance'not in req:
        notFoundParam = 'startBalance not found'
    elif 'testDay'not in req:
        notFoundParam = 'testDay not found'
    elif 'modelId'not in req:
        notFoundParam = 'modelId not found'
    else:
        modelId = req['modelId']
        model = Model.query.filter_by(id = modelId).first()
        if str(model.user_id) == str(userId):
            currencySymobol = req['symbol']
            startDate = req['startDate']
            endDate = req['endDate']
            startBalance = req['startBalance']
            currencyAmount = req['currencyAmount']
            avgCurrencyRate = req['avgCurrencyRate']
            testDay = req['testDay']
            # testRl(data, currencySymobol, start_balance, training, test, filename, log, priceLook = 'Close'):
            data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            result = Rl.testRl(data, currencySymobol, startBalance, training = 0, test = testDay, filename = model.model_path, log= None,currencyAmount = currencyAmount,avgCurrencyRate = avgCurrencyRate)
            response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': result
                }),
            mimetype='application/json'
            )
            response.status_code = 200     
        else:
            response = app.response_class(
            response=json.dumps({
                'status_code': 401,
                'res': {"error":"Unauthorize model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 401

        return response
    response = app.response_class(
        response=json.dumps({
            'status_code': 422,
            'res': {"symbol":notFoundParam}
        }),
        mimetype='application/json',
    )
    response.status_code = 422
    return response


@main.route('/predict', methods=['POST'])
@login_required
def predictModel():
    req = request.get_json()
    app = current_app._get_current_object()
    isParam = True
    userId = current_user.get_id()
    now = datetime.datetime.now()
    notFoundParam = ''
    if 'startDate' not in req:
        notFoundParam = 'startDate not found'
    elif 'endDate'not in req:
        notFoundParam = 'endDate not found'
    elif 'symbol'not in req:
        notFoundParam = 'symbol not found'
    elif 'currencyAmount'not in req:
        notFoundParam = 'currencyAmount not found'
    elif 'avgCurrencyRate'not in req:
        notFoundParam = 'avgCurrencyRate not found'
    elif 'startBalance'not in req:
        notFoundParam = 'startBalance not found'
    elif 'modelId'not in req:
        notFoundParam = 'modelId not found'
    else:
        modelId = req['modelId']
        model = Model.query.filter_by(id = modelId).first()
        if str(model.user_id) == str(userId):
            currencySymobol = req['symbol']
            startDate = req['startDate']
            endDate = req['endDate']
            startBalance = req['startBalance']
            currencyAmount = req['currencyAmount']
            avgCurrencyRate = req['avgCurrencyRate']
            #   def getPredict(data, currencySymobol, start_balance, filename, currency_amount, avg_currency_rate, priceLook = 'Close'):
  
            data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            result = Rl.getPredict(data, currencySymobol, startBalance, filename = model.model_path,currency_amount = currencyAmount,avg_currency_rate = avgCurrencyRate)
            response = app.response_class(
            response=json.dumps({
                'status_code': 200,
                'res': result
                }),
            mimetype='application/json'
            )
            response.status_code = 200     
        else:
            response = app.response_class(
            response=json.dumps({
                'status_code': 401,
                'res': {"error":"Unauthorize model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 401

        return response
    response = app.response_class(
        response=json.dumps({
            'status_code': 422,
            'res': {"symbol":notFoundParam}
        }),
        mimetype='application/json',
    )
    response.status_code = 422
    return response