import bitfinex
import pandas as pd
import numpy as np
import datetime
import time
import os
from datetime import timedelta

epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0
    
# Create a function to fetch the data
def fetch_data(start=1364767200000, stop=1545346740000, symbol='btcusd', interval='1m', tick_limit=1000, step=60000000):
    # Create api instance
    api_v2 = bitfinex.bitfinex_v2.api_v2()
    start = start - step
    data = []
    while start < stop:
        start = start + step
        end = start + step
        res = api_v2.candles(symbol=symbol, interval=interval, limit=tick_limit, start=start, end=end)
        data.extend(res)
        print('Retrieving data from {} to {} for {}'.format(pd.to_datetime(start, unit='ms'),
                                                            pd.to_datetime(end, unit='ms'), symbol))
        time.sleep(1.5)
    return data


def calibrate_data(start,path):
    df = pd.read_csv(path)
    times=df["time"]
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    step=timedelta(minutes=5)
    time_format="%Y-%m-%d %H:%M:%S"
    names = ['time', 'open', 'close', 'high', 'low', 'volume']
    for t in times.values:
        current=start.strftime(time_format)
        if current not in df.index:
            print("current is {}, t is {}".format(current,t))
            prev=(start-timedelta(minutes=5)).strftime(time_format)
            new_row=df.loc[prev:prev].values.tolist()
            new_row[0].insert( 0, current)
            dfa=pd.DataFrame(new_row,columns=names)
            dfa.set_index('time', inplace=True)
            frames = [df, dfa]
            df=pd.concat(frames)
        start=start+step  
    df.sort_index(inplace=True)
    df.to_csv(path)
# Define query parameters
bin_size = '5m'
limit = 5000
time_step = 1000*5*60*limit
start=datetime.datetime(2016, 1, 1, 0, 0,0)
t_start=unix_time_millis(start)
t_stop=unix_time_millis( datetime.datetime(2016, 2, 1, 0, 0,0))
#api_v1 = bitfinex.bitfinex_v1.api_v1()
#pairs = api_v1.symbols()
pairs=['btcusd']
save_path = '/mnt/work/bitfinex_data/test'

if os.path.exists(save_path) is False:
    os.mkdir(save_path)

for pair in pairs:
    pair_data = fetch_data(start=t_start, stop=t_stop, symbol=pair, interval=bin_size, tick_limit=limit, step=time_step)

    # Remove error messages
    #ind = [np.ndim(x) != 0 for x in pair_data]
    #pair_data = [i for (i, v) in zip(pair_data, ind) if v]
    #pair_data=[pair_data]

    # Create pandas data frame and clean data
    names = ['time', 'open', 'close', 'high', 'low', 'volume']
    df = pd.DataFrame(pair_data, columns=names)
    df.drop_duplicates(inplace=True)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)

    print('Done downloading data. Saving to .csv.')
    path='{}/bitfinex_{}_{}.csv'.format(save_path, pair,bin_size)
    df.to_csv(path)
    print('calibrating data')
    calibrate_data(start,path)

print('Done retrieving data')
