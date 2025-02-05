import bitfinex
import pandas as pd
import numpy as np
import datetime
import time
import os
from datetime import timedelta
import configparser
import logging.config
logging.config.fileConfig("logger.conf")
logger = logging.getLogger("bitfinex")


candle=1
epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0
    
# Create a function to fetch the data
def fetch_data(start=1364767200000, stop=1545346740000, symbol='btcusd', interval='1m', tick_limit=1000, step=60000000):
    # Create api instance
    api_v2 = bitfinex.bitfinex_v2.api_v2()
    #start = start - step
    data = []
    while start < stop:
        if start+step <= stop:
            end= start+step
        else:
            end = stop
        res = api_v2.candles(symbol=symbol, interval=interval, limit=tick_limit, start=start, end=end)
        data.extend(res)
        logger.info('Retrieving data from {} to {} for {}'.format(pd.to_datetime(start, unit='ms'),
                                                            pd.to_datetime(end, unit='ms'), symbol))
        if len(data):
            #logger.info("data is {}".format(data))
            #names = ['time', 'open', 'close', 'high', 'low', 'volume']
            #df = pd.DataFrame(data, columns=names)
            #df.drop_duplicates(inplace=True)
            #df['time'] = pd.to_datetime(df['time'], unit='ms')
            #df.set_index('time', inplace=True)
            #df.sort_index(inplace=True)
            #s=pd.to_datetime(start, unit='ms').strftime("%Y-%m-%d-%H-%M-%S")
            #e=pd.to_datetime(end, unit='ms').strftime("%Y-%m-%d-%H-%M-%S")
            #df.to_csv("/mnt/work/bitfinex_data/slices/{}###{}.csv".format(s,e))
            #number=number+1
            logger.info("data length is {}".format(len(data)))
        else:
            logger.info("data length is zero")
        start=start+step
        logger.info("start is {}, stop is {}".format(start,stop))
        time.sleep(12)
    return data

buffer=[]
def calibrate_data(start,stop,path_new,path_original):
    df = pd.read_csv(path_original)
    times=df["time"]
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    step=timedelta(minutes=candle)
    time_format="%Y-%m-%d %H:%M:%S"
    names = ['time', 'open', 'close', 'high', 'low', 'volume']
    while start <= stop:
        current=(start+timedelta(minutes=candle)).strftime(time_format)
        if current not in df.index:
            print("current is {}".format(current))
            prev=(datetime.datetime.strptime(current,time_format)-timedelta(minutes=candle)).strftime(time_format)
            new_row=df.loc[prev:prev].values.tolist()
            while len(new_row) == 0:
                prev=(datetime.datetime.strptime(prev,time_format)-timedelta(minutes=candle)).strftime(time_format)
                new_row=df.loc[prev:prev].values.tolist()
                print("prev is {}, new_row is {}".format(prev, new_row))
            new_row[0].insert( 0, current)
            buffer=[]
            buffer.extend(new_row)
            dfa=pd.DataFrame(buffer,columns=names)
            dfa.set_index('time', inplace=True)
            frames = [df, dfa]
            df=pd.concat(frames)
            df.sort_index(inplace=True)
            buffer=[]
        start=start+step  
    df.to_csv(path_new)
# Define query parameters
bin_size = '{}m'.format(candle)
limit = 5000
time_step = 1000*candle*60*limit
#Bitfinex最早提供的数据是2013-04-01 00:05:00
start=datetime.datetime(2016, 8, 1, 0, 0,0)
stop=datetime.datetime(2016, 8, 5, 0, 0,0)
t_start=unix_time_millis(start)
t_stop=unix_time_millis(stop)
logger.info("t_start:{}, t_stop:{} , time_step:{}".format(t_start,t_stop,time_step))
#api_v1 = bitfinex.bitfinex_v1.api_v1()
#pairs = api_v1.symbols()
pairs=['btcusd']
save_path = '/mnt/work/bitfinex_data'

if os.path.exists(save_path) is False:
    os.mkdir(save_path)

for pair in pairs:
    pair_data = fetch_data(start=t_start, stop=t_stop, symbol=pair, interval=bin_size, tick_limit=limit, step=time_step)

    # Remove error messages
    ind = [np.ndim(x) != 0 for x in pair_data]
    pair_data = [i for (i, v) in zip(pair_data, ind) if v]

    # Create pandas data frame and clean data
    names = ['time', 'open', 'close', 'high', 'low', 'volume']
    df = pd.DataFrame(pair_data, columns=names)
    df.drop_duplicates(inplace=True)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)

    print('Done downloading data. Saving to .csv.')
    path_original='{}/bitfinex_{}_{}_original.csv'.format(save_path, pair,bin_size)
    path_new='{}/bitfinex_{}_{}_new.csv'.format(save_path, pair,bin_size)
    df.to_csv(path_original)
    print('calibrating data')
    calibrate_data(start,stop,path_new,path_original)

print('Done retrieving data')
