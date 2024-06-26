import sys, os
import time
import datetime
import numpy as np
import sqlite3
import argparse
import pytz

from utils.dbmanager import add_run_day_pot, add_run_pot, create_connection, create_table
from beaminfo.simple_query import query_pot_interval
from runinfo.read_run_info import make_timestamp, parse_line

## Arguments

parser = argparse.ArgumentParser(description='Parsing DAQLog')
parser.add_argument('-i', dest="Start")
parser.add_argument('-f', dest="End")
args = parser.parse_args()

print("[ParseDAQLog.py] Request range")
print("[ParseDAQLog.py] - Start:", args.Start)
print("[ParseDAQLog.py] - End:", args.End )

potDir = os.environ["potDir"]
dbname = "%s/dbase/RunSummary.db"%(potDir)
conn = create_connection(dbname)

## Check if there's any "RUNNING" state
sql_RunningStateCheck = 'select * from run_timestamp WHERE comment="RUNNING";'
cur = conn.cursor()
cur.execute(sql_RunningStateCheck)
RunningStateCheckOutput = cur.fetchall()
if len(RunningStateCheckOutput)>0:
  for line in RunningStateCheckOutput:
    #ex) (9294, 1671406288, 1671602399, 'Physics_General_thr400_Majority_5_7_nb_OverlappingWindow_00001', 'RUNNING')
    runNum = line[0]
    startTS = line[1]
    endTS = line[2]

    startDT_utc = datetime.datetime.fromtimestamp(startTS, datetime.timezone.utc)
    endDT_utc = datetime.datetime.fromtimestamp(endTS, datetime.timezone.utc)

    startDT_fnal = startDT_utc.astimezone(pytz.timezone('America/Chicago'))
    endDT_fnal = endDT_utc.astimezone(pytz.timezone('America/Chicago'))

    ## If this run is behind args.Start, replace args.Start to this run
    ## If not, e.g., we don't have to
    start_day = args.Start
    ts_start_day = make_timestamp( start_day+" 00:00:00 CDT", "%Y-%m-%d %H:%M:%S %Z" )

    if startDT_utc.timestamp() < ts_start_day:

      print("[ParseDAQLog.py] Run %d was in RUNNING state (%s ~ %s),"%(runNum, startDT_fnal.strftime("%Y-%m-%d %H:%M:%S %Z"), endDT_fnal.strftime("%Y-%m-%d %H:%M:%S %Z")))
      print("[ParseDAQLog.py] so we need to check how this run ended.")
      startDate_fnal = startDT_fnal.date().isoformat()
      print("[ParseDAQLog.py] -> Setting Start date to %s"%(startDate_fnal))
      args.Start = startDate_fnal
      break
    else:
      break

## Check the last run from current database
sql_DBLastRunStart = '''SELECT run, start
FROM run_timestamp
WHERE run = (SELECT MAX(run) FROM run_timestamp);'''
cur.execute(sql_DBLastRunStart)
DBLastRunStartOutput = cur.fetchall()
DBLastRunStartTimpstamp = DBLastRunStartOutput[0][1]
DBLastRunStartDatetime = datetime.datetime.fromtimestamp( DBLastRunStartTimpstamp, datetime.timezone.utc )

print("[ParseDAQLog.py] Last run from the current databse")
print("[ParseDAQLog.py] - Run:", DBLastRunStartOutput[0][0])
print("[ParseDAQLog.py] - Start:", DBLastRunStartDatetime.strftime("%Y-%m-%d %H:%M:%S %Z"))

## Clear and write it again from scatch
ClearTable = False
if ClearTable:
  cur = conn.cursor()
  cur.execute("DELETE FROM run_timestamp;")
  conn.commit()

## Override the values?
override = True

## Range

start_day = args.Start
end_day = args.End

ts_start_day = make_timestamp( start_day+" 00:00:00 CDT", "%Y-%m-%d %H:%M:%S %Z" )
ts_end_day   = make_timestamp( end_day+" 23:59:59 CDT", "%Y-%m-%d %H:%M:%S %Z" )

## Optional, default 0
StartLine = 0

edges = []
recovers = []
configs = []
underedge = ["NULL",-1,-1]
overedge = ["NULL",-1,-1]

daglogfilepath = "%s/temp/DAQInterface_partition1.log"%(potDir)
daqlog_lines = open(daglogfilepath).readlines()

out = open("%s/temp/ParsedDAQInterface.txt"%(potDir),"w")

## Quickly check the last timestamp 
for j_line in range(StartLine, len(daqlog_lines)):

  i_line = len(daqlog_lines) - 1 - j_line

  line = daqlog_lines[i_line].strip('\n')
  if len(line.split())>0:
    if line.split()[0] not in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
      continue

  IsParsibleLine = False
  for known_line in ["START transition complete for run", "STOP transition underway for run", "RECOVER transition underway", 'DAQInterface in partition 1 launched and now in "stopped" state', "CONFIG transition underway"]:
    if known_line in line:
      IsParsibleLine = True
      break;
  if not IsParsibleLine:
    continue

  LogLastRun, LogLastTimestamp = parse_line(line)
  LogLastDatetime = datetime.datetime.fromtimestamp( LogLastTimestamp, datetime.timezone.utc )

  print("[ParseDAQLog.py] DAQ log file to be parsed %s"%(daglogfilepath))
  print("[ParseDAQLog.py] - Current log file has last timestamp at:", LogLastDatetime.strftime("%Y-%m-%d %H:%M:%S %Z") )

  if ts_start_day>LogLastTimestamp:
    print("[ParseDAQLog.py] * Requested start time was", start_day, "but the current log file might not be the latest. You might want to copy the latest logfile.")
  break

## Now loop over logfiles and collect edges
for i_line in range(StartLine, len(daqlog_lines)):

  line = daqlog_lines[i_line].strip('\n')

  if len(line.split())>0:
    if line.split()[0] not in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
      continue

  if "START transition complete for run" in line:
    run, timestamp = parse_line(line)
    #print("[DEBUG][insert_multi_daily_runs] Start found")
    if timestamp > ts_start_day and timestamp < ts_end_day: 
      #print("[DEBUG][insert_multi_daily_runs] -> In time")
      LinesInTheRange = True
      edges.append(["Start", run, timestamp])
    elif timestamp <= ts_start_day:
      #print("[DEBUG][insert_multi_daily_runs] -> Updating previous edge")
      underedge = ["Start", run, timestamp]
    elif timestamp >= ts_end_day:
      #print("[DEBUG][insert_multi_daily_runs] -> Updating next edge")
      overedge = ["Start", run, timestamp]
      break

  elif "STOP transition underway for run" in line:
    run, timestamp = parse_line(line)
    #print("[DEBUG][insert_multi_daily_runs] Stop found")
    if timestamp > ts_start_day and timestamp < ts_end_day: 
      #print("[DEBUG][insert_multi_daily_runs] -> In time")
      edges.append(["Stop", run, timestamp])
    elif timestamp <= ts_start_day:
      #print("[DEBUG][insert_multi_daily_runs] -> Updating previous edge")
      underedge = ["Stop", run, timestamp]
    elif timestamp >= ts_end_day:
      #print("[DEBUG][insert_multi_daily_runs] -> Updating next edge")
      overedge = ["Stop", run, timestamp]
      break

  elif ("RECOVER transition underway" in line) or  ('DAQInterface in partition 1 launched and now in "stopped" state' in line):
    dummy, timestamp = parse_line(line)
    if timestamp > ts_start_day and timestamp < ts_end_day: 
       recovers.append(["Recover", timestamp])
    elif timestamp >= ts_end_day: # or timestamp > ts_end_day:
       break

  elif ("CONFIG transition underway" in line):
    dummy, timestamp = parse_line(line)
    nextline = daqlog_lines[i_line+1].strip('\n')
    configFile = "NULL"
    if "Config name: " in nextline:
      configFile = nextline.replace('Config name: ','')
    configs.append([configFile, timestamp])

  else:
    continue

# now transform the edges in intervals 
intervals = []

if len(edges) > 0:

  for idx in range(0,len(edges)-1):

    edge = edges[idx]
    Status = edge[0]
    RunNum = edge[1] # string
    TimeStamp = edge[2]
    dt = datetime.datetime.fromtimestamp(TimeStamp, datetime.timezone.utc)

    edge_next = edges[idx+1]
    Status_next = edge_next[0]
    RunNum_next = edge_next[1] # string
    TimeStamp_next = edge_next[2]
    dt_next = datetime.datetime.fromtimestamp(TimeStamp_next, datetime.timezone.utc)

    #print("@@@@@@@@@@@@@")
    #print(edge)
    #print(edge_next)

    if RunNum==RunNum_next:
      if Status=="Start" and Status_next=="Stop":
        intervals.append( [RunNum, TimeStamp, TimeStamp_next, ""] )

      elif Status=="Stop" and Status_next=="Start":
        ThisComment = "No run between %s ~ %s"%(dt.strftime("%Y-%m-%d %H:%M:%S"), dt_next.strftime("%Y-%m-%d %H:%M:%S"))
        #print(ThisComment)

    #elif int(RunNum)+1==int(RunNum_next):
    elif int(RunNum)<int(RunNum_next):

      if Status=="Start" and Status_next=="Start":
        ThisComment = "Run crashed without clear stop between %s ~ %s"%(dt.strftime("%Y-%m-%d %H:%M:%S"), dt_next.strftime("%Y-%m-%d %H:%M:%S"))
        #print(ThisComment)
        ## Run crashed without clear stop. Look for first recover after start
        for recover in recovers:
          TimeStamp_rec = recover[1]
          dt_rec = datetime.datetime.fromtimestamp(TimeStamp_rec, datetime.timezone.utc)
          if TimeStamp < TimeStamp_rec and TimeStamp_rec < TimeStamp_next:
            intervals.append( [RunNum, TimeStamp, TimeStamp_rec, "CRASH"] )
            break

    else:

      if Status=="Stop" and Status_next=="Stop":
        ThisComment = "Stop followed by stop between %s ~ %s"%(dt.strftime("%Y-%m-%d %H:%M:%S"), dt_next.strftime("%Y-%m-%d %H:%M:%S"))
        #print(ThisComment)

  if edges[-1][0]=="Start":

    edge = edges[-1]
    Status = edge[0]
    RunNum = edge[1] # string
    TimeStamp = edge[2]
    dt = datetime.datetime.fromtimestamp(TimeStamp, datetime.timezone.utc)

    ## The last edge is a run start. Let see if we have a recover after this"
    recFound=False
    for recover in recovers:
      TimeStamp_rec = recover[1]
      dt_rec = datetime.datetime.fromtimestamp(TimeStamp_rec, datetime.timezone.utc)
      if TimeStamp < TimeStamp_rec and TimeStamp_rec < ts_end_day:
        ## This run crashed before the end of the DAQ log
        recFound = True
        intervals.append( [RunNum, TimeStamp, TimeStamp_rec, "CRASH"] )
        break
    if not recFound:
      ## This run is still running by the time the log file ended
      intervals.append( [RunNum, TimeStamp, ts_end_day, "RUNNING"] )

for i_itv in range(0,len(intervals)):

  interval = intervals[i_itv]

  run_value = interval[0]
  t0 = interval[1]
  t1 = interval[2]
  Comment = interval[3]

  t0_str = datetime.datetime.fromtimestamp(t0, datetime.timezone.utc).strftime("%Y-%m-%d")
  t1_str = datetime.datetime.fromtimestamp(t1, datetime.timezone.utc).strftime("%Y-%m-%d")

  date_value = t0_str

  runtime_value = t1 - t0

  out.write("%s,%d,%d,\"%s\"\n"%(run_value,t0,t1,Comment))

  ## find config file
  ## config happens before the run start
  configFile = "NULL"
  prevEnd = ts_start_day if i_itv==0 else intervals[i_itv-1][2]
  for config in configs:
    TimeStamp_conf = config[1]
    dt_conf = datetime.datetime.fromtimestamp(TimeStamp_conf, datetime.timezone.utc)
    if prevEnd < TimeStamp_conf and TimeStamp_conf < t0:
      configFile = config[0]

  if override:
    #print("Overriding run %s"%(run_value))
    deldql = "DELETE FROM run_timestamp WHERE run=%s"%(run_value)
    cur = conn.cursor()
    cur.execute(deldql)
    conn.commit()

  sql = "INSERT INTO run_timestamp(run, start, stop, conf, comment) VALUES(?,?,?,?,?)"
  row_insert = (int(run_value), t0, t1, configFile, Comment)

  cur = conn.cursor()
  ## if the comment in the currnet db is "RUNNING", we need to update this
  cur.execute('DELETE FROM run_timestamp WHERE (run=%s AND comment="RUNNING")'%(run_value))
  try:
    #print(row_insert)
    cur.execute(sql, row_insert)
  except sqlite3.IntegrityError:
    print("Values for run %s already exists. If you want to update the value, set override=True"%(run_value))
    raise
  conn.commit()

out.close()
