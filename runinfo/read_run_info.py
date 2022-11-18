import sys, os
import time
import datetime
import numpy as np
import pandas as pd

potDir = os.environ['potDir']

from utils.dbmanager import add_run_day_pot, add_run_pot, create_connection

from beaminfo.simple_query import query_pot_interval

def read_reverse_order(file_name):
    # Open file for reading in binary mode
    with open(file_name, 'rb') as read_obj:
        # Move the cursor to the end of the file
        read_obj.seek(0, os.SEEK_END)
        # Get the current position of pointer i.e eof
        pointer_location = read_obj.tell()
        # Create a buffer to keep the last read line
        buffer = bytearray()
        # Loop till pointer reaches the top of the file
        while pointer_location >= 0:
            # Move the file pointer to the location pointed by pointer_location
            read_obj.seek(pointer_location)
            # Shift pointer location by -1
            pointer_location = pointer_location -1
            # read that byte / character
            new_byte = read_obj.read(1)
            # If the read byte is new line character then it means one line is read
            if new_byte == b'\n':
                # Fetch the line from buffer and yield it
                yield buffer.decode()[::-1]
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)
        # As file is read completely, if there is still data in buffer, then its the first line.
        if len(buffer) > 0:
            # Yield the first line too
            yield buffer.decode()[::-1]


def make_timestamp( time_string, string_format="%Y-%b-%d %H:%M:%S %Z" ):

    timestamp=datetime.datetime.strptime(time_string, string_format)
    #print("timestamp",timestamp)
    return int(time.mktime(timestamp.timetuple()))

def get_day_range(start_day, end_day):

  ret = []
  start_day_date = datetime.date.fromisoformat(start_day)
  end_day_date = datetime.date.fromisoformat(end_day)
  delta = datetime.timedelta(days=1)
  while start_day_date <= end_day_date:
    ret.append( start_day_date.strftime("%Y-%m-%d") )
    start_day_date += delta
  return ret


def parse_line( line ):
    # example Thu Jun 30 12:24:37 CDT 2022: STOP transition complete for run 8524

    buff = line.split(": ") #mind the space for correct string parsing
#    date_info = buff[0].split(" ")
#    run_info  = buff[1].split(" ")
    date_info = buff[0].split()
    run_info  = buff[1].split(" ")
    month = date_info[1]
    day   = date_info[2]
    times = date_info[3]
    zone  = date_info[4]
    year  = date_info[5]
    run   = run_info[-1]

    #Form the timestamp 
    day_string = "-".join([ year, month, day ])

    time_string=day_string+" "+times+" "+zone
    #print("date_info",date_info)
    #print("time",time_string)
    return run, make_timestamp(time_string)

def insert_runs( conn ):
    print("insert runs")
    # read the file backwards. Find the timestamp of start and stop of the run
    edges = []
    recovers = []
    prevedge = []

    firstrun=8460
    for line in read_reverse_order("temp/DAQInterface_partition1.log"):
#        print("in for cycle")
        if "START transition complete for run" in line:

            run, timestamp = parse_line(line)
            print("reading start", line)
            print("start timestamp", run, timestamp)

            if int(run) >= firstrun:
                print('appeding start',run, timestamp)
                edges.append(["Start", run, timestamp])
            else:
                break
        if ("STOP transition underway for run" in line):

            run, timestamp = parse_line(line)
            print("reading stop", line)
#            print("stop timestamp", run, timestamp)
#            print("day start", run, ts_start_day)
#            print("day end", run, ts_end_day)
            
            if int(run) >= firstrun:
                print('appeding stop',run, timestamp)
                edges.append(["Stop", run, timestamp])
            else:
                break
        if ("RECOVER transition underway" in line):

            dummy, timestamp = parse_line(line)
            print("reading recover", line)

#            print("day start", run, ts_start_day)
#            print("day end", run, ts_end_day)
#            if timestamp > ts_start_day and timestamp < ts_end_day: 
#                edges.append(["Stop", run, timestamp])
#            elif timestamp < ts_start_day:
#                break
           
            if int(run) >= firstrun:
                print("appending recover timestamp", timestamp)
                recovers.append(["Recover", timestamp])
            else:
                break

    print("before sorting edges")
    edges = sorted(edges, key=lambda x: -x[2]) 
    print("before sorting edges",len(edges))
    # now transform the edges in intervals 
    intervals = []
    
    if len(edges) > 0:
        print("in edges loop",len(edges))
        # Assumes that a start is followed by a stop and
        #  a stop is followed by a start ( too string ? )
        #
#        print('inter0',intervals[0])
        for idx, edge in enumerate(edges[1:]):
            idx = idx+1
            print('idx',idx)
            print('edge',edge,'later edge',edges[idx-1])
            if edge[0] == 'Start' and edges[idx-1][0] == 'Stop':
                intervals.append( [edge[1], edge[2], edges[idx-1][2]] )
                print('appending',edge[1],edge[2],edges[idx-1][2])
            elif edge[0] == 'Stop' and edges[idx-1][0] == 'Start':
                print("run stopped between",edge[2],edges[idx-1][2])
            elif edge[0] == 'Stop' and edges[idx-1][0] == 'Stop':
                # do nothing
                print( 'Stop followed by a stop' )
            elif edge[0] == 'Start' and edges[idx-1][0] == 'Start':
                # Run crashed without clear stop. Look for first recover after start
                print('double start')
                for irec,recover in enumerate(recovers):
                    rectime=recovers[irec][1]
                    edgetime0=edge[2]
                    edgetime1=edges[idx-1][2]
                    print('edge before',edgetime0,'edge after',edgetime1)
                    print('rectime',rectime)
                    if rectime > edgetime0 and rectime < edgetime1 :
                        if intervals[len(intervals)-1][1] == edgetime0:
                            intervals[len(intervals)-1][2]=rectime
                        else:
                            #print('intervals len',len(intervals))
                            if len(intervals):
                                dum=len(intervals)-1
                                print('dum',dum)
                                recrun=int(intervals[dum][0])-1
                                intervals.append( [recrun, edgetime0, rectime ] )
                            else:
                                intervals.append( [0, edgetime0, rectime ] )

    print('recovers',len(recovers),'edges',len(edges))

#it's possible the last of the day crashed without a clean STOP. 
#We look for recovers that are later than any start/stop. 
#If there are any, we shorten the last run having it stopped at RECOVER instead of midnight 
    if len(edges) > 0 and len(recovers) > 0:
        print('last recover time',recovers[0][1],'edge', edges[0][2])
    if(len(recovers)):
        if recovers[0][1] > edges[0][2]:
            intervals[0][2]=recovers[0][1]

    if len(edges)==0 and len(recovers)==0 :
        # If we didn't find any edge or recover it means that the run never stopped during the day
        # we just query between the beginning and the end of the day 
        intervals.append( [ 0, ts_start_day, ts_end_day] )
        print('no edges, no recovers')

    total_runtime=0
    print('intervals',len(intervals))
    for interval in intervals:
       

        run_value = int(interval[0])

        t0 = interval[1]

        t1 = interval[2]

        runtime_value = t1 - t0
 
        total_runtime=total_runtime+runtime_value
        print("run",run_value,"t1",t1,"t0",t0,"runtime",runtime_value)
        pot_bnb_value =  float( query_pot_interval(t0, t1, "E:TOR875", "1d") )
        print('bnb',pot_bnb_value)
        pot_numi_value =  float( query_pot_interval(t0, t1, "E:TORTGT", "a9") )
        print('numi',pot_numi_value)
        add_row = (run_value, runtime_value, pot_bnb_value, pot_numi_value, "majority")
        print('prova')
        add_run_pot(conn, add_row )
        
        update_delivered_pot(conn, run_value, t0, t1)

    print('total runtime',total_runtime)
    # REMOVE the DAQInterface_partition1 log file from the temp folder        
#    os.system( "rm temp/DAQInterface_partition1.log" )

def update_delivered_pot( conn, run, start, end, override=False ):
    """
    Update the delivered POT for both beam: 
    Args: 
        run: string with the run
        override: delete if a row for that day already exists 
    Returs: 
        None
    """

    if conn is not None:

        print( "Updating the POT delivered on: {}")

        if override:

            print( "Remove existing rows with key on: {}" )

            remove_run_pot_beam(conn, run, "bnb")
            remove_run_pot_beam(conn, run, "numi")
        
 
        add_run_pot_beam( conn, ( day, query_pot_interval(start,end, "E:TORTGT", "a9") ), "numi" )
        add_run_pot_beam( conn, ( day, query_pot_interval(start,end, "E:TOR875", "1d") ), "bnb")
        
        print(" ALL pot delivered information updated for day {} ")
       
    else:

        print("FAILED CONNECTION")

def insert_daily_runs( conn, day_string ):

    # Use the day_string to get the UNIX timestamps of the start-end of the day
    ts_start_day = make_timestamp( day_string+" 00:00:00 CDT", "%Y-%m-%d %H:%M:%S %Z" )
    ts_end_day   = make_timestamp( day_string+" 23:59:59 CDT", "%Y-%m-%d %H:%M:%S %Z" )

    ## Run timestamp db

    dbname = "%s/dbase/RunSummary.db"%(potDir)
    conn_rts = create_connection(dbname)
    if conn_rts is None:
        print("FAILED CONNECTION to %s"%(dbname))

    print("@@ Day: %s"%(day_string))
    print("@@ ts_start_day = %d"%(ts_start_day))
    print("@@ ts_end_day = %d"%(ts_end_day))

    ToMergedDF = []

    run_prev = pd.read_sql( "SELECT * FROM run_timestamp WHERE (start<%d) AND (stop>=%d)"%(ts_start_day,ts_start_day), conn_rts )
    if run_prev.shape[0]>0:
      print("@@ Run prev")
      print(run_prev)
      run_prev.at[0,"start"] = ts_start_day
      if run_prev.at[0,"stop"]>=ts_end_day:
        run_prev.at[0,"stop"] = ts_end_day
      ToMergedDF.append(run_prev)

    run_contained = pd.read_sql( "SELECT * FROM run_timestamp WHERE (start>=%d) AND (stop<=%d)"%(ts_start_day,ts_end_day), conn_rts )
    if run_contained.shape[0]>0:
      print("@@ Run contained")
      print(run_contained)
      ToMergedDF.append(run_contained)

    run_continued = pd.read_sql( "SELECT * FROM run_timestamp WHERE (start BETWEEN %d AND %d) AND (stop>=%d)"%(ts_start_day,ts_end_day,ts_end_day), conn_rts )
    if run_continued.shape[0]>0:
      print("@@ Run continued")
      print(run_continued)
      run_continued.at[0,"stop"] = ts_end_day
      ToMergedDF.append(run_continued)

    conn_rts.close()

    if len(ToMergedDF)==0:
      return

    df_merged = pd.concat(ToMergedDF, ignore_index=True)
    print("@@ Final intervals")
    print(df_merged)

    sum_pot_bnb_value = 0.
    sum_pot_numi_value = 0.
    sum_runtime = 0.

    for i in range(0,df_merged.shape[0]):
      run = df_merged.at[i,"run"]
      start = df_merged.at[i,"start"]
      stop = df_merged.at[i,"stop"]

      pot_bnb_value =  float( query_pot_interval(start, stop, "E:TOR875", "1d") )
      pot_numi_value = float( query_pot_interval(start, stop, "E:TORTGT", "a9") )
      runtime = stop-start

      sum_pot_bnb_value += pot_bnb_value
      sum_pot_numi_value += pot_numi_value
      sum_runtime += runtime

      #print(run,start,stop,pot_bnb_value,pot_numi_value)

    print(day_string, sum_pot_bnb_value, sum_pot_numi_value, sum_runtime)

    sql = "INSERT INTO daily_collected_pot(day, pot_bnb_collected, pot_numi_collected, runtime) VALUES(?,?,?,?)"
    add_row = (day_string, sum_pot_bnb_value, sum_pot_numi_value, sum_runtime)

    cur = conn.cursor()
    cur.execute(sql, add_row)
    conn.commit()


    #print('total runtime',total_runtime)
    #REMOVE the DAQInterface_partition1 log file from the temp folder        
    #os.system( "rm temp/DAQInterface_partition1.log" )

