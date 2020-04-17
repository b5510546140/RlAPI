# Agent
import keras
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense
from keras.optimizers import Adam

import numpy as np
import random
from collections import deque


class Agent:
    def __init__(self, state_size, is_eval=False, model_name="",gamma = 0.95,epsilon = 1.0, epsilon_min = 0.01, epsilon_decay = 0.995):
        self.state_size = state_size # normalized previous days
        self.action_size = 3 #  buy_1, sell_1,DO Nothing
        self.memory = deque(maxlen=2000)
        self.inventory1 = []
        self.inventory2 = []
        self.model_name = model_name
        self.is_eval = is_eval
        self.gamma = gamma #gamma is the discount factor. It quantifies how much importance we give for future rewards.
        self.epsilon = epsilon #Exploration and Exploitation — Epsilon (ε)
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.model = load_model("./project/modelsRl/" + model_name) if is_eval else self._model()

    def _model(self):
        model = Sequential()
        model.add(Dense(units=64, input_dim=self.state_size, activation="relu"))
        model.add(Dense(units=32, activation="relu"))
        model.add(Dense(units=8, activation="relu"))
        model.add(Dense(self.action_size, activation="linear"))
        model.compile(loss="mse", optimizer=Adam(lr=0.0001))
        return model

    def act(self, state):
        if not self.is_eval and random.random() <= self.epsilon:
#             print("random action")
            return random.randrange(self.action_size)
#         print("Calculating using model")
#         print(self.model.predict(state))
        options = self.model.predict(state)
#         print(str(options))
        return np.argmax(options[0])
    
    def getPredict(self, state):
        print("Predict using model")
        options = self.model.predict(state)
        print(str(options))
        return np.argmax(options[0])
    
    def getState(self, state):
        return self.model.predict(state)


    def expReplay(self, batch_size):
        mini_batch = []
#         print("expReplay")
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
#             print("For loop")
            target = reward
#             print("target = "+str(target))
#             print("Done = "+str(done))
            if not done:
                # print("Not Done")
                # print("///////////////////////////////////")
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
#             print("target_f")
#             print(target_f)
#             print(target_f[0][action])
            target_f[0][action] = target
#             print(target_f)
            self.model.fit(state, target_f, epochs=1, verbose=0)
#             print("Self model")
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
#         print("Wtf model")

