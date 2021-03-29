#!venv/bin/python3

'''
Author:		Massimo Clementi
Created:	2021-03-29

'''

import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

df = pd.read_csv("data_time_series.csv")

'''
 FEATURES THAT CAN BE SELECTED:
	totale_positivi		tamponi
	nuovi_positivi		terapia_intensiva
'''
selected_feature = "nuovi_positivi"


dates = df['data'].values
# pd.to_datetime(dates[0]) + pd.Timedelta(1,'day')
x = np.arange(0,dates.shape[0]).reshape(-1,1)
y = df[[selected_feature]].values.squeeze()

kernel = RBF() + WhiteKernel()
gpr_model = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=50)
print("> GPR training started at", datetime.now())
gpr_model.fit(x,y)
print("              finished at", datetime.now())
#print("    score = ",gpr_model.score(x,y))

print("> Generating plot...")
y_gpr, y_var = gpr_model.predict(x, return_std=True)
plt.figure(figsize=(14,5), dpi=100)
plt.plot(pd.to_datetime(dates),y, marker='x', markersize=3, linewidth=0, label=selected_feature+" - actual data")
plt.plot(pd.to_datetime(dates[:-3]), \
    	 np.convolve(np.pad(y,3,mode='edge'), np.ones(7)/7, mode='valid')[:-3], \
    		alpha=0.5, label=selected_feature+" - 7 days moving average")
#plt.plot(pd.to_datetime(dates), np.convolve(np.pad(y,7,mode='edge'), np.ones(15)/15, mode='valid'), \
#    		alpha=0.5, label=selected_feature+" - 15-days window mean")
plt.plot(pd.to_datetime(dates)[:-15], \
    	 np.convolve(np.pad(y,15,mode='edge'), np.ones(31)/31, mode='valid')[:-15], \
    		alpha=0.5, label=selected_feature+" - 31 days moving average")
plt.plot(pd.to_datetime(dates),y_gpr, color='red', label=selected_feature+" - GPR model")



days_to_predict = 14
x_pred = np.arange(x[-1][0],x[-1][0]+days_to_predict).reshape(-1,1)
y_pred, y_pred_var = gpr_model.predict(x_pred, return_std=True)
x_pred_dates = [pd.to_datetime(dates)[-1] + pd.Timedelta(i,'day') for i in range(0,days_to_predict)]
plt.plot(x_pred_dates, y_pred, ':', color='red', label=selected_feature+" - GPR prediction")
plt.fill_between(
    np.concatenate((dates, x_pred_dates)),
    y1= np.concatenate((y_gpr - 2 * y_var, y_pred - 2 * y_pred_var)),
    y2= np.concatenate((y_gpr + 2 * y_var, y_pred + 2 * y_pred_var)),
    color='green',
    alpha=0.10,
    label='GPR confidence area'
)

plt.legend()
plt.title("Gaussian Process Regression modelling")

plt.gcf().savefig('Figura-4-GPR.pdf')
print("> Saving and opening export folder...")
os.system("open ./")
#plt.show()


