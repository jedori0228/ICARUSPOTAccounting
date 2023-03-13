import sys, os
import time
import datetime
import pytz
import numpy as np
import pandas as pd

from utils.dbmanager import add_run_day_pot, add_run_pot, create_connection, create_table
from beaminfo.simple_query import query_pot_interval
from runinfo.read_run_info import make_timestamp, parse_line

tz_CDT = pytz.timezone("America/Chicago")

potDir = os.environ["potDir"]
dbname = "%s/dbase/RunSummary.db"%(potDir)
conn = create_connection(dbname)

runStart = 9610
runEnd = 999999

sqlcmd = 'SELECT * FROM run_timestamp WHERE (run>=%d AND run<=%d)'%(runStart, runEnd)

df = pd.read_sql(sqlcmd, conn)
conn.close()

df['hrs'] = (df['stop']-df['start'])/3600.

#df['start'] = df['start'].map(lambda ts : datetime.datetime.strftime( datetime.datetime.fromtimestamp(ts, tz_CDT), "%Y-%m-%d %H:%M:%S") )
#df['stop'] = df['stop'].map(lambda ts : datetime.datetime.strftime( datetime.datetime.fromtimestamp(ts, tz_CDT), "%Y-%m-%d %H:%M:%S") )

df['start'] = df['start'].map(lambda ts : datetime.datetime.strftime( datetime.datetime.fromtimestamp(ts, tz_CDT), "%m/%d/%Y %H:%M") )
df['stop'] = df['stop'].map(lambda ts : datetime.datetime.strftime( datetime.datetime.fromtimestamp(ts, tz_CDT), "%m/%d/%Y %H:%M") )

#df.drop('conf',inplace=True ,axis=1)
#df = df[['run', 'start', 'stop', 'hrs', 'comment']]
#df = df[['run', 'start', 'stop', 'hrs', 'conf']]
df = df[['run', 'start', 'stop', 'conf']]

#df.sort_values(by=['hrs'], inplace=True, ascending=False)

print(df.to_string())
