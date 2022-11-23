# ICARUS POT accounting script

## Prerequisite
[Conda](https://docs.conda.io/en/latest/miniconda.html) is recommended
```
## Recommend /icarus/app/users/ for the miniconda installation
cd /icarus/app/users/${USER}/
## Get installer
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh
## Install
## It asks you where to install the package. Default is ${HOME}, but 
## should be changed to /icarus/app/users/${USER}/miniconda3/
bash Miniconda3-latest-Linux-x86_64.sh 
## Creating environment from a .yml file (only need once)
conda env create --name runco --file=CondaEnv/runco.yml
## Activating the environment (every time with new shell)
conda activate runco
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
DAQIntercae log file (e.g., `DAQInterface_partition1.log`) contains typically O(1E6) lines. We parse this file and save the run start/stop times into a database, before we query BNB/NuMI DB.
```
## Creat temp directory if doesn't exist
mkdir -p ${potDir}/temp/
## Copy file from icarus gateway
scp ${gatewayhostname}:/daq/log/DAQInterface_partition1.log ${potDir}/temp/  
## Run parsing script
python ParseDAQLog.py -i YYYY-MM-DD -f YYYY-MM-DD
```

- ```-i YYYY-MM-DD```: Which day to start updating
- ```-f YYYY-MM-DD```: Up to which day to update

## Update delivered POT

```python pot_account.py update-daily-pot YYYY-MM-DD YYYY-MM-DD <True/False>```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated
- ```True/False``` are booleans for "override" option; True if you want to update the current table with new values

## Update collected POT

```python pot_account.py update-daily-runs YYYY-MM-DD YYYY-MM-DD <True/False>```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated
- ```True/False``` are booleans for "override" option; True if you want to update the current table with new values

## Draw plots

```python pot_account.py make-daq-plots YYYY-MM-DD YYYY-MM-DD```

- ```YYYY-MM-DD YYYY-MM-DD``` are the start and the end date to be updated

## To get the updates from github
`git pull`
