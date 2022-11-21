import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import pandas as pd
import numpy as np

from matplotlib.gridspec import GridSpec

from statistics import mode 

def makePOTPlot( df, beam, range ):

    fig=plt.figure( figsize=(15,5) )

    gs=GridSpec(2,1, height_ratios=[6, 2]) 

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column
    
    ax0.set_title(beam, fontsize=18)

    #ax0.axis("off")
    ax0.spines["right"].set_visible(False)
    ax0.spines["left"].set_visible(False)
    ax0.spines["top"].set_visible(False)

    ax0.yaxis.grid( linestyle='-' )
    
    del_label="pot_%s_delivered" % beam
    
    x=pd.to_datetime( df["day"], utc=True )
    y=df[del_label]/1000000
    ax0.fill_between(x, y, step="mid", alpha=0.2)
    ax0.step( x, y, drawstyle="steps", where='mid', linewidth=2.0, label="Delivered" )
    
    col_label="pot_%s_collected" % beam
    
    y=df[col_label]/1000000
    ax0.fill_between(x, y, step="mid", alpha=0.4)
    ax0.step( x, y, drawstyle="steps", where='mid', linewidth=2.0,label="Collected" )

    ax0.set_ylabel( "$10^{18}$ POT/day", fontsize=16 )

    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Y'))

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )

    fig.legend(fontsize=18)

    ## The ratio below ######################################################

    ax1=fig.add_subplot(gs[1]) # First row, second column
    
    ratio_label="ratio_%s" % beam
    
    ax1.plot(x, df[ratio_label], 'o', color='black', markersize=10, markerfacecolor='gray', markeredgecolor='black', markeredgewidth=2)
    ax1.set_ylabel( "Ratio", fontsize=16 )

    #ax0.grid(True, linestyle='--')
    ax1.tick_params(axis="y",direction="in", left="on", right='on')
    ax1.tick_params(axis="x",direction="in", bottom="on",top='on')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Y'))
    
    ax1.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )

    ax1.set_ylim(0, 1.0)
    
    plt.tight_layout()
    
    return plt

def makePOTPlotBoth( df, beam1, beam2,range ):

    fig=plt.figure( figsize=(16,6.0) )

    gs=GridSpec(2,1, height_ratios=[6, 2])

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column

    ax0.set_title(beam1.upper(), fontsize=18)

    del_label1="pot_%s_delivered" % beam1
 
    df["timeindex"] = pd.to_datetime( df["day"], utc=True )
    df = df[ ( df.timeindex >= pd.to_datetime( range[0], utc=True ) ) & ( df.timeindex <= pd.to_datetime( range[1], utc=True ) ) ]

    x=df["timeindex"].values
    y=np.cumsum(df[del_label1]/1000000)

    ax0.plot( x, y,':C0', linewidth=4.0, label="NuMI Delivered: %.1f E18 POT" % np.max(y))

    del_label2="pot_%s_delivered" % beam2

    y=np.cumsum(df[del_label2]/1000000)

    ax0.plot( x, y, ':C1', linewidth=4.0, label="BNB Delivered: %.1f E18 POT" % np.max(y))

    col_label1="pot_%s_collected" % beam1

    y=np.cumsum( df[col_label1]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="NuMI Collected: %.1f E18 POT" % np.max(y) )

    col_label2="pot_%s_collected" % beam2

    y=np.cumsum( df[col_label2]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="BNB Collected: %.1f E18 POT" % np.max(y) )

    ax0.set_ylabel( "$10^{18}$ POT", fontsize=16 )
    ax0.set_xlabel( "Day (UTC)", fontsize=16 )

    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    ax0.legend(fontsize=18, loc='upper left')

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    plt.tight_layout()

    return plt

def makePOTSumPlot( df, beam, range ):

    fig=plt.figure( figsize=(16,6.0) )

    gs=GridSpec(2,1, height_ratios=[6, 2]) 

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column
    
    ax0.set_title(beam.upper(), fontsize=18)
    
    del_label="pot_%s_delivered" % beam
    
    df["timeindex"] = pd.to_datetime( df["day"], utc=True )
    df = df[ ( df.timeindex >= pd.to_datetime( range[0], utc=True ) ) & ( df.timeindex <= pd.to_datetime( range[1], utc=True ) ) ]    

    x=df["timeindex"].values
    y=np.cumsum(df[del_label]/1000000)
    
    ax0.plot( x, y, linewidth=4.0, label="Delivered: %.1f E18 POT" % np.max(y) )
    
    col_label="pot_%s_collected" % beam
    
    y=np.cumsum( df[col_label]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="Collected: %.1f E18 POT" % np.max(y) )

    ax0.set_ylabel( "$10^{18}$ POT", fontsize=16 )
    ax0.set_xlabel( "Day (UTC)", fontsize=16 )
    
    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    ax0.legend(fontsize=18, loc='upper left')

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    plt.tight_layout()
    
    return plt


def makeDAQEffPlot( pot_daily_collected, range ):

    fig, ax = plt.subplots( 1,1, figsize=(18, 4.3), sharey=True )

    norm=24

    ax.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["runtime"]/(3600.)/norm, '-.', color="#E48900", linewidth=5, label="DAQ Uptime")

    #print( mode( pot_daily_collected["runtime"]/(3600.)) )
    #print( np.median( pot_daily_collected["runtime"]/(3600.)/norm) )
    #print( np.mean( pot_daily_collected["runtime"]/(3600.)) )
    
    ax.yaxis.grid(True, linestyle='--')

    ax.tick_params(axis="y",direction="in", left="on", right='on')
    ax.tick_params(axis="x",direction="in", bottom="on",top='on')
    ax.set_ylim((0.0, 1.1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_ylabel( "DAQ Time / 24 hours", fontsize=16 )

    ax1 = ax.twinx()

    #print ( pot_daily_collected["ratio_bnb"])
    #print ( pot_daily_collected["ratio_numi"])

    ax1.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["ratio_bnb"], 'o', markersize=14, markerfacecolor='#9EDE73', markeredgecolor='black', markeredgewidth=2, label="BNB Efficiency")
    ax1.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["ratio_numi"], '^', markersize=14, markerfacecolor='#BE0000', markeredgecolor='black', markeredgewidth=2, label="NuMI Efficiency")
    ax1.set_ylim((0.0, 1.1))
    ax1.set_ylabel( "POT collected / POT delivered", fontsize=16 )
    ax1.set_xlabel( "Day (UTC)", fontsize=16 )

    fig.legend(fontsize=16, bbox_to_anchor=[0.2, 0.4])

    ax.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    fig.tight_layout()

    return plt

def makePOTPlotRun( df, beam, run ):

    fig=plt.figure( figsize=(15,5) )

    gs=GridSpec(2,1, height_ratios=[6, 2]) 

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column
    
    ax0.set_title(beam, fontsize=18)

    #ax0.axis("off")
    ax0.spines["right"].set_visible(False)
    ax0.spines["left"].set_visible(False)
    ax0.spines["top"].set_visible(False)

    ax0.yaxis.grid( linestyle='-' )
    
    del_label="pot_%s_delivered" % beam
    
    x=pd.to_datetime( df["day"], utc=True )
    y=df[del_label]/1000000
    ax0.fill_between(x, y, step="mid", alpha=0.2)
    ax0.step( x, y, drawstyle="steps", where='mid', linewidth=2.0, label="Delivered" )
    
    col_label="pot_%s_collected" % beam
    
    y=df[col_label]/1000000
    ax0.fill_between(x, y, step="mid", alpha=0.4)
    ax0.step( x, y, drawstyle="steps", where='mid', linewidth=2.0,label="Collected" )

    ax0.set_ylabel( "$10^{18}$ POT/day", fontsize=16 )

    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Y'))

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )

    fig.legend(fontsize=18)

    ## The ratio below ######################################################

    ax1=fig.add_subplot(gs[1]) # First row, second column
    
    ratio_label="ratio_%s" % beam
    
    ax1.plot(x, df[ratio_label], 'o', color='black', markersize=10, markerfacecolor='gray', markeredgecolor='black', markeredgewidth=2)
    ax1.set_ylabel( "Ratio", fontsize=16 )

    #ax0.grid(True, linestyle='--')
    ax1.tick_params(axis="y",direction="in", left="on", right='on')
    ax1.tick_params(axis="x",direction="in", bottom="on",top='on')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Y'))
    
    ax1.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )

    ax1.set_ylim(0, 1.0)
    
    plt.tight_layout()
    
    return plt

def makePOTPlotBothRun( df, beam1, beam2,run ):

    fig=plt.figure( figsize=(16,6.0) )

    gs=GridSpec(2,1, height_ratios=[6, 2])

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column

    ax0.set_title(beam1.upper(), fontsize=18)

    del_label1="pot_%s_delivered" % beam1
 
    df["timeindex"] = pd.to_datetime( df["day"], utc=True )
    df = df[ ( df.timeindex >= pd.to_datetime( range[0], utc=True ) ) & ( df.timeindex <= pd.to_datetime( range[1], utc=True ) ) ]

    x=df["timeindex"].values
    y=np.cumsum(df[del_label1]/1000000)

    ax0.plot( x, y,':C0', linewidth=4.0, label="NuMI Delivered: %.1f E18 POT" % np.max(y))

    del_label2="pot_%s_delivered" % beam2

    y=np.cumsum(df[del_label2]/1000000)

    ax0.plot( x, y, ':C1', linewidth=4.0, label="BNB Delivered: %.1f E18 POT" % np.max(y))

    col_label1="pot_%s_collected" % beam1

    y=np.cumsum( df[col_label1]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="NuMI Collected: %.1f E18 POT" % np.max(y) )

    col_label2="pot_%s_collected" % beam2

    y=np.cumsum( df[col_label2]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="BNB Collected: %.1f E18 POT" % np.max(y) )

    ax0.set_ylabel( "$10^{18}$ POT", fontsize=16 )
    ax0.set_xlabel( "Day (UTC)", fontsize=16 )

    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    ax0.legend(fontsize=18, loc='upper left')

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    plt.tight_layout()

    return plt

def makePOTSumPlotRun( df, beam, run ):

    fig=plt.figure( figsize=(16,6.0) )

    gs=GridSpec(2,1, height_ratios=[6, 2]) 

    ## The pot plots ####################################################

    ax0=fig.add_subplot(gs[0]) # First row, first column
    
    ax0.set_title(beam.upper(), fontsize=18)
    
    del_label="pot_%s_delivered" % beam
    
    df["timeindex"] = pd.to_datetime( df["day"], utc=True )
    df = df[ ( df.timeindex >= pd.to_datetime( range[0], utc=True ) ) & ( df.timeindex <= pd.to_datetime( range[1], utc=True ) ) ]    

    x=df["timeindex"].values
    y=np.cumsum(df[del_label]/1000000)
    
    ax0.plot( x, y, linewidth=4.0, label="Delivered: %.1f E18 POT" % np.max(y) )
    
    col_label="pot_%s_collected" % beam
    
    y=np.cumsum( df[col_label]/1000000 )
    ax0.plot( x, y, linewidth=4.0,label="Collected: %.1f E18 POT" % np.max(y) )

    ax0.set_ylabel( "$10^{18}$ POT", fontsize=16 )
    ax0.set_xlabel( "Day (UTC)", fontsize=16 )
    
    ax0.tick_params(axis="x",direction="in", bottom="on")

    ax0.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    ax0.legend(fontsize=18, loc='upper left')

    ax0.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    plt.tight_layout()
    
    return plt


def makeDAQEffPlotRun( pot_daily_collected, run ):

    fig, ax = plt.subplots( 1,1, figsize=(18, 4.3), sharey=True )

    norm=24

    ax.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["runtime"]/(3600.)/norm, '-.', color="#E48900", linewidth=5, label="DAQ Uptime")

    print( mode( pot_daily_collected["runtime"]/(3600.)) )
    print( np.median( pot_daily_collected["runtime"]/(3600.)/norm) )
    print( np.mean( pot_daily_collected["runtime"]/(3600.)) )
    
    ax.yaxis.grid(True, linestyle='--')

    ax.tick_params(axis="y",direction="in", left="on", right='on')
    ax.tick_params(axis="x",direction="in", bottom="on",top='on')
    ax.set_ylim((0.0, 1.1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_ylabel( "DAQ Time / 24 hours", fontsize=16 )

    ax1 = ax.twinx()

    #print ( pot_daily_collected["ratio_bnb"])
    #print ( pot_daily_collected["ratio_numi"])

    ax1.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["ratio_bnb"], 'o', markersize=14, markerfacecolor='#9EDE73', markeredgecolor='black', markeredgewidth=2, label="BNB Efficiency")
    ax1.plot( pd.to_datetime(pot_daily_collected["day"], utc=True), pot_daily_collected["ratio_numi"], '^', markersize=14, markerfacecolor='#BE0000', markeredgecolor='black', markeredgewidth=2, label="NuMI Efficiency")
    ax1.set_ylim((0.0, 1.1))
    ax1.set_ylabel( "POT collected / POT delivered", fontsize=16 )
    ax1.set_xlabel( "Day (UTC)", fontsize=16 )

    fig.legend(fontsize=16, bbox_to_anchor=[0.2, 0.4])

    ax.set_xlim( pd.to_datetime( range[0], utc=True ), pd.to_datetime( range[1], utc=True ) )


    fig.tight_layout()

    return plt

