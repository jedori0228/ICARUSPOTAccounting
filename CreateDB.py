import sys, os
import time
import datetime
import numpy as np

from utils.dbmanager import add_run_day_pot, add_run_pot, create_connection, create_table
from beaminfo.simple_query import query_pot_interval
from runinfo.read_run_info import make_timestamp, parse_line

potDir = os.environ["potDir"]
dbname = "%s/dbase/RunSummary.db"%(potDir)
conn = create_connection(dbname)

create_run_timestamp = """ CREATE TABLE IF NOT EXISTS run_timestamp (
run INTEGER NOT NULL,
start TIMESTAMP NOT NULL,
stop TIMESTAMP NOT NULL,
conf TEXT,
comment TEXT,
UNIQUE( run )
  ); """

create_daily_collected_pot = """ CREATE TABLE IF NOT EXISTS daily_collected_pot (
day TEXT NOT NULL,
pot_bnb_collected REAL NOT NULL,
pot_numi_collected REAL NOT NULL,
runtime REAL NOT NULL,
UNIQUE( day )
  ); """


create_day_pot_bnb = """ CREATE TABLE IF NOT EXISTS day_pot_bnb (
day text PRIMARY KEY,
pot real NOT NULL,
UNIQUE( day )
); """

create_day_pot_numi = """ CREATE TABLE IF NOT EXISTS day_pot_numi (
day text PRIMARY KEY,
pot real NOT NULL,
UNIQUE( day )
); """

create_table( conn, create_run_timestamp )
create_table( conn, create_daily_collected_pot )
create_table( conn, create_day_pot_bnb )
create_table( conn, create_day_pot_numi )
