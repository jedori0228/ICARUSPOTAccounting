#!/bin/bash
scp ${gatewayhostname}:/daq/log/DAQInterface_partition1.log ${potDir}/temp/DAQInterface_partition1.log.new
cd temp
./merge.sh
