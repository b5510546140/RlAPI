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
from .models import Policy
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
        try:
            data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
        except:
            print("No data found, symbol may be delisted")
            data = []
        if len(data) == 0:
            notFoundParam = "No data found, symbol may be delisted"
            response = app.response_class(
                response=json.dumps({
                    'status_code': 422,
                    'res': {"symbol":notFoundParam}
                }),
                mimetype='application/json',
            )
            response.status_code = 422
            return response
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
    elif req['startBalance'] <= 0:
        notFoundParam = 'startBalance cannot less than or equal 0'
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
            gamma = 0.95
        else:
            gamma = req['gamma']
        if 'epsilon'not in req:
            epsilon = 1.0
        else:
            epsilon = req['epsilon']
        if 'epsilon_min'not in req:
            epsilon_min = 0.01
        else:
            epsilon_min = req['epsilon_min']
        if 'epsilon_decay'not in req:
            epsilon_decay = 0.995
        else:
            epsilon_decay = req['epsilon_decay']
        if 'currencyAmount' not in req or req['currencyAmount'] is None:
            currencyAmount = -1
        else:
            currencyAmount = req['currencyAmount']
        if 'avgCurrencyRate' not in req or req['avgCurrencyRate'] is None :
            avgCurrencyRate = -1
        else:
            avgCurrencyRate = req['avgCurrencyRate']  
        if 'conditions' not in req:
            conditions = []
        else:
            conditions = req['conditions']  
        if 'openclose' not in req:
            openclose = "Close"
        else:
            openclose = req['openclose']
        if 'buyLotSize' not in req:
            buyLotSize = -1
        else:
            buyLotSize = req['buyLotSize']
        if 'saleLotSize' not in req:
            saleLotSize = -1
        else:
            saleLotSize = req['saleLotSize']
        md = Model.query.filter_by(user_id=userId,).\
        filter_by(model_name = modelName).first()
        if md:
            notFoundParam = 'modelName already exist'
        else :
            try:
                data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            except:
                print("No data found, symbol may be delisted")
                data = []
            if len(data) < trainDay + testDay:
                if len(data) > 0:
                    notFoundParam = 'Data Available' + str(len(data))
                else: notFoundParam = "No data found, symbol may be delisted"
            else:
                newLog = Log(user_id = userId, created_at = now, log_text = "", train_text = "", test_text = "")
                db.session.add(newLog)
                db.session.commit()
                fileName = Rl.trainModel(data, currencySymobol, episode_count= episodeCount, start_balance=startBalance, training=trainDay, test=testDay, model_name=modelName, log=newLog,currencyAmount = currencyAmount,avgCurrencyRate = avgCurrencyRate,gamma = gamma, epsilon= epsilon,epsilon_min=epsilon_min, epsilon_decay=epsilon_decay, conditions=conditions, openclose=openclose, buyLotSize = buyLotSize, saleLotSize = saleLotSize)
                isParam = False
                newstartDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
                newendDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
                if currencyAmount == -1: currencyAmount = None
                if avgCurrencyRate == -1: avgCurrencyRate = None
                new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, log_id = newLog.id, model_path = fileName,  start_balance=startBalance, currency_amount = currencyAmount,avg_currency_rate = avgCurrencyRate, gamma = gamma, epsilon= epsilon, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay, start_date= newstartDate,end_date = newendDate, have_model = True, buy_lot_size = buyLotSize, sale_lot_size = saleLotSize)
                db.session.add(new_Rlmodel)
                db.session.commit()
                md = Model.query.filter_by(user_id=userId,).\
                filter_by(model_name = modelName).first()
                response = app.response_class(
                    response=json.dumps({
                        'status_code': 201,
                        'res': {"model_id":md.id}
                    }),
                    mimetype='application/json',
                )
                response.status_code = 201
                
                for condition in conditions:
                    new_condition = Policy(model_id= md.id,created_at = now, action = condition["action"], con = condition["con"], sym = condition["sym"], num = condition["num"])
                    db.session.add(new_condition)
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
                    "data":log.log_text,
                    "train":log.train_text}
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
    df = pd.DataFrame(columns = ["id","user_id","created_at","updated_at","num_train_date","num_test_date","gamma","epsilon","epsilon_min","epsilon_decay","episode_count","model_name","currency_symobol","start_balance","currency_amount","avg_currency_rate","log_id","model_path","have_model"])
    if len(models) > 0:
        for model in models:
            df = df.append({'id': model.id,'user_id' : model.user_id,'created_at' : model.created_at,'updated_at' : model.updated_at,'num_train_date' : model.num_train_date,'num_test_date' : model.num_test_date,'gamma' : model.gamma,'epsilon' : model.epsilon,'epsilon_min' : model.epsilon_min,'epsilon_decay' : model.epsilon_decay,'episode_count' : model.episode_count,'model_name' : model.model_name,'currency_symobol' : model.currency_symobol,'start_balance' : model.start_balance,'currency_amount' : model.currency_amount,'avg_currency_rate' : model.avg_currency_rate,'log_id' : model.log_id,'model_path' : model.model_path, 'have_model':model.have_model} , ignore_index=True)

        response = make_response(df.to_json(orient = "records"),200)
        response.mimetype = 'application/json'
    else:
        response = make_response(df.to_json(orient = "records"),404)
        response.mimetype = 'application/json'
    return  response

@main.route('/policy', methods=['POST'])
@login_required
def getPolicy():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
        response = app.response_class(
            response=json.dumps({
                'status_code': 422,
                'res': {"symbol":notFoundParam}
            }),
            mimetype='application/json',
        )
        response.status_code = 422
    else:
        policys = Policy.query.filter_by(model_id=req['modelId']).all()
        df = pd.DataFrame(columns = ["id","model_id","action","con","sym","num"])
        if len(policys) > 0:
            for policy in policys:
                df = df.append({'id': policy.id,'model_id' : policy.model_id,'action':policy.action,'con':policy.con,'sym':policy.sym,'num':policy.num} , ignore_index=True)
            response = make_response(df.to_json(orient = "records"),200)
            response.mimetype = 'application/json'
        else:
            response = make_response(df.to_json(orient = "records"),404)
            response.mimetype = 'application/json'
    return  response

@main.route('/model', methods=['POST'])
@login_required
def getModelById():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
        isParam = True
    else:
        model = Model.query.get(req['modelId'])
        if model.currency_amount == -1: model.currency_amount = None
        if model.avg_currency_rate == -1: model.avg_currency_rate = None

        if str(model.user_id) == userId:
                    response = app.response_class(
                        response=json.dumps({
                            'status_code': 201,
                            'res': {'id': model.id,'user_id' : model.user_id,'num_train_date' : model.num_train_date,'num_test_date' : model.num_test_date,'gamma' : model.gamma,'epsilon' : model.epsilon,'epsilon_min' : model.epsilon_min,'epsilon_decay' : model.epsilon_decay,'episode_count' : model.episode_count,'model_name' : model.model_name,'currency_symobol' : model.currency_symobol,'start_balance' : model.start_balance,'currency_amount' : model.currency_amount,'avg_currency_rate' : model.avg_currency_rate,'log_id' : model.log_id,'model_path' : model.model_path, 'start_date': model.start_date.strftime('%Y-%m-%d'), 'end_date':model.end_date.strftime('%Y-%m-%d')}
                        }),
                        mimetype='application/json',
                    )
                    response.status_code = 201
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
            gamma = 0.95
        else:
            gamma = req['gamma']
        if 'epsilon'not in req:
            epsilon = 1.0
        else:
            epsilon = req['epsilon']
        if 'epsilon_min'not in req:
            epsilon_min = 0.01
        else:
            epsilon_min = req['epsilon_min']
        if 'epsilon_decay'not in req:
            epsilon_decay = 0.995
        else:
            epsilon_decay = req['epsilon_decay']
        if 'currencyAmount' not in req or req['currencyAmount'] is None:
            currencyAmount = -1
        else:
            currencyAmount = req['currencyAmount']
        if 'avgCurrencyRate' not in req or req['avgCurrencyRate'] is None :
            avgCurrencyRate = -1
        else:
            avgCurrencyRate = req['avgCurrencyRate']  
        if 'conditions' not in req:
            conditions = []
        else:
            conditions = req['conditions']
        if 'openclose' not in req:
            openclose = "Close"
        else:
            openclose = req['openclose']
        isParam = False
        isUpdate = False
        isNotError = True
        if model is None:
            response = app.response_class(
            response=json.dumps({
                'status_code': 404,
                'res': {"error":"Not found Model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 404
            return response
        if str(model.user_id) == userId:
            if str(model.model_name) == modelName:
                Log.query.filter(Log.id == model.log_id).delete()
                isUpdate = True
            else :
                md = Model.query.filter_by(user_id=userId,).\
                filter_by(model_name = modelName).first()
                if md:
                    isParam = True
                    notFoundParam = 'modelName already exist'
                    isNotError = False

            if isNotError:
                try:
                    data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
                except:
                    print("No data found, symbol may be delisted")
                    data = []
                if len(data) < trainDay + testDay:
                    notFoundParam = 'Data Available' + str(len(data))
                else: notFoundParam = "No data found, symbol may be delisted"
                data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
                
                if len(data) < trainDay + testDay:
                    notFoundParam = 'train and testDay more than data ' + str(len(data))
                else:
                    newLog = Log(user_id = userId, created_at = now, log_text = "", train_text = "", test_text = "")
                    db.session.add(newLog)
                    db.session.commit()
                    fileName = Rl.trainModel(data, currencySymobol, episode_count= episodeCount, start_balance=startBalance, training=trainDay, test=testDay, model_name=modelName, log=newLog, isUpdate = isUpdate, OldmodelPath= model.model_path,currencyAmount = currencyAmount,avgCurrencyRate = avgCurrencyRate,gamma = gamma, epsilon= epsilon,epsilon_min=epsilon_min, epsilon_decay=epsilon_decay, conditions=conditions, openclose= openclose)
                    newstartDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
                    newendDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
                    if currencyAmount == -1: currencyAmount = None
                    if avgCurrencyRate == -1: avgCurrencyRate = None
                    if isUpdate:
                        model.updated_at = now
                        model.num_train_date = trainDay
                        model.num_test_date = testDay
                        model.episode_count = episodeCount 
                        model.currency_symobol = currencySymobol
                        model.log_id = newLog.id # Todo delete old log
                        model.model_path = fileName
                        model.start_balance=startBalance
                        model.currency_amount = currencyAmount
                        model.avg_currency_rate = avgCurrencyRate
                        model.gamma = gamma
                        model.epsilon = epsilon
                        model.epsilon_min = epsilon_min
                        model.epsilon_decay = epsilon_decay
                        model.start_date = startDate
                        model.end_date = endDate
                        model.have_model = True
                        model.start_date = newstartDate
                        model.end_date = newendDate

                        Policy.query.filter(Policy.model_id == model.id).delete()
                        for condition in conditions:
                            new_condition = Policy(model_id= model.id,created_at = now, action = condition["action"], con = condition["con"], sym = condition["sym"], num = condition["num"])
                            db.session.add(new_condition)
                        db.session.commit()
                        response = app.response_class(
                            response=json.dumps({
                                'status_code': 201,
                                'res': {"model_id":model.id}
                            }),
                            mimetype='application/json',
                        )
                        response.status_code = 201                        
                    else:
                        new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, log_id = newLog.id, model_path = fileName,  start_balance=startBalance, currency_amount = currencyAmount,avg_currency_rate = avgCurrencyRate,gamma = gamma, epsilon= epsilon, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay,start_date= newstartDate,end_date = newendDate, have_model = True)
                        db.session.add(new_Rlmodel)
                        db.session.commit()
                        md = Model.query.filter_by(user_id=userId,).\
                        filter_by(model_name = modelName).first()
                        for condition in conditions:
                            new_condition = Policy(model_id= md.id,created_at = now, action = condition["action"], con = condition["con"], sym = condition["sym"], num = condition["num"])
                            db.session.add(new_condition)
                        db.session.commit()
                        response = app.response_class(
                            response=json.dumps({
                                'status_code': 201,
                                'res': {"model_id":md.id}
                            }),
                            mimetype='application/json',
                        )
                        response.status_code = 201              
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
        print(modelId)
        print(userId)
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
            if 'currencyAmount' not in req or req['currencyAmount'] is None:
                currencyAmount = -1
            else:
                currencyAmount = req['currencyAmount']
            if 'avgCurrencyRate' not in req or req['avgCurrencyRate'] is None :
                avgCurrencyRate = -1
            else:
                avgCurrencyRate = req['avgCurrencyRate']  
            if 'openclose' not in req:
                openclose = "Close"
            else:
                openclose = req['openclose']
            testDay = req['testDay']
            # testRl(data, currencySymobol, start_balance, training, test, filename, log, priceLook = 'Close'):
            data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            print(currencyAmount)
            print(avgCurrencyRate)
            result = Rl.testRl(data, currencySymobol, startBalance, training = 0, test = testDay, filename = model.model_path, log= None,currencyAmount = currencyAmount,avgCurrencyRate = avgCurrencyRate, priceLook = openclose)
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
            if 'currencyAmount' not in req or req['currencyAmount'] is None:
                currencyAmount = -1
            else:
                currencyAmount = req['currencyAmount']
            if 'avgCurrencyRate' not in req or req['avgCurrencyRate'] is None :
                avgCurrencyRate = -1
            else:
                avgCurrencyRate = req['avgCurrencyRate']  
            #   def getPredict(data, currencySymobol, start_balance, filename, currency_amount, avg_currency_rate, priceLook = 'Close'):
  
            try:
                data = yf.download(currencySymobol, start=startDate, end=endDate).reset_index()
            except:
                data = []
            if len(data) > 0:
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
                        'status_code': 422,
                        'res': {"symbol":"No data found, Please don't selected weekend"}
                    }),
                    mimetype='application/json',
                )
                response.status_code = 422
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


@main.route('/saverl', methods=['POST'])
@login_required
def saveModel():
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
            gamma = 0.95
        else:
            gamma = req['gamma']
        if 'epsilon'not in req:
            epsilon = 1.0
        else:
            epsilon = req['epsilon']
        if 'epsilon_min'not in req:
            epsilon_min = 0.01
        else:
            epsilon_min = req['epsilon_min']
        if 'epsilon_decay'not in req:
            epsilon_decay = 0.995
        else:
            epsilon_decay = req['epsilon_decay']
        if 'currencyAmount' not in req or req['currencyAmount'] is None:
            currencyAmount = -1
        else:
            currencyAmount = req['currencyAmount']
        if 'avgCurrencyRate' not in req or req['avgCurrencyRate'] is None :
            avgCurrencyRate = -1
        else:
            avgCurrencyRate = req['avgCurrencyRate']  
        if 'conditions' not in req:
            conditions = []
        else:
            conditions = req['conditions']
        isParam = False
        isUpdate = False
        isNotError = True
        if model is None:
            response = app.response_class(
            response=json.dumps({
                'status_code': 404,
                'res': {"error":"Not found Model"}
            }),
            mimetype='application/json',
            )
            response.status_code = 404
            return response
        if str(model.user_id) == str(userId):
            newstartDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
            newendDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
            if currencyAmount == -1: currencyAmount = None
            if avgCurrencyRate == -1: avgCurrencyRate = None

            if str(model.model_name) == modelName:
                model.updated_at = now
                model.num_train_date = trainDay
                model.num_test_date = testDay
                model.episode_count = episodeCount 
                model.currency_symobol = currencySymobol
                model.start_balance=startBalance
                model.currency_amount = currencyAmount
                model.avg_currency_rate = avgCurrencyRate
                model.gamma = gamma
                model.epsilon = epsilon
                model.epsilon_min = epsilon_min
                model.epsilon_decay = epsilon_decay
                model.start_date = startDate
                model.end_date = endDate
                model.have_model = False
                model.start_date = newstartDate
                model.end_date = newendDate

                Policy.query.filter(Policy.model_id == model.id).delete()
                for condition in conditions:
                    new_condition = Policy(model_id= model.id,created_at = now, action = condition["action"], con = condition["con"], sym = condition["sym"], num = condition["num"])
                    db.session.add(new_condition)
                db.session.commit()

                response = app.response_class(
                response=json.dumps({
                    'status_code': 200,
                    'res': 'Save Succesful'
                    }),
                mimetype='application/json'
                )
                response.status_code = 200   

            else :
                md = Model.query.filter_by(user_id=userId,).\
                filter_by(model_name = modelName).first()
                if md:
                    isParam = True
                    notFoundParam = 'modelName already exist'
                    isNotError = False
                else:
                    # Save as new model
                    new_Rlmodel = Model(user_id = userId, created_at = now, num_train_date = trainDay, num_test_date = testDay,episode_count = episodeCount ,model_name = modelName, currency_symobol = currencySymobol, have_model = False,  start_balance=startBalance, currency_amount = currencyAmount,avg_currency_rate = avgCurrencyRate,gamma = gamma, epsilon= epsilon, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay,start_date= newstartDate,end_date = newendDate, model_path = '')
                    db.session.add(new_Rlmodel)
                    db.session.commit()
                    md = Model.query.filter_by(user_id=userId,).\
                    filter_by(model_name = modelName).first()
                    for condition in conditions:
                        new_condition = Policy(model_id= md.id,created_at = now, action = condition["action"], con = condition["con"], sym = condition["sym"], num = condition["num"])
                        db.session.add(new_condition)
                    db.session.commit()
                    response = app.response_class(
                        response=json.dumps({
                            'status_code': 201,
                            'res': {"model_id":md.id}
                        }),
                        mimetype='application/json',
                    )
                    response.status_code = 201        
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
    
@main.route('/logTrain', methods=['POST'])
@login_required
def getLogTrain():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
        isParam = True
    else:
        model = Model.query.get(req['modelId'])
        print(model.log_id)
        log = Log.query.get(model.log_id)
        print(log)
        df = pd.DataFrame(columns = ["Episode","TotalPortforlio"])

        if log is not None:
            testList = log.train_text.split(',')
            testList.pop()
            for test in testList:
                temp = test.split('_')

                print(temp[0])
                print(temp[1])
                df = df.append({'Episode': temp[0],'TotalPortforlio' : temp[1]} , ignore_index=True)
            print(df.head())
            response = make_response(df.to_json(orient = "records"),200)
            response.mimetype = 'application/json'
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


@main.route('/logById', methods=['POST'])
@login_required
def getLogById():
    req = request.get_json()
    isParam = False
    app = current_app._get_current_object()
    userId = current_user.get_id()
    if 'modelId' not in req:
        notFoundParam = 'modelId not found'
        isParam = True
    else:
        model = Model.query.get(req['modelId'])
        if model:
            log = Log.query.get(model.log_id)
            if log is not None:
                if str(userId) == str(log.user_id):
                    response = app.response_class(
                        response=json.dumps({
                            'status_code': 200,
                            'res': {
                                "userId":log.user_id,
                                "data":log.log_text,
                                "train":log.train_text}
                        }),
                        mimetype='application/json',
                    )
                    response.status_code = 200
                    return response
                else:
                    response = app.response_class(
                    response=json.dumps({
                        'status_code': 401,
                        'res': {"error":"Unauthorize model"}
                    }),
                    mimetype='application/json',
                    )
                    response.status_code = 401
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