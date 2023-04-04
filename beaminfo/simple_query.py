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

  pot = 0.
  spill = 0
  for i, line in enumerate(f):
    if i==0:
      continue
    pot += parse_line(line)
    spill += 1
  print('interval t0',t0,'t1',t1,'pot',pot,'spill',spill,'device',device_name)
  return pot, spill


def query_full_day_pot(ts_start, ts_end, device_name, event, debug=False ):

  url = "%s/data?v=%s&e=e,%s&t0=%d&t1=%d&f=csv" % (beamdburl, device_name, event, ts_start, ts_end)

  if debug:
    print( "URL:", url )

  f = urllib.request.urlopen(url)

  if debug:
    print( "Status code: %s\n" % (f.getcode(),) )

  pot = 0.
  spill = 0
  for i, line in enumerate(f):
    if i==0:
      continue
    pot += parse_line(line)
    spill += 1
  print('full day t0',ts_start,'t1',ts_end,'pot',pot,'spill',spill,'device',device_name)
  return pot, spill

def get_full_day_horncurrent(ts_start, ts_end, device_name, event, debug=False ):

  url = "%s/data?v=%s&e=e,%s&t0=%d&t1=%d&f=csv" % (beamdburl, device_name, event, ts_start, ts_end)

  if debug:
    print( "URL:", url )

  print(url)

  f = urllib.request.urlopen(url)

  if debug:
    print( "Status code: %s\n" % (f.getcode(),) )

  totalcount = 0.
  sumcurrent = 0.
  for i, line in enumerate(f):
    if i==0:
      continue
    this_current = parse_line(line)
    #print("get_full_day_horncurrent", device_name, this_current)
    if abs(this_current)>10.:
      totalcount += 1.
      sumcurrent += this_current
  avgcurrent = 0.
  if totalcount>0.:
    avgcurrent = sumcurrent/totalcount
  print('full day sum current',ts_start,'t1',ts_end,'sum_current',sumcurrent,'avg_current',avgcurrent,'device',device_name)

  return avgcurrent

def query_full_day( ts_start_day, ts_end_day, beam ):

  ## pot

  pot_db_device = "E:TORTGT" if beam=="numi" else "E:TOR875" # else = bnb
  pot_db_event = "a9" if beam=="numi" else "1d" # else = bnb

  pot, spill = query_full_day_pot(ts_start_day, ts_end_day, pot_db_device, pot_db_event)

  ## horn current

  hc_db_device = "E:HRNDIR" if beam=="numi" else "E:THCURR" # else = bnb
  hc_db_event = "a9" if beam=="numi" else "1d" # else = bnb

  hc = get_full_day_horncurrent(ts_start_day, ts_end_day, hc_db_device, hc_db_event)

  mode = "none"
  if beam=="numi":
    if hc<0:
      mode = "nu"
    elif hc>0:
      mode = "nubar"
  elif beam=="bnb":
    if hc>0:
      mode = "nu"
    elif hc<0:
      mode = "nubar"

  return [pot, spill, mode]
  
