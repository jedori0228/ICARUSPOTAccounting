#!/bin/bash

## run1
#init=2022-06-09
#fin=2022-07-09

## run2
#init=2022-12-20
#fin=2023-03-06

## run1 + run2
#init=2022-06-09
#fin=2023-03-06

## weekly
init=2023-03-06
fin=2023-03-12

python ParseDAQLog.py -i ${init} -f ${fin}
python pot_account.py update-daily-pot ${init} ${fin} True
python pot_account.py update-daily-runs ${init} ${fin} True
python pot_account.py make-daq-plots ${init} ${fin}


