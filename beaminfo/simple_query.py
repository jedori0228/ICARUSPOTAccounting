import urllib.request, sys, os

import numpy as np

beamdburl = os.environ["beamdburl"]

def parse_line(line):
#  print('line',line)
  line = ( line.strip() ).decode('utf-8')
#  print('line',line)
  buff = line.split(",")
#  print('buff',buff)
  return float(buff[5])


def query_pot_interval( t0, t1, device_name, event, debug=False ):

  url = "%s/data?v=%s&e=e,%s&t0=%d&t1=%d&f=csv" % (beamdburl, device_name, event, t0, t1)

  print(url)

  if debug:
    print( "URL:", url )

  f = urllib.request.urlopen(url)

  if debug:
    print( "Status code: %s\n" % (f.getcode(),) )

  pot = np.sum( [ parse_line(line) for i, line in enumerate(f) if i!=0 ])
  print('interval t0',t0,'t1',t1,'pot',pot,'device',device_name)
  return pot


def query_full_day( ts_start,ts_end, device_name, event, debug=False ):

  url = "%s/data?v=%s&e=e,%s&t0=%d&t1=%d&f=csv" % (beamdburl, device_name, event, ts_start, ts_end)

  if debug:
    print( "URL:", url )

  f = urllib.request.urlopen(url)

  if debug:
    print( "Status code: %s\n" % (f.getcode(),) )

  pot = np.sum( [ parse_line(line) for i, line in enumerate(f) if i!=0 ])
  print('full day t0',ts_start,'t1',ts_end,'pot',pot,'device',device_name)
  return pot
