# ICARUS POT accounting script

## Prerequisite
[Conda](https://docs.conda.io/en/latest/miniconda.html) is recommended
```
## Creating environment from a .yml file (only need once)
conda env create --name runco --file=CondaEnv/runco.yml
## Activating the environment (every time with new shell)
conda acticate runco
```

## Setup
```
## Running setup script (every time with new shell)
source env_setup.sh
## source shared environment (every time with new shell)
source /icarus/app/users/jskim/Runco/ICARUSPOTAccounting/share/shared_env_setup.sh
## If an initial db file is missing from ${potDir}/dbase/, either
## 1) Create a new one
mkdir -p dbase
python CreateDB.py
## 2) Copy from existing one
cp /icarus/app/users/jskim/Runco/ICARUSPOTAccounting/share/RunSummary.db ${potDir}//dbase/
```

## Parsing DAQInterface log file
DAQIntercae log file (e.g., `DAQInterface_partition1.log`) contains typically ~2M lines. We parse this file and save the run start/stop times into a database, before we query BNB/NuMI DB.
```
## Creat temp directory if doesn't exist
mkdir -p ${potDir}/temp/
## Copy file from icarus gateway
scp ${gatewayhostname}:/daq/log/DAQInterface_partition1.log ${potDir}/temp/  
## Run parsing script
python ParseDAQLog.py
```

## Update delivered POT

```python pot_account.py update-multi-daily-pot YYYY-MM-DD YYYY-MM-DD <True/False>```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated
- ```True/False``` are booleans for "override" option; True if you want to update the current table with new values

## Update collected POT

```python pot_account.py update-multi-daily-runs YYYY-MM-DD YYYY-MM-DD <True/False>```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated
- ```True/False``` are booleans for "override" option; True if you want to update the current table with new values

## Draw plots

```python pot_account.py make-daq-plots YYYY-MM-DD YYYY-MM-DD```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated
