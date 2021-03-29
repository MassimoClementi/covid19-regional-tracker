#!venv/bin/python3


# # COVID-19 Regional Tracker
# Author: Massimo Clementi | Date: 1 April 2020


import argparse
import os
import pandas as pd
import urllib.request
import ssl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

import numpy as np
from numpy import errstate


parser = argparse.ArgumentParser(description='COVID-19 Regional Temporal Analysis by Massimo Clementi')
parser.add_argument('nome_provincia', type=str, help='name of the province to extract the data from')
parser.add_argument('last_year', type=int, help='year of the latest available data')
parser.add_argument('last_month', type=int, help='month of the latest available data')
parser.add_argument('last_day', type=int, help='day of the latest available data')
parsed_values = parser.parse_args()



def formatted_date(yyyy,mm,dd):
    
    year = str(yyyy)
    month = str(mm)
    day = str(dd)
    
    year = year.zfill(4)
    month = month.zfill(2)
    day = day.zfill(2)
    
    return year + month + day



def url_string(it):
    """
    Get the full url used to dowload the data of the given date
    """
    
    b_link ="https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-"
       
    return b_link + it + ".csv"



def get_date_iterators(yyyy,mm,dd):
    """
    Return iterator over a date range
    """
    
    start_date = formatted_date(2020,2,25)  # <-- date of oldest available data
    end_date = formatted_date(yyyy,mm,dd)
    
    pd_it = pd.date_range(start_date,end_date,freq='D')
    
    it = []
    
    for el in pd_it:
        it.append(formatted_date(el.year,el.month,el.day))
        
    return it



nome_provincia = parsed_values.nome_provincia

daily_cvs_folder = os.path.join(os.getcwd(),"daily-data")
if os.path.exists(daily_cvs_folder) is not True:
    os.mkdir(daily_cvs_folder)

ssl._create_default_https_context = ssl._create_unverified_context
data_time_series = list()



''' Get all data available till date specified '''
print("> Reading all the data files until " + str(parsed_values.last_year) + "-" + str(parsed_values.last_month) + "-" + \
      str(parsed_values.last_day) + ", please wait...")
for date in get_date_iterators(parsed_values.last_year, parsed_values.last_month, parsed_values.last_day):
    
    full_string = url_string(date)
    name = full_string[-36:]
    file_path = os.path.join(daily_cvs_folder,name)
    
    ''' If data is not present in data folder, download from GitHub repo and save it '''
    if os.path.isfile(file_path) is not True:
        
        try:
            print("Getting",name,"...", end='')
            req = urllib.request.urlretrieve(full_string)
            print(" done!")
            df = pd.read_csv(req[0])
            df.to_csv(file_path)
        except:
            print("\n [ERROR]",name,"is NOT AVAILABLE for download!","\nQuitting now...")
            quit()
        
    else:
        
        df = pd.read_csv(file_path)
    
    ''' Extract only data for the specified region and accumulate data over time'''
    df = df[df.denominazione_regione == nome_provincia]
    data_time_series.append([df["data"].values[0], \
                             int(df["totale_positivi"]), \
                             int(df["tamponi"]), \
                             int(df["nuovi_positivi"]), \
                             int(df["dimessi_guariti"]), \
                             int(df["deceduti"]), \
                             int(df["isolamento_domiciliare"]), \
                             int(df["ricoverati_con_sintomi"]), \
                             int(df["terapia_intensiva"])])



''' Create dataframe of the time series and then export it '''
df = pd.DataFrame(data=data_time_series, \
                  columns=['data', 'totale_positivi', 'tamponi', 'nuovi_positivi', \
                           'dimessi_guariti', 'deceduti', 'isolamento_domiciliare', \
                           'ricoverati_con_sintomi', 'terapia_intensiva'])
df.to_csv('data_time_series.csv', date_format='%s')

print("> Completed!")

df = pd.read_csv('data_time_series.csv', parse_dates=[0], infer_datetime_format=True)


nuovi_positivi_7_giorni = np.sum(df['nuovi_positivi'][-7:])
print(" new positives over last 7 days:",nuovi_positivi_7_giorni)
if nome_provincia == "P.A. Trento":
    print("  (approx over 100.000 for PAT): {v:.0f}".format(v=nuovi_positivi_7_giorni/5.5))

nuovi_tamponi = np.zeros(len(df['tamponi']))
for i in range(1, len(nuovi_tamponi)):
    nuovi_tamponi[i] = df['tamponi'].values[i] - df['tamponi'].values[i-1]
nuovi_tamponi[0] = 0
#print(nuovi_tamponi[-1])

print("> Now plotting and exporting... ", end='')

''' Plot1 '''
fig1,ax1 = plt.subplots()
ax1_2 = ax1.twinx()
ax1.bar(pd.to_datetime(df["data"]),df["nuovi_positivi"], \
         color='tab:orange', alpha=1, label='Nuovi positivi')
ax1.plot(pd.to_datetime(df["data"]),nuovi_tamponi/30, \
         marker='s',color='tab:red', linewidth=0.7, markersize = 0.5, label='Tamponi /50')
with errstate(divide='ignore'):     # do not print warnings about division by zero, just works for now
    ax1_2.plot(pd.to_datetime(df["data"]), 10*np.log10(df["nuovi_positivi"]/nuovi_tamponi), \
             marker='o',color='black', linewidth=0.7, markersize = 0.5, label='Giornaliero')
    ax1_2.plot(pd.to_datetime(df["data"]), 10*np.log10(df["totale_positivi"]/df["tamponi"]), \
             marker=None,color='tab:purple',markersize = 2.0, label='Cumulativo')
    #ax1_2.plot(pd.to_datetime(df["data"]),10*np.log10(nuovi_tamponi), \
    #         marker=None,color='grey',markersize = 1.0, label='Tamponi')

ax1_2.set_xlabel('Data')
ax1_2.set_ylabel('Numero positivi / tamponi [dB]')
ax1.set_ylabel('Valore', color='tab:orange')
ax1.tick_params(axis='y', colors='tab:orange')
if nome_provincia == "P.A. Trento":
    ax1_2.set_title("Evoluzione per " + nome_provincia + " (inc. {v:.0f})".format(v=nuovi_positivi_7_giorni/5.5))
else:
    ax1_2.set_title("Evoluzione per " + nome_provincia)
ax1_2.legend()
ax1.legend()
ax1_2.grid(True)
ax1_2.xaxis.set_major_locator(mdates.MonthLocator(interval = 2))
ax1_2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    

''' Plot2 '''
fig2,ax2 = plt.subplots()
ax2_1 = ax2.twinx()
ax2.bar(pd.to_datetime(df["data"]),df["totale_positivi"], \
        color='tab:red', alpha=1)
with errstate(divide='ignore'):
    #ax2_1.plot(pd.to_datetime(df["data"]),20*np.log10(df["dimessi_guariti"]), \
    #         marker="o",color='green',markersize = 2.0)
    #ax2_1.plot(pd.to_datetime(df["data"]),20*np.log10(df["deceduti"]), \
    #         marker="o",color='blue',markersize = 2.0)
    #ax2_1.bar(pd.to_datetime(df["data"]),np.maximum(np.gradient(df["dimessi_guariti"]),0), \
    #        color='green')
    #ax2_1.bar(pd.to_datetime(df["data"]),np.maximum(np.gradient(df["deceduti"]),0), \
    #        color='blue')
    ax2_1.plot(pd.to_datetime(df["data"]), \
            10*np.log10(np.maximum(np.gradient(df["deceduti"]),0) / np.maximum(np.gradient(df["dimessi_guariti"]),0.1)), \
            marker='s', color='black', linewidth=0.7, markersize = 0.5)
    
ax2.set_xlabel('Data')
ax2.set_ylabel('Totale positivi', color='tab:red')
ax2_1.set_ylabel('Trend giornaliero deceduti / dimessi [dB]')
ax2.tick_params(axis='y', colors='tab:red')
ax2_1.tick_params(axis='y', colors='black')
ax2.set_title("Evoluzione per " + nome_provincia)
#ax2_1.legend(("Guariti","Decessi"))
ax2.grid(True)
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval = 2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))


    
''' Plot 3 '''
fig3,ax3 = plt.subplots()
ax3_1 = ax3.twinx()
ax3.bar(pd.to_datetime(df["data"]),df["terapia_intensiva"], \
        color='tab:red', alpha=1)
ax3.bar(pd.to_datetime(df["data"]),df["ricoverati_con_sintomi"], \
        color='tab:blue', bottom=df["terapia_intensiva"], alpha=1)
ax3_1.plot(pd.to_datetime(df["data"]),df["isolamento_domiciliare"], \
         marker="s",color='black', linewidth=0.7, markersize = 0.5)

ax3_1.set_xlabel('Data')
ax3_1.set_ylabel('Numero persone in isolamento domiciliare')
ax3_1.set_title("Evoluzione per " + nome_provincia)
ax3.legend(("Terapia intensiva", "Ricoverati con sintomi"))
ax3.grid(True)
ax3_1.xaxis.set_major_locator(mdates.MonthLocator(interval = 2))
ax3_1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))



''' Export plots while preserving transparency '''
fig1.savefig("Figura-1-Casi-su-tampone-e-nuovi-positivi.pdf")
fig2.savefig("Figura-2-Positivi-guariti-decessi.pdf")
fig3.savefig("Figura-3-Ospedalizzati-e-ricoverati.pdf")

print("done!")

#print("> Opening export folder...")
#os.system("open ./")

#plt.show()

