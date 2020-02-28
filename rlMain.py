import pandas as pd
import sys

import pandas as pd

import math, random 
import numpy as np 
from datetime import datetime, timedelta

import keras
from keras.models import Sequential
from keras.models import load_model

from .state import State
from .agent import Agent
import project.function as fc


class Rl():

    def trainModel(data, currencySymobol, episode_count, start_balance, training, test):

        pd_data1_train=data[0:training]
        pd_data1_test=data[training:training+test]
        
        # total_Prof=[]
        # done=False

        Act_datasize = test
        batch_size = 64
        data1_test=pd_data1_test['Close']
        data1_train=pd_data1_train['Close']
        print("//////////////////////////")
        print(pd_data1_train['Date'])
        data1_date=pd_data1_train['Date']
        data1_test=pd_data1_test['Date']

        #Define arrays to store per episode values 
        total_Prof=[]
        total_stock1bal=[]
        # total_stock2bal=[]
        total_open_cash=[]
        total_port_value=[]
        total_days_played=[]


        for e in range(episode_count):
            print("..........")
            print("Episode " + str(e) + "/" + str(episode_count))
            
            Bal_stock1 = int(np.floor((start_balance/2)/data1_train[0]))

            open_cash=start_balance/2
            datasize=training
            done=False
            total_profit = 0
            reward = 0
            
            #Initialize Agent
            agent = Agent(5)
            agent.inventory1 =[]
            open_cash_t1=open_cash
            for i in range(Bal_stock1):
                agent.inventory1.append(data1_train[0])
            Bal_stock1_t1 = len(agent.inventory1)
            
            #Timestep delta to make sure that with time reward increases for taking action
            #timestep_delta=0
            
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
                        agent.inventory1.append(data1_train[t])
                        Bal_stock1_t1= len(agent.inventory1)
                        open_cash_t1=state_class_obj.open_cash-state_class_obj.Stock1Price #Here we are buying 1 stock
                        
                        #needs to be reviewed
                        if(state_class_obj.open_cash<500):
                            reward=-1000
                        elif (state_class_obj.Stock1Price > state_class_obj.fiveday_stock1):
                            reward=abs(state_class_obj.Stock1Price - state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
                            # if(Bal_stock1_t1 == 1):
                            #     reward = 30000
                        else:  
                            reward=-abs(change_percent_stock1)*100
        #                 elif (abs(change_percent_stock1)<=2):
        #                     reward=-10000
        #                 else:  
        #                     reward=-change_percent_stock1*100
                        

                       
                        
                if action == 1:  #sell stock 1
                    if state_class_obj.Stock1Blnc <1 :
                       # print("sold stock 2 when it did not have stock 2, so bankrupt, end of episode")
                        reward=-5000000
                        done = True
                        #end episode
                    else:
                        #print("In sell stock 1")
                        bought_price1=agent.inventory1.pop(0)
                        Bal_stock1_t1= len(agent.inventory1)
                        Bal_stock2_t1=len(agent.inventory2)
                        open_cash_t1=state_class_obj.open_cash+state_class_obj.Stock1Price #State[0] is the price of stock 1. Here we are buying 1 stoc
                  
                        # Need to be review
                        # if(state_class_obj.Stock1Blnc<10):
                        #     reward=-100000
                        if (abs(change_percent_stock1)<=1):
                            reward=-abs(change_percent_stock1)*100
                        else:
                            reward=change_percent_stock1*100 #State[0] is the price of stock 1. Here we are buying 1 stock
                        
                        total_profit += data1_train[t] - bought_price1
                    #print("reward for sell stock1 " + str(reward))
                        
                


        #        TODO Config logic in this Action 
                if action == 2:             # Do nothing action    
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
                    print("Total portfolio value: " + str(next_state_class_obj.portfolio_value)+ "  stock 1 number: " + str(len(agent.inventory1)))
                    print(agent.inventory1)
                    #      +"  stock 2 number: "+str(len(agent.inventory2))+"  open cash"+str(next_state_class_obj.open_cash))
                    total_Prof.append(total_profit)
                    total_stock1bal.append(len(agent.inventory1))
        #             total_stock2bal.append(len(agent.inventory2))
                    total_open_cash.append(state_class_obj.open_cash)
                    total_port_value.append(state_class_obj.portfolio_value)
                    total_days_played.append(t)
                    if len(agent.memory) <= batch_size:
                        print("^_^")
                        agent.expReplay(len(agent.memory))


                    print("--------------------------------")
        #             state_class_obj.reset()
                    break
                   
                  

                if len(agent.memory) > batch_size:
                    agent.expReplay(batch_size)


            if e % 10 == 0:
                print("e%10")
                agent.model.save("./project/modelsRl/model_ep" + str(e)+".h5")

        return fc.formatPrice(total_profit)

    # stock_name1, episode_count, start_balance, training, test = 'AOT.BK', 50,10000,731,240
    # pd_data1=pd.read_csv('data/'+stock_name1+'.csv', sep=",", header=0)


# pd_data1['Date']=pd.to_datetime(pd_data1['Date'], format='%Y/%m/%d')
# # pd_data2['Date']=pd.to_datetime(pd_data2['Date'], format='%Y/%m/%d')

# list1= pd_data1['Date']
# pd_data1_train=pd_data1[0:training]
# # pd_data2_train=pd_data2[0:training]
# #Test Data
# pd_data1_test=pd_data1[training:training+test]
# # pd_data2_test=pd_data2[training:training+test]
# pd_data1_test=pd_data1_test.reset_index(drop=True) 


# vol1_train=getStockVolVec(stock_name1)
# # vol2_train=getStockVolVec(stock_name2)

# total_Prof=[]
# done=False

# Act_datasize = test
# batch_size = 64

# #Benchmark Model

# data1_test=pd_data1_test['Open']
# data1_train=pd_data1_train['Open']

# data1_date=pd_data1_train['Date']
# data1_test=pd_data1_test['Date']

# #Define arrays to store per episode values 
# total_Prof=[]
# total_stock1bal=[]
# # total_stock2bal=[]
# total_open_cash=[]
# total_port_value=[]
# total_days_played=[]


# # In[ ]:


# # #Initialize Agent
# # agent = Agent(5)
# # Bal_stock1=int(0)
# # open_cash=start_balance
    
# # datasize=training
# # reward = 0
# # state_class_obj= State(data1_train, Bal_stock1, open_cash,0)
# # state_array_obj=state_class_obj.getState()
# # action = agent.act(state_array_obj)


# # In[ ]:


# # # #Initialize Agent
# # # agent = Agent(5)
# # # Bal_stock1=int(0)
# # # open_cash=start_balance
    
# # # datasize=training
# # # reward = 0
# # # state_class_obj= State(data1_train, Bal_stock1, open_cash,0)
# # # state_array_obj=state_class_obj.getState()
# # # action = agent.act(state_array_obj)
# # print("Agent memory = "+ str(len(agent.memory)))
# # print("Action ="+ str(action))
# # print(agent.getPredict(state_array_obj))
# # next_state_class_obj=State(data1_train, Bal_stock1, open_cash,1)
# # next_state_array_obj=next_state_class_obj.getState()
# # print("..........")   
# # #                          state, action, reward, next_state, done
# # agent.memory.append((state_array_obj, 1, -500000, next_state_array_obj, True))
# # # agent.expReplay(len(agent.memory))
# # print(agent.getPredict(next_state_array_obj))
# # print("Agent memory = "+ str(len(agent.memory)))


# # In[ ]:


# #Training run

# import csv


# for e in range(episode_count + 1):
#     print("..........")
#     print("Episode " + str(e) + "/" + str(episode_count))
    
# #     Bal_stock1=int(0)
#     Bal_stock1 = int(np.floor((start_balance/2)/data1_train[0]))
# #     Bal_stock2=int(np.floor((start_balance/4)/data2_train[0]))
#     open_cash=start_balance/2
#     datasize=training
#     done=False
#     total_profit = 0
#     reward = 0
    
#     #Initialize Agent
#     agent = Agent(5)
#     agent.inventory1 =[]
#     open_cash_t1=open_cash
# #     agent.inventory2 =[]
#     for i in range(Bal_stock1):
#         agent.inventory1.append(data1_train[0])
#     Bal_stock1_t1 = len(agent.inventory1)
# #     for i in range(Bal_stock2):
# #         agent.inventory2.append(data2_train[0]) 
    
    
#     #Timestep delta to make sure that with time reward increases for taking action
#     #timestep_delta=0
    
#     #Running episode over all days in the datasize
#     for t in range(datasize):
# #         print(datasize)
#         #print(pd_data1_train.iloc[t,0])
#         state_class_obj= State(data1_train, Bal_stock1, open_cash,t)
#         state_array_obj=state_class_obj.getState()
#         action = agent.act(state_array_obj)
                   
#         change_percent_stock1=(state_class_obj.Stock1Price-state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
# #         change_percent_stock2=(state_class_obj.Stock2Price-state_class_obj.fiveday_stock2)/state_class_obj.fiveday_stock2*100
        
#         #print("change_percent_stock1:  "+str(change_percent_stock1))
#         #print("change_percent_stock2:  "+str(change_percent_stock2))
        
        
#         if action == 0:  #buy stock 1
#             if state_class_obj.Stock1Price > state_class_obj.open_cash:
#                 '''
#                 print("Buy stock 1 when it did not have cash, so bankrupt, end of episode")
#                 reward=-reward_timedelta*10
#                 done = True
#                 '''
#                 #If agent is trying to buy when it has no cash but has stock1 and stock2 balance then, 
#                 #it should pick from other actions
#                 #if (state_class_obj.Stock1Blnc>1) and  (state_class_obj.Stock2Blnc>1):
#                  #   action=random.sample([1, 2, 4, 5, 6],  1)  # Choose 1 elements from sell actions
#                 #else:    
#                 #print("Bankrupt")
#                 reward=-200000
#                 done = True
#                 #end episode
                     
#             else:
#                 #print("In Buy stock 1")
#                 agent.inventory1.append(data1_train[t])
#                 Bal_stock1_t1= len(agent.inventory1)
#                 open_cash_t1=state_class_obj.open_cash-state_class_obj.Stock1Price #Here we are buying 1 stock
                
#                 #needs to be reviewed
#                 if(state_class_obj.open_cash<500):
#                     reward=-1000
#                 elif (state_class_obj.Stock1Price > state_class_obj.fiveday_stock1):
#                     reward=abs(state_class_obj.Stock1Price - state_class_obj.fiveday_stock1)/state_class_obj.fiveday_stock1*100
#                     if(Bal_stock1_t1 == 1):
#                         reward = 30000
#                 else:  
#                     reward=-abs(change_percent_stock1)*100
# #                 elif (abs(change_percent_stock1)<=2):
# #                     reward=-10000
# #                 else:  
# #                     reward=-change_percent_stock1*100
                

               
                
#         if action == 1:  #sell stock 1
#             if state_class_obj.Stock1Blnc <1 :
#                # print("sold stock 2 when it did not have stock 2, so bankrupt, end of episode")
#                 reward=-5000000
#                 done = True
#                 #end episode
#             else:
#                 #print("In sell stock 1")
#                 bought_price1=agent.inventory1.pop(0)
#                 Bal_stock1_t1= len(agent.inventory1)
#                 Bal_stock2_t1=len(agent.inventory2)
#                 open_cash_t1=state_class_obj.open_cash+state_class_obj.Stock1Price #State[0] is the price of stock 1. Here we are buying 1 stoc
          
#                 if(state_class_obj.Stock1Blnc<10):
#                     reward=-100000
#                 elif (abs(change_percent_stock1)<=1):
#                     reward=-abs(change_percent_stock1)*100
#                 else:
#                     reward=change_percent_stock1*100 #State[0] is the price of stock 1. Here we are buying 1 stock
                
#                 #total_profit += data1_train[t] - bought_price1
#             #print("reward for sell stock1 " + str(reward))
                
        


# #        TODO Config logic in this Action 
#         if action == 2:             # Do nothing action    
#                 if (abs(change_percent_stock1)<=2):
#                     reward=100
#                 elif (state_class_obj.open_cash<0.1*start_balance):
#                     reward=-1000000
# #                 else:
# #                     reward=-100000
                
#                 Bal_stock1_t1= len(agent.inventory1)
# #                 Bal_stock2_t1=len(agent.inventory2)
#                 open_cash_t1=open_cash
#                # print("Do nothing")
            
        
        
#         #print("reward:  "+str(reward))
#         #if done!= False:done = True if t == datasize
#         if t == datasize-1:
#             #print("t==datasize")
#             done=True
#             next_state_class_obj=State(data1_train, Bal_stock1_t1, open_cash_t1,t)
#             next_state_array_obj=next_state_class_obj.getState()
#         else:
#             next_state_class_obj=State(data1_train, Bal_stock1_t1, open_cash_t1,t+1)
#             next_state_array_obj=next_state_class_obj.getState()
            
#         agent.memory.append((state_array_obj, action, reward, next_state_array_obj, done))
#         #print("Action is "+str(action)+" reward is" + str(reward))
         
#         Bal_stock1=Bal_stock1_t1
# #         Bal_stock2= Bal_stock2_t1
#         open_cash=open_cash_t1
        
        
#       #  print("total_profit on day basis " + str(total_profit) +"on day"+str(t) + "stock 1 number: " + 
#         #      str(len(agent.inventory1))+"/"+str(next_state_class_obj.Stock1Blnc)+" stock2 number:"+
#          #         str(len(agent.inventory2)) +"/"+str(next_state_class_obj.Stock2Blnc)+
#           #        "open cash: "+str(next_state_class_obj.open_cash))
        
#        # print("doneAction" + str(done))
#        # print("--------------------------------") 
       
        
        
#         if done==True:
#             print("--------------------------------")
#             print("Total Profit: " + formatPrice(total_profit))
#             print("Total No. of days played: " + str(t)+ "  out of overall days:  " + str(datasize))
#             print("Total portfolio value: " + str(next_state_class_obj.portfolio_value)+ "  stock 1 number: " + str(len(agent.inventory1)))
#             #      +"  stock 2 number: "+str(len(agent.inventory2))+"  open cash"+str(next_state_class_obj.open_cash))
#             total_Prof.append(total_profit)
#             total_stock1bal.append(len(agent.inventory1))
# #             total_stock2bal.append(len(agent.inventory2))
#             total_open_cash.append(state_class_obj.open_cash)
#             total_port_value.append(state_class_obj.portfolio_value)
#             total_days_played.append(t)
#             if len(agent.memory) <= batch_size:
#                 print("^_^")
#                 agent.expReplay(len(agent.memory))


#             print("--------------------------------")
# #             state_class_obj.reset()
#             break
           
          

#         if len(agent.memory) > batch_size:
#             agent.expReplay(batch_size)


#     if e % 10 == 0:
#         agent.model.save("models/model_ep" + str(e)+".h5")
        





# # In[ ]:


# print("Total Apple stocks in episodes"+ str(total_stock1bal))
# print("///////")
# # print("Total Amazon stocks in episodes"+ str(total_stock2bal))
# print("Total Open cash in episodes"+ str(total_open_cash))
# print("Total Portfolio value in episodes"+ str(total_port_value))
# print("------------------------------")
# print("Total Days in episodes"+ str(total_days_played))

# print("Benchmark_Profit is  " + str(int(Training_Benchmark_Portfolio_Value)) +"   with remaining Apple Stocks: " + str(remaining_stock1))


# # In[ ]:


# pd_data1_test=pd_data1_test.reset_index(drop=True)
# data1_test=pd_data1_test['Open']
# print(pd_data1_test.head())
# print(pd_data1_test.tail())