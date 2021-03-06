import pandas as pd
import sys

import pandas as pd
import os

import math, random 
import numpy as np 
from datetime import datetime, timedelta
from . import db

from tensorflow import keras
import keras
from keras.models import Sequential
from keras.models import load_model
from keras.backend import clear_session


from .state import State
from .agent import Agent
import project.function as fc
import time 
import operator


class Rl():

    def trainModel(data, currencySymobol, episode_count, start_balance, training, test, model_name, log, isUpdate = False, OldmodelPath = "",currencyAmount = -1, avgCurrencyRate = -1,gamma = 0.95, epsilon = 1.0, epsilon_min = 0.01, epsilon_decay = 0.995, conditions = [], openclose = 'Close', buyLotSize = -1, saleLotSize = -1):

        pd_data1_train=data[0:training]
        pd_data1_test=data[training:training+test]

        Act_datasize = test
        batch_size = 64
        data1_test=pd_data1_test['Close']
        data1_train=pd_data1_train['Close']
        print("//////////////////////////")
        data1_date=pd_data1_train['Date']
        data1_test=pd_data1_test['Date']
        filename = ""
        #Define arrays to store per episode values 
        total_Prof=[]
        total_stock1bal=[]
        # total_stock2bal=[]
        total_open_cash=[]
        total_port_value=[]
        total_days_played=[]

        buyPolicy = []
        sellPolicy = []
        holdPolicy = []

        if len(conditions) > 0: 
            isPolicy = True 
            ops = { ">": operator.gt, "<": operator.lt, "=": operator.eq, ">=": operator.ge, "<=": operator.le }
            for condition in conditions:
                if condition["action"] == "buy":
                    buyPolicy.append(condition)
                elif condition["action"] == "sell":
                    sellPolicy.append(condition)
                elif condition["action"] == "hold":
                    holdPolicy.append(condition)
                
        else: isPolicy = False


        log.log_text = '    ---------- Training ---------- \n'     
        for e in range(episode_count):
            print("..........")
            print("Episode " + str(e+1) + "/" + str(episode_count))
            log.log_text = log.log_text + "Episode " + str(e+1) + "/" + str(episode_count)
            db.session.commit()

            open_cash=start_balance/2
            datasize=training
            done=False
            total_profit = 0
            reward = 0
            buySize = 50
            maxSize = 100
            totalInven = 0
            avgInven = -1
            #Initialize Agent

            agent = Agent(5, gamma = gamma, epsilon= epsilon, epsilon_min=epsilon_min, epsilon_decay=epsilon_decay)
            agent.inventory1 =[]
            
            if currencyAmount == 0: currencyAmount = -1
            if avgCurrencyRate == 0: avgCurrencyRate = -1
            if currencyAmount != -1 and avgCurrencyRate != -1:
                for i in range(currencyAmount):
                    agent.inventory1.append(avgCurrencyRate)
                    totalInven = totalInven + avgCurrencyRate
                open_cash = start_balance
            else:
                Bal_stock1 = int(np.floor((start_balance/2)/data1_train[0]))
                for i in range(Bal_stock1):
                    agent.inventory1.append(data1_train[0])
                    totalInven = totalInven + data1_train[0]
                open_cash = start_balance - (data1_train[0] * len(agent.inventory1))
            Bal_stock1_t1 = len(agent.inventory1)
            Bal_stock1 = Bal_stock1_t1
            if Bal_stock1_t1 == 0: avgInven = 0
            else:avgInven = totalInven/Bal_stock1_t1
            #Timestep delta to make sure that with time reward increases for taking action
            #timestep_delta=0
            open_cash_t1=open_cash
            #Running episode over all days in the datasize
            for t in range(datasize):
        #         print(datasize)
                #print(pd_data1_train.iloc[t,0])
                state_class_obj= State(data1_train, Bal_stock1, open_cash,t)
                state_array_obj=state_class_obj.getState()
                action = agent.act(state_array_obj)
                           
                change_percent_stock1=(state_class_obj.Stock1Price-state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
        #         change_percent_stock2=(state_class_obj.Stock2Price-state_class_obj.fiveday_stock2)/state_class_obj.fiveday_stock2*100
                
                #print("change_percent_stock1:  "+str(change_percent_stock1))
                #print("change_percent_stock2:  "+str(change_percent_stock2))
                
                
                if action == 0:  #buy stock 1
                    if state_class_obj.Stock1Price > state_class_obj.open_cash:
                        '''
                        print("Buy stock 1 when it did not have cash, so bankrupt, end of episode")
                        reward=-reward_timedelta*10
                        done = True
                        '''
                        #If agent is trying to buy when it has no cash but has stock1 and stock2 balance then, 
                        #it should pick from other actions
                        #if (state_class_obj.Stock1Blnc>1) and  (state_class_obj.Stock2Blnc>1):
                         #   action=random.sample([1, 2, 4, 5, 6],  1)  # Choose 1 elements from sell actions
                        #else:    
                        #print("Bankrupt")
                        reward=-200000
                        done = True
                        #end episode
                             
                    else:
                        #print("In Buy stock 1")
                        if buyLotSize == -1:
                            buytemp = state_class_obj.open_cash/buySize
                            buyamount = np.floor(buytemp/data1_train[t])
                            if buyamount == 0: buyamount = 1
                            for i in range(int(buyamount)):
                                agent.inventory1.append(data1_train[t])
                                totalInven = totalInven + data1_train[t]
                            # print(len(agent.inventory1))
                            Bal_stock1_t1= len(agent.inventory1)
                            avgInven = totalInven/Bal_stock1_t1
                            open_cash_t1=state_class_obj.open_cash - state_class_obj.Stock1Price * buyamount #Here we are buying 1 stock
                            buySize = buySize - 1
                        else:
                            for i in range(int(buyLotSize)):
                                agent.inventory1.append(data1_train[t])
                                totalInven = totalInven + data1_train[t]
                            Bal_stock1_t1= len(agent.inventory1)
                            avgInven = totalInven/Bal_stock1_t1
                            open_cash_t1=state_class_obj.open_cash - state_class_obj.Stock1Price * buyLotSize
                        #needs to be reviewed
                        if(state_class_obj.open_cash<500):
                            reward=-1000
                        else:
                            isBuyDeafault = True
                            if isPolicy and len(buyPolicy) > 0:
                                isBuyDeafault = False
                                opera = buyPolicy[0]["con"]
                                sym = buyPolicy[0]["sym"]
                                num = float(buyPolicy[0]["num"])
                                if sym == 'ma':
                                    averageXday = Rl.ma_x_day_window(data1_train, t, num)
                                    if ops[opera](state_class_obj.Stock1Price ,averageXday):
                                        reward=abs(state_class_obj.Stock1Price - averageXday)/averageXday*100
                                    else:
                                        # Might change Change percent Stock
                                        reward=-abs(change_percent_stock1)*100
                                elif sym == 'profit':
                                    percentproit = (state_class_obj.Stock1Price - avgInven)/avgInven * 100
                                    if ops[opera](percentproit ,num):
                                        reward= abs(percentproit)*100
                                    else:
                                        reward= -abs(percentproit)*100
                                elif sym == 'change':
                                    averageOneDay = Rl.ma_x_day_window(data1_train, t, 1)
                                    changePercent = (state_class_obj.Stock1Price-averageOneDay)/averageOneDay*100
                                    if ops[opera](changePercent ,num):
                                        reward= abs(changePercent)*100
                                    else:
                                        reward= -abs(changePercent)*100
                                elif sym == 'change5':
                                    if ops[opera](change_percent_stock1 ,num):
                                        reward= abs(change_percent_stock1)*100
                                    else:
                                        reward= -abs(change_percent_stock1)*100
                                else: #Default same as below
                                    isBuyDeafault = True

                            if isBuyDeafault:
                                print("Default for Buy")
                                if state_class_obj.Stock1Price > state_class_obj.fiveday_stock1:
                          
                                    reward=abs(state_class_obj.Stock1Price - state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
                                else:  
                                    reward=-abs(change_percent_stock1)*100
                        

                       
                        
                if action == 1:  #sell stock 1
                    if state_class_obj.Stock1Blnc <1 :
                       # print("sold stock 2 when it did not have stock 2, so bankrupt, end of episode")
                        reward=-5000000
                        done = True
                        #end episode
                    else:
                        TotalBought = 0
                        if saleLotSize == -1:
                            sellSize = maxSize - buySize
                            buySize = buySize + 1
                            tempSale = np.floor(Bal_stock1_t1 / sellSize)
                            if tempSale == 0: tempSale = 1
                            for j in range(int(tempSale)):
                                bought_price1 = agent.inventory1.pop(0)
                                TotalBought = TotalBought + avgInven
                                totalInven = totalInven - avgInven
                            Bal_stock1_t1= len(agent.inventory1)
                            avgInven = totalInven/Bal_stock1_t1
                            open_cash_t1 = state_class_obj.open_cash + (state_class_obj.Stock1Price * tempSale) #State[0] is the price of stock 1. Here we are buying 1 stoc
                        else:
                            for j in range(int(saleLotSize)):
                                bought_price1 = agent.inventory1.pop(0)
                                TotalBought = TotalBought + avgInven
                                totalInven = totalInven - avgInven
                            Bal_stock1_t1= len(agent.inventory1)
                            avgInven = totalInven/Bal_stock1_t1
                            open_cash_t1 = state_class_obj.open_cash + (state_class_obj.Stock1Price * saleLotSize)
                        # Need to be review
                        # if(state_class_obj.Stock1Blnc<10):
                        #     reward=-100000
                        if (abs(change_percent_stock1)<=1):
                            reward=-abs(change_percent_stock1)*100
                        else:
                            
                            isSellDeafault = True
                            if isPolicy and len(sellPolicy) > 0:
                                isSellDeafault = False
                                opera = sellPolicy[0]["con"]
                                sym = sellPolicy[0]["sym"]
                                num = float(sellPolicy[0]["num"])
                                if sym == 'ma':
                                    averageXday = Rl.ma_x_day_window(data1_train, t, num)
                                    if ops[opera](state_class_obj.Stock1Price ,averageXday):
                                        reward=abs(state_class_obj.Stock1Price - averageXday)/averageXday*100
                                    else:
                                        # Might change Change percent Stock
                                        reward=-abs(change_percent_stock1)*100
                                elif sym == 'profit':
                                    percentproit = (state_class_obj.Stock1Price - avgInven)/avgInven * 100
                                    if ops[opera](percentproit ,num):
                                        reward= abs(percentproit)*100
                                    else:
                                        reward= -abs(percentproit)*100
                                elif sym == 'change':
                                    averageOneDay = Rl.ma_x_day_window(data1_train, t, 1)
                                    changePercent = (state_class_obj.Stock1Price-averageOneDay)/averageOneDay*100
                                    if ops[opera](changePercent ,num):
                                        reward= abs(changePercent)*100
                                    else:
                                        reward= -abs(changePercent)*100
                                elif sym == 'change5':
                                    if ops[opera](change_percent_stock1 ,num):
                                        reward= abs(change_percent_stock1)*100
                                    else:
                                        reward= -abs(change_percent_stock1)*100
                                else: #Default same as below
                                    isSellDeafault = True

                            if isSellDeafault:
                                reward=change_percent_stock1*100 #State[0] is the price of stock 1. Here we are buying 1 stock
                    if not done:
                        if saleLotSize == -1:
                            total_profit += (tempSale * data1_train[t]) - TotalBought
                        else:
                            total_profit += (saleLotSize * data1_train[t]) - TotalBought
                        
                if action == 2:             # Do nothing action    
                    isHoldDeafault = True
                    if isPolicy and len(holdPolicy) > 0:
                        isHoldDeafault = False
                        opera = holdPolicy[0]["con"]
                        sym = holdPolicy[0]["sym"]
                        num = float(holdPolicy[0]["num"])
                        if sym == 'ma':
                            averageXday = Rl.ma_x_day_window(data1_train, t, num)
                            if ops[opera](state_class_obj.Stock1Price ,averageXday):
                                reward=abs(state_class_obj.Stock1Price - averageXday)/averageXday*100
                            else:
                                # Might change Change percent Stock
                                reward=-abs(change_percent_stock1)*100
                        elif sym == 'profit':
                            percentproit = (state_class_obj.Stock1Price - avgInven)/avgInven * 100
                            if ops[opera](percentproit ,num):
                                reward= abs(percentproit)*100
                            else:
                                reward= -abs(percentproit)*100
                        elif sym == 'change':
                            averageOneDay = Rl.ma_x_day_window(data1_train, t, 1)
                            changePercent = (state_class_obj.Stock1Price-averageOneDay)/averageOneDay*100
                            if ops[opera](changePercent ,num):
                                reward= abs(changePercent)*100
                            else:
                                reward= -abs(changePercent)*100
                        elif sym == 'change5':
                            if ops[opera](change_percent_stock1 ,num):
                                reward= abs(change_percent_stock1)*100
                            else:
                                reward= -abs(change_percent_stock1)*100
                        else: #Default same as below
                            isHoldDeafault = True

                    if isHoldDeafault:
                        if (abs(change_percent_stock1)<=2):
                            reward=100
                        elif (state_class_obj.open_cash<0.1*start_balance):
                            reward=-1000000
        #                 else:
        #                     reward=-100000
                        
                        Bal_stock1_t1= len(agent.inventory1)
        #                 Bal_stock2_t1=len(agent.inventory2)
                        open_cash_t1=open_cash
                       # print("Do nothing")
                    
                
                
                #print("reward:  "+str(reward))
                #if done!= False:done = True if t == datasize

                if t == datasize-1:
                    #print("t==datasize")
                    done=True
                    next_state_class_obj=State(data1_train, Bal_stock1_t1, open_cash_t1,t)
                    next_state_array_obj=next_state_class_obj.getState()
                else:
                    next_state_class_obj=State(data1_train, Bal_stock1_t1, open_cash_t1,t+1)
                    next_state_array_obj=next_state_class_obj.getState()
                    
                agent.memory.append((state_array_obj, action, reward, next_state_array_obj, done))
                #print("Action is "+str(action)+" reward is" + str(reward))
                 
                Bal_stock1=Bal_stock1_t1
        #         Bal_stock2= Bal_stock2_t1
                open_cash=open_cash_t1
                
                
              #  print("total_profit on day basis " + str(total_profit) +"on day"+str(t) + "stock 1 number: " + 
                #      str(len(agent.inventory1))+"/"+str(next_state_class_obj.Stock1Blnc)+" stock2 number:"+
                 #         str(len(agent.inventory2)) +"/"+str(next_state_class_obj.Stock2Blnc)+
                  #        "open cash: "+str(next_state_class_obj.open_cash))
                
               # print("doneAction" + str(done))
               # print("--------------------------------") 
               
                
                if done==True:
                    print("--------------------------------")
                    print("Total Profit: " + fc.formatPrice(total_profit))
                    print("Total No. of days played: " + str(t+1)+ "  out of overall days:  " + str(datasize))
                    print("Price day 1 :"+ str(data1_train[0]) + " last day :"+ str(data1_train[t]) + " percen Change: "+str((data1_train[t]- data1_train[0])/data1_train[0]* start_balance/100))
                    print("Total portfolio value: " + str(next_state_class_obj.portfolio_value)+ "  stock 1 number: " + str(len(agent.inventory1)))
                    # print(agent.inventory1)
                    #      +"  stock 2 number: "+str(len(agent.inventory2))+"  open cash"+str(next_state_class_obj.open_cash))
                    log.log_text = log.log_text + " Total port value: " +"{0:,.2f}".format(next_state_class_obj.portfolio_value)+"\n"
                    log.train_text = log.train_text +str(e+1)+"_" +str(next_state_class_obj.portfolio_value)+","
                    total_Prof.append(total_profit)
                    total_stock1bal.append(len(agent.inventory1))
        #             total_stock2bal.append(len(agent.inventory2))
                    total_open_cash.append(state_class_obj.open_cash)
                    total_port_value.append(state_class_obj.portfolio_value)
                    total_days_played.append(t)
                    if len(agent.memory) <= batch_size:
                        agent.expReplay(len(agent.memory))


                    print("--------------------------------")
        #             state_class_obj.reset()
                    break
                if len(agent.memory) > batch_size:
                    agent.expReplay(batch_size)
            if e+1 == episode_count:
                print("Episode"+str(episode_count))
                filename = str(log.user_id)+"_"+str(model_name)+"_model_ep" + str(e)+".h5"
                if isUpdate:
                    try:
                        os.remove("./project/modelsRl/"+OldmodelPath)
                    except:
                        print("Delete Not Found")
                agent.model.save("./project/modelsRl/"+filename)
                print("Save Done")
                clear_session()
                # agent.clearSeassion()
        log.log_text =  log.log_text + '    ---------- Testing ---------- \n'     
        Rl.testRl(data, currencySymobol, start_balance, training, test, filename, log, currencyAmount = currencyAmount, avgCurrencyRate = avgCurrencyRate)
        return filename

    def testRl(data, currencySymobol, start_balance, training, test, filename, log, priceLook = 'Close', currencyAmount = -1, avgCurrencyRate = -1):
        pd_data1_test=data[training:training+test].reset_index(drop=True)
        print(pd_data1_test.head())
        pddates = pd_data1_test['Date']
        data1_test=pd_data1_test[priceLook]

        total_Prof=[]
        total_stock1bal=[]
        # total_stock2bal=[]
        total_open_cash=[]
        total_port_value=[]
        total_days_played=[]
        if currencyAmount == 0: currencyAmount = -1
        if avgCurrencyRate == 0: avgCurrencyRate = -1
        resultText = ""
        for e in range(1):
        #     Bal_stock1 = 0
            Bal_stock1 = int(np.floor((start_balance/2)/data1_test[0]))
            open_cash=start_balance
            datasize=test
            done=False
            total_profit = 0
            reward = 0
            totalInven = 0
            buySize = 50
            maxSize = 100
            temp = avgCurrencyRate * currencyAmount
            if temp == 1: startPort = start_balance
            else:  startPort = start_balance + avgCurrencyRate * currencyAmount
            agent = Agent(5, is_eval=True, model_name=filename)
            agent.inventory1 =[]
            
            if currencyAmount != -1 and avgCurrencyRate != -1:
                for i in range(currencyAmount):
                    agent.inventory1.append(avgCurrencyRate)
                    totalInven = totalInven + avgCurrencyRate
                open_cash = start_balance
            else:
                Bal_stock1 = int(np.floor((start_balance/2)/data1_test[0]))
                for i in range(Bal_stock1):
                    agent.inventory1.append(data1_test[0])
                    totalInven = totalInven + data1_test[0]
                open_cash = start_balance - (data1_test[0] * len(agent.inventory1))
            Bal_stock1_t1 = len(agent.inventory1)
            Bal_stock1 = Bal_stock1_t1
            if Bal_stock1_t1 == 0: avgInven = 0
            else:avgInven = totalInven/Bal_stock1_t1
            open_cash_t1=open_cash
            #Running episode over all days in the datasize
            for t in range(datasize):
                state_class_obj= State(data1_test, Bal_stock1, open_cash,t)
                state_array_obj=state_class_obj.getState()
        #         print("State = get State ========")
        #         print(state_array_obj)
                action = agent.act(state_array_obj)
        #         print("Agent .get predict = ")
        #         print(agent.getPredict(state_array_obj))       
                change_percent_stock1=(state_class_obj.Stock1Price-state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
                
                if action == 0:  #buy stock 1

                    if state_class_obj.Stock1Price > state_class_obj.open_cash:
                        resultText = resultText + "Test Day "+ str(t+1) + " Buy but did not have cash, so bankrupt, end of episode"
                        '''
                        print("Buy stock 1 when it did not have cash, so bankrupt, end of episode")
                        reward=-reward_timedelta*10
                        done = True
                        '''
                        done = True
                        #end episode
                            
                    else:
                        buytemp = state_class_obj.open_cash/buySize
                        buyamount = np.floor(buytemp/data1_test[t])
                        if buyamount == 0: buyamount = 1
                        for i in range(int(buyamount)):
                            agent.inventory1.append(data1_test[t])
                            totalInven = totalInven + data1_test[t]
                        # print(len(agent.inventory1))
                        Bal_stock1_t1= len(agent.inventory1)
                        avgInven = totalInven/Bal_stock1_t1
                        open_cash_t1=state_class_obj.open_cash-state_class_obj.Stock1Price * buyamount #Here we are buying 1 stock
                        buySize = buySize - 1
                        resultText = resultText + "Test Day "+ str(t+1) + " Buy "
                        

                    
                        
                if action == 1:  #sell stock 1
                    if state_class_obj.Stock1Blnc <1 :
                        done = True
                        resultText = resultText + "Test Day "+ str(t+1) + " Sell but don't have cyrrency left "
                    else:
                        sellSize = maxSize - buySize
                        buySize = buySize + 1
                        tempSale = np.floor(Bal_stock1_t1 / sellSize)
                        if tempSale == 0: tempSale = 1
                        TotalBought = 0
                        for j in range(int(tempSale)):
                            bought_price1 = agent.inventory1.pop(0)
                            TotalBought = TotalBought + bought_price1
                            totalInven = totalInven - avgInven
                        Bal_stock1_t1= len(agent.inventory1)
                        avgInven = totalInven/Bal_stock1_t1
                        open_cash_t1 = state_class_obj.open_cash + (state_class_obj.Stock1Price * tempSale) #State[0] is the price of stock 1. Here we are buying 1 stoc
                        resultText = resultText + "Test Day "+ str(t+1) + " Sell "
                
                if action == 2:             # Do nothing action
                    print("Hold")

                    Bal_stock1_t1= len(agent.inventory1)
                    resultText = resultText + "Test Day "+ str(t+1) + " Hold "
                    

                if t == datasize-1:
                    #print("t==datasize")
                    done=True
                    next_state_class_obj=State(data1_test, Bal_stock1_t1, open_cash_t1,t)
                    next_state_array_obj=next_state_class_obj.getState()
                else:
                    next_state_class_obj=State(data1_test, Bal_stock1_t1, open_cash_t1,t+1)
                    next_state_array_obj=next_state_class_obj.getState()
                    
                agent.memory.append((state_array_obj, action, reward, next_state_array_obj, done))
                
                Bal_stock1=Bal_stock1_t1
                open_cash=open_cash_t1

                resultText = resultText + "|Balance: "+str(Bal_stock1)+" open_cash: "+"{0:,.2f}".format(open_cash)+"  \n"
                
                if done==True:
                    print()
                    # print(pd_data1_test[t])
                # print("Total Profit: " + formatPrice(total_profit))
                # print("Total No. of days played: " + str(t)+ "  out of overall days:  " + str(datasize))
                # print("Total portfolio value: " + str(next_state_class_obj.portfolio_value)+ 
                    #     "  stock 1 number: " + str(len(agent.inventory1))
                    #      +"  stock 2 number: "+str(len(agent.inventory2))+"  open cash"+str(next_state_class_obj.open_cash))
                    resultText = resultText + " ---------- Testing Summary On Last day ("+pddates[t].strftime("%x")+")---------- \n"
                    resultText = resultText + "Total "+ str(currencySymobol)+" in Balance "+ str(Bal_stock1) + "\n Total Open cash in episodes "+ "{0:,.2f}".format(open_cash)+ " \n Total Portfolio value in episodes "+ "{0:,.2f}".format(state_class_obj.portfolio_value) +" \n Total Days in episodes "+ str(t+1) + "\n"+ "Total Profit: " + "{0:,.2f}".format(state_class_obj.portfolio_value - startPort) + "\n"+ "Total Profit %: " + "{0:,.2f}".format((state_class_obj.portfolio_value - startPort)/startPort*100) + " %"
                    if log is not None:
                        log.log_text = log.log_text + resultText
                        db.session.commit()
                    print("Total "+ str(currencySymobol)+" in Balance "+ str(Bal_stock1))
                    # print("Total Amazon stocks in episodes"+ str(total_stock2bal))
                    print("Total Open cash in episodes "+ str(open_cash))
                    print("Total Portfolio value in episodes "+ str(state_class_obj.portfolio_value))
                    print("------------------------------")
                    print("Total Days in episodes "+ str(t+1))

                    print("--------------------------------")
                    clear_session()
                    break
        return resultText
            

    def getPredict(data, currencySymobol, start_balance, filename, currency_amount, avg_currency_rate, priceLook = 'Close'):
        pd_data1_test=data
        data1_test=pd_data1_test[priceLook]

        total_Prof=[]
        total_stock1bal=[]
        # total_stock2bal=[]
        total_open_cash=[]
        total_port_value=[]
        total_days_played=[]

        for e in range(1):
        #     Bal_stock1 = 0
            Bal_stock1 = int(np.floor((start_balance/2)/data1_test[0]))
            open_cash=start_balance
            datasize=1
            done=False
            total_profit = 0
            reward = 0
            
            agent = Agent(5, is_eval=True, model_name=filename)
            agent.inventory1 =[]
            open_cash_t1=open_cash
            for i in range(currency_amount):
                agent.inventory1.append(avg_currency_rate)
                
            Bal_stock1_t1 = len(agent.inventory1)
            #Running episode over all days in the datasize
            for t in range(datasize):
                state_class_obj= State(data1_test, Bal_stock1, open_cash,t)
                state_array_obj=state_class_obj.getState()
        #         print("State = get State ========")
                # print(state_array_obj)
                action = agent.act(state_array_obj)
        #         print("Agent .get predict = ")
                print(agent.getPredict(state_array_obj))
                statePredict = agent.getState(state_array_obj)
                print(str(statePredict))
                print(statePredict[0][0])
                # print(action)           
        actionName = "Buy State = "+ str(statePredict[0][0]) + "\n" + "Sell State = "+ str(statePredict[0][1]) +  "\n" + "Hold State = "+ str(statePredict[0][2]) + "\n\n"
        if action == 0:  #buy stock 1
            actionName = actionName + "Model Suggest to Buy"
        elif action == 1:  #sell stock 1
            actionName = actionName + "Model Suggest to Sell"
        else:
            actionName = actionName + "Model Suggest to Hold"

        clear_session()
        return actionName

    def ma_x_day_window(data, timestep, x):
        day = int(np.floor(x))
        step = timestep
        if step < day:
            return data[0]
        
        stock_xdays = np.mean(data[step-day:step])

        return stock_xdays