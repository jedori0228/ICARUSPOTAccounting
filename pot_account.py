import sys
import click
import numpy

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import os, sys
import sqlite3 



from beaminfo.simple_query import query_full_day, query_pot_interval
from utils.dbmanager import add_day_pot_beam, create_connection, create_table, remove_run_day_pot, remove_day_pot_beam, remove_daily_collected_pot
from runinfo.read_run_info import insert_daily_runs, make_timestamp, get_day_range

from plotting.plots_utils import makePOTPlot, makePOTSumPlot, makeDAQEffPlot, makePOTPlotBoth
from plotting.plots_utils import makePOTPlotRun, makePOTSumPlotRun, makeDAQEffPlotRun, makePOTPlotBothRun

USER = os.environ['USER']
potDir = os.environ['potDir']

masterDBName = "RunSummary.db"

sys.path.append(potDir)

#######################################################################################################

@click.group("pot_evaluation")
@click.pass_context
def cli(ctx):
    '''
    POT Evaluation commands

    '''

#######################################################################################################

@cli.command("update-daily-pot")
@click.argument("start_day")
@click.argument("end_day")
@click.argument("override")
@click.pass_context
def update_daily_pot( ctx, start_day="", end_day="", override=False ):
    """
    Update the delivered POT for both beam: 
    Args: 
        start_day : string with the day with the values to update in the format "yyyy-mm-dd"
        end_dat : string with the day with the values to update in the format "yyyy-mm-dd"
        override: delete if a row for that day already exists 
    Returs: 
        None
    """

    print("@@ Connecting to %s/dbase/%s"%(potDir,masterDBName))
    conn = create_connection("%s/dbase/%s"%(potDir,masterDBName))

    if conn is not None:

        print( "Updating the POT delivered between : {} ~ {}".format(start_day,end_day) )

        days = get_day_range(start_day,end_day)
        for day in days:
          if override:
              print( "Remove existing rows with key on: {}".format(day) )

              remove_day_pot_beam(conn, day, "bnb")
              remove_day_pot_beam(conn, day, "numi")
          
          ts_start_day = make_timestamp( day+" 00:00:00 CDT", "%Y-%m-%d %H:%M:%S %Z" )
          ts_end_day   = make_timestamp( day+" 23:59:59 CDT", "%Y-%m-%d %H:%M:%S %Z" )
          add_day_pot_beam( conn, ( day, query_full_day(ts_start_day,ts_end_day, "E:TORTGT", "a9") ), "numi" )
          add_day_pot_beam( conn, ( day, query_full_day(ts_start_day,ts_end_day, "E:TOR875", "1d") ), "bnb")
          
          print(" ALL pot delivered information updated for day {} ".format(day))
         
    else:

      print("FAILED CONNECTION")


#######################################################################################################

@cli.command("update-daily-runs")
@click.argument("start_day")
@click.argument("end_day")
@click.argument("override")
@click.pass_context
def update_daily_runs( ctx, start_day="", end_day="", override=False ):
    """
    Update the collected POT associated to a run for both beam: 
    Args: 
        day: string with the day with the values to update in the format "yyyy-mm-dd"
        override: delete if a row for that day already exists 
    Returs: 
        None
    """

    conn = create_connection("%s/dbase/%s"%(potDir, masterDBName))

    if conn is not None:

        print( "@@ Updating the POT collected between : {} ~ {}".format(start_day,end_day) )

        days = get_day_range(start_day,end_day)
        for day in days:
          if override:
            print( "Remove existing rows with key on: {}".format(day) )
            remove_daily_collected_pot( conn, day )

          insert_daily_runs( conn, day )
        print( "@@ -> ALL pot collected information updated between : {} ~ {}".format(start_day,end_day) )

    else:

        print("FAILED CONNECTION")

#######################################################################################################

@cli.command("make-daq-plots")
@click.pass_context
@click.argument("start_day")
@click.argument("end_day")
def make_daq_plots( ctx, start_day="", end_day="" ):
    """
    Make the daq plots with the new day information
    TODO: select range
    """

    if start_day=="":
        start_day="2021-05-31"
    if end_day=="":
        end_day=today.strftime("%Y-%m-%d")

    time_range = (start_day, end_day)

    print("Potting between {} and {}".format(start_day, end_day) )

    conn = create_connection("%s/dbase/%s"%(potDir, masterDBName))

    if conn is None:
        print("FAILED CONNECTION")
    
    pot_run_collected = pd.read_sql( "SELECT * from daily_collected_pot", conn )
    pot_daily_bnb = pd.read_sql( "SELECT * from day_pot_bnb", conn )
    pot_daily_numi = pd.read_sql( "SELECT * from day_pot_numi", conn )
    
    conn.close()

    # Merge BNB
    pot_run_collected = pot_run_collected.join( pot_daily_bnb.set_index("day"), on="day" ) 
    pot_run_collected.rename( columns={ "pot" : "pot_bnb_delivered"}, inplace=True )
    # Merge Numi
    pot_run_collected = pot_run_collected.join( pot_daily_numi.set_index("day"), on="day" ) 
    pot_run_collected.rename( columns={ "pot" : "pot_numi_delivered"}, inplace=True )

    pot_run_collected["ratio_bnb"] = pot_run_collected["pot_bnb_collected"] / pot_run_collected["pot_bnb_delivered"]
    pot_run_collected["ratio_numi"] = pot_run_collected["pot_numi_collected"] / pot_run_collected["pot_numi_delivered"]

    pot_run_collected = pot_run_collected.sort_values('day')

    ## strip df by time range

    pot_run_collected = pot_run_collected[ pd.to_datetime( pot_run_collected['day'] ) >= pd.to_datetime( start_day ) ]
    pot_run_collected = pot_run_collected[ pd.to_datetime( pot_run_collected['day'] ) <= pd.to_datetime( end_day ) ]

    ## Print final DataGrame

    print(pot_run_collected)

    ## Median

    print("@@ Medians")

    print("pot_bnb_collected = ",  np.median(pot_run_collected["pot_bnb_collected"]) )
    print("pot_numi_collected = ", np.median(pot_run_collected["pot_numi_collected"]) )

    print("pot_bnb_delivered = ",  np.median(pot_run_collected["pot_bnb_delivered"]) )
    print("pot_numi_delivered = ", np.median(pot_run_collected["pot_numi_delivered"]) )

    print("ratio_bnb = ",  np.median(pot_run_collected["ratio_bnb"]) )
    print("ratio_numi = ", np.median(pot_run_collected["ratio_numi"]) )
    print("runtime = ",  np.median(pot_run_collected["runtime"]) )

    ## Sum

    print("@@ Sum")

    print("BNB")
    print("- Delivered = %1.2e POT"%(np.sum(pot_run_collected["pot_bnb_delivered"])*1E12) )
    print("- Collected = %1.2e POT"%(np.sum(pot_run_collected["pot_bnb_collected"])*1E12) )
    print("- Collected/Delivered = %1.3f"%(np.sum(pot_run_collected["pot_bnb_collected"])/np.sum(pot_run_collected["pot_bnb_delivered"])) )
    print("NuMI")
    print("- Delivered = %1.2e POT"%(np.sum(pot_run_collected["pot_numi_delivered"])*1E12) )
    print("- Collected = %1.2e POT"%(np.sum(pot_run_collected["pot_numi_collected"])*1E12) )
    print("- Collected/Delivered = %1.3f"%(np.sum(pot_run_collected["pot_numi_collected"])/np.sum(pot_run_collected["pot_numi_delivered"])) )
    sumRunTime = np.sum(pot_run_collected["runtime"])
    print("Runtime = %d sec"%( int(sumRunTime) ) )
    print("        = %1.1f hrs"%( sumRunTime/3600. ) )
    print("        = %1.1f days"%( sumRunTime/3600./24. ) )

    # MAKE PLOTS, SAVE THEM 
    plt = makePOTPlot(pot_run_collected, "bnb", time_range)
    plt.savefig("fig/eff_pot_bnb.pdf")
    
    plt = makePOTPlot(pot_run_collected, "numi", time_range)
    plt.savefig("fig/eff_pot_numi.pdf")

    plt = makePOTSumPlot( pot_run_collected, "bnb", time_range)
    plt.savefig("fig/cumulative_pot_bnb.pdf")

    plt = makePOTSumPlot( pot_run_collected, "numi", time_range)
    plt.savefig("fig/cumulative_pot_numi.pdf")

    plt = makePOTPlotBoth( pot_run_collected, "numi", "bnb", time_range)
    plt.savefig("fig/cumulative_pot_numi_bnb.pdf")

    plt = makeDAQEffPlot( pot_run_collected, time_range )
    plt.savefig("fig/eff_daq_numi_bnb.pdf")
    plt.show()
    
    return

#######################################################################################################

@cli.command("make-runbyrun-plots")
@click.pass_context
@click.argument("run")

def make_runbyrun_plots( ctx, run=""):
    """
    Make the daq plots with the new day information
    TODO: select range
    """
    conn = create_connection("%s/dbase/run02_beaminfo.db"%(potDir))

    if conn is None:
        print("FAILED CONNECTION")
    
    pot_daily_run=pd.read_sql( "SELECT * from run_day_pot", conn )
    pot_run_=pd.read_sql( "SELECT * from run_pot", conn )

    pot_run.to_csv('dumpbnb.csv')
    conn.close()

    # DB Manipulation
    pot_run_collected = pd.DataFrame(pot_run)
    print(pot_run_collected[1]) 
#    pot_run_collected.columns = [col_name[0] for col_name in pot_run_collected.columns.to_flat_index()]
    

    # Merge BNB
#    pot_run_collected = pot_run_collected.join( pot_daily_bnb.set_index("run"), on="run" ) 
#   pot_run_collected.rename( columns={ "pot" : "pot_bnb_delivered"}, inplace=True )

    

    # Merge Numi
#    pot_run_collected = pot_run_collected.join( pot_daily_numi.set_index("day"), on="day" ) 
#    pot_run_collected.rename( columns={ "pot" : "pot_numi_delivered"}, inplace=True )


#    pot_run_collected["ratio_bnb"] = pot_run_collected["pot_bnb_collected"] / pot_run_collected["pot_bnb_delivered"]
#    pot_run_collected["ratio_numi"] = pot_run_collected["pot_numi_collected"] / pot_run_collected["pot_numi_delivered"]

#    print("pot_bnb_collected = ",  np.median(pot_run_collected["pot_bnb_collected"]))
#    print("pot_numi_collected = ", np.median(pot_run_collected["pot_numi_collected"]))

#    print("pot_bnb_delivered = ",  np.median(pot_run_collected["pot_bnb_delivered"]))
#    print("pot_numi_delivered = ", np.median(pot_run_collected["pot_numi_delivered"]))


#    print("ratio_bnb = ",  np.median(pot_run_collected["ratio_bnb"]))
#    print("ratio_numi = ", np.median(pot_run_collected["ratio_numi"]))
#    print("runtime = ",  np.median(pot_run_collected["runtime"]))


    # MAKE PLOTS, SAVE THEM 
#    plt = makePOTPlotRun(pot_run_collected, "bnb", run)
#    plt.savefig("fig/eff_pot_bnb.pdf")
    
#    plt = makePOTPlotRun(pot_run_collected, "numi", run)
#    plt.savefig("fig/eff_pot_numi.pdf")

#    plt = makePOTSumPlotRun( pot_run_collected, "bnb", run)
#    plt.savefig("fig/cumsum_pot_bnb.pdf")

#    plt = makePOTSumPlotRun( pot_run_collected, "numi", run)
#    plt.savefig("fig/cumsum_pot_numi.pdf")

#    plt = makePOTPlotBothRun( pot_run_collected, "numi", "bnb", run)
#   plt.savefig("fig/cumsum_pot_numi_bnb.pdf")


#    plt = makeDAQEffPlotRun( pot_run_collected, run )
#    plt.savefig("fig/eff_daq_numi_bnb.pdf")
#    plt.show()
    
    return

def main():
    cli(obj=dict())


if '__main__' == __name__:
    main()
