# ICARUS POT accounting script

## Prerequisite
[Conda](https://docs.conda.io/en/latest/miniconda.html) is recommended
```
# Recommend /exp/icarus/app/users/ for the miniconda installation
cd /exp/icarus/app/users/${USER}/
# Download the installer
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh
# Run the installer
bash Miniconda3-latest-Linux-x86_64.sh 
# It asks you where to install the package. Default is ${HOME}, but
# should be changed to /exp/icarus/app/users/${USER}/miniconda3/
# Creating environment from a .yml file (only need once)
conda env create --name runco --file=CondaEnv/runco.yml
# Activating the environment (every time with new shell)
conda activate runco
```

## For committing to Fermilab directorate performance database
```
# We need oracle db libraries
# Download the installer
wget https://download.oracle.com/otn_software/linux/instantclient/218000/instantclient-basic-linux.x64-21.8.0.0.0dbru.zip
# Unzip
unzip instantclient-basic-linux.x64-21.8.0.0.0dbru.zip
```

## Setup
```
# Running setup script (every time with new shell)
source env_setup.sh
# If an initial db file is missing from ${potDir}/dbase/, either
# 1) Create a new one
mkdir -p dbase
python CreateDB.py
# 2) Copy from existing one
cp /exp/icarus/app/users/jskim/Runco/ICARUSPOTAccounting/share/RunSummary.db ${potDir}/dbase/
```

## Parsing DAQInterface log file
DAQIntercae log file (e.g., `DAQInterface_partition1.log`) contains typically O(1E6) lines. We parse this file and save the run start/stop times into a database, before we query BNB/NuMI DB.
```
## Creat temp directory if doesn't exist
mkdir -p ${potDir}/temp/
## Copy file from icarus gateway
source getDAQLog.sh
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

## Commit weekly report to Fermilab directorate performance database

```
# -i: Start day, should be Monday
# (-f: Optional; End date will be automatically set to Sunday)
# --no_commit: Do not commit the data; Run this before you update date the DB
python UpdateFermiDB.py -i YYYY-MM-DD --dev # Update the Develop area for debugigng
python UpdateFermiDB.py -i YYYY-MM-DD --prod # Update the Prodcution area
```

You can check the committed data from (need VPN if you are offsite)
- Develop area: https://ccdapps-dev.fnal.gov/pls/apex/f?p=104
- Production area: https://ccdapps-prod.fnal.gov/pls/apex/f?p=104

## To get the updates from github
`git pull`
