import sys, os
import time
import datetime
import numpy as np
import sqlite3

from utils.dbmanager import add_run_day_pot, add_run_pot, create_connection, create_table
from beaminfo.simple_query import query_pot_interval
from runinfo.read_run_info import make_timestamp, parse_line

potDir = os.environ["potDir"]
dbname = "%s/dbase/RunSummary.db"%(potDir)
conn = create_connection(dbname)

## Clear and write it again from scatch
ClearTable = False
if ClearTable:
  cur = conn.cursor()
  cur.execute("DELETE FROM run_timestamp;")
  conn.commit()

## Override values
override = True

## Range

start_day = "2020-01-15"
end_day = "2022-11-16"

ts_start_day = make_timestamp( start_day+" 00:00:00 CDT", "%Y-%m-%d %H:%M:%S %Z" )
ts_end_day   = make_timestamp( end_day+" 23:59:59 CDT", "%Y-%m-%d %H:%M:%S %Z" )

## Optional, default 0
StartLine = 0

edges = []
recovers = []
configs = []
underedge = ["NULL",-1,-1]
overedge = ["NULL",-1,-1]

lines = open("%s/temp/DAQInterface_partition1.log"%(potDir)).readlines()

out = open("%s/temp/ParsedDAQInterface.txt"%(potDir),"w")

for i_line in range(StartLine, len(lines)):

  line = lines[i_line].strip('\n')

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

  elif ("STOP transition underway for run" in line):
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

  elif ("RECOVER transition underway" in line):
    dummy, timestamp = parse_line(line)
    if timestamp > ts_start_day and timestamp < ts_end_day: 
       recovers.append(["Recover", timestamp])
    elif timestamp >= ts_end_day: # or timestamp > ts_end_day:
       break

  elif ("CONFIG transition underway" in line):
    dummy, timestamp = parse_line(line)
    nextline = lines[i_line+1].strip('\n')
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
    dt = datetime.datetime.fromtimestamp(TimeStamp)

    edge_next = edges[idx+1]
    Status_next = edge_next[0]
    RunNum_next = edge_next[1] # string
    TimeStamp_next = edge_next[2]
    dt_next = datetime.datetime.fromtimestamp(TimeStamp_next)

    #print("@@@@@@@@@@@@@")
    #print(edge)
    #print(edge_next)

    if RunNum==RunNum_next:
      if Status=="Start" and Status_next=="Stop":
        intervals.append( [RunNum, TimeStamp, TimeStamp_next, ""] )

      elif Status=="Stop" and Status_next=="Start":
        ThisComment = "No run between %s ~ %s"%(dt.strftime("%Y-%m-%d %H:%M:%S"), dt_next.strftime("%Y-%m-%d %H:%M:%S"))
        #print(ThisComment)

    elif int(RunNum)+1==int(RunNum_next):

      if Status=="Start" and Status_next=="Start":
        ThisComment = "Run crashed without clear stop between %s ~ %s"%(dt.strftime("%Y-%m-%d %H:%M:%S"), dt_next.strftime("%Y-%m-%d %H:%M:%S"))
        #print(ThisComment)
        ## Run crashed without clear stop. Look for first recover after start
        for recover in recovers:
          TimeStamp_rec = recover[1]
          dt_rec = datetime.datetime.fromtimestamp(TimeStamp_rec)
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
    dt = datetime.datetime.fromtimestamp(TimeStamp)

    ## The last edge is a run start. Let see if we have a recover after this"
    recFound=False
    for recover in recovers:
      TimeStamp_rec = recover[1]
      dt_rec = datetime.datetime.fromtimestamp(TimeStamp_rec)
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

  t0_str = datetime.datetime.fromtimestamp(t0).strftime("%Y-%m-%d")
  t1_str = datetime.datetime.fromtimestamp(t1).strftime("%Y-%m-%d")

  date_value = t0_str

  runtime_value = t1 - t0

  out.write("%s,%d,%d,\"%s\"\n"%(run_value,t0,t1,Comment))

  ## find config file
  ## config happend before run start
  configFile = "NULL"
  prevEnd = ts_start_day if i_itv==0 else intervals[i_itv-1][2]
  for config in configs:
    TimeStamp_conf = config[1]
    dt_conf = datetime.datetime.fromtimestamp(TimeStamp_conf)
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
    #print("Values for run %s already exists. If you want to update the value, set override=True"%(run_value))
    raise
  conn.commit()

out.close()
