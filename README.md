![](https://github.com/uBiome/ubiome-dat-dashboard/blob/master/assets/datdash-main.png)
***


- [Standard Procedures for Dashboarding Apps](#standard-procedures-for-dashboarding-apps)
  - [Folder Structure](#folder-structure)
  - [Data Pull Scripts](#data-pull-scripts)
  - [Using Git Flow](#using-git-flow)
  
# Standard Procedures for Dashboarding Apps

## Folder Structure
        |--app_archive/     
        |--apps/            
        |--assets/          
           |--project_subfolder
        |--data/            
           |--archive
           |--current
        |--pull_scripts/    
        |--queries/         
        |--subapps/         
           |--project_subfolder

**More information:**
1. `app_archive` : Store unused or deprecated apps. Use it as a backup folder for previous app versions if so desired.
2. `apps` : Current app files. Store only .py files here as they will show up on the index page.
3. `assets` : Support files for your dash. Do not store data files or query files here. More for images, etc. Use subfolders for clarity.
4. `data/archive` : The location your data pulling script stores the previous datafile before overwriting it with the latest pull.
5. `data/current` : Latest data pull, this is where your app reads from.
6. `pull_scripts` : A .py file that contains credentials, connects to a database or api, pulls down data, and saves it to `data/current` while moving any previous file to `data/archive`. See section 2: Data Pull Scipts for example.
7. `subapps` : keep your main app file clean by storing tabs or large subapps in this folder, and importing them into your main app. Use project subfolders to keep it clean.

## Data Pull Scripts
Remember to:
- Store in `pull_scripts` and use a subfolder. Example: `mko` for Marketing Key Ops.
- Contain credentials (use VaultUI, i.e. `import hvac`)
- Have script move old data file to `data/archive` in case something goes wrong
- Store new data in `data/current`
- If multiple apps require the same data, make your pull such that you aren't storing redundant information
- When pushing a script, specify the interval you'd like it to run with in your Pull Request

Sample Script:
```python
#%% IMPORTS ###################################################################
#
###############################################################################
import hvac
import os
import sqlalchemy as db
import psycopg2
import sys
import pandas as pd
import numpy as np
from datetime import datetime as dt
import re
from pathlib import Path


#%% CREDENTIALS ###############################################################
#
###############################################################################

def file_home_token(file_name):
    with open(os.path.expanduser(file_name)) as f:
        return f.read()

# Using plaintext
VAULT_ID = file_home_token('~/.vault/dash_vault_id')
client = hvac.Client(url='https://vault.ubiome.com:8200', 
                     token=file_home_token('~/.vault/dash_vault_token'))

phi = client.read('secret/production/' + VAULT_ID + '/phi/')['data']
pg = client.read('secret/production/' + VAULT_ID + '/pg/')['data']
mysql = client.read('secret/production/' + VAULT_ID + '/mysql/')['data']

#%% QUERY FUNCTIONS############################################################
#
###############################################################################

# create engine using sqlalchemy
def makeEngine(d, creds, driver='postgres'):
    '''
    Create a connection to your desired database using VAULT credentials and
    SQLAlchemy

    Parameters:
    d : string. name of database
    creds : variable holding credential dictionary from VAULT
    driver : string. "postgres" for PostgreSQL and "mysql+pymysql" for MySQL
            NB: pymysql doesn't need to be imported but it should be installed

    Example:
    mysql_engine = makeEngine(d="ubiome", creds=mysql, driver="mysql+pymysql")
    '''

    # create a URL in the form
    # driver://USER:PW@host:port/database
    dburl = db.engine.url.URL(driver,
                                database = d,
                                username = creds['user'], 
                                password = creds['pw'], 
                                host = creds['host'], 
                                port = creds['port'])
    
    # sqlalchemy was imported as db
    # use the dburl to make an engine (connection) to the database
    engine = db.create_engine(dburl)

    # return the connection for use
    return engine 


def SQLtoDF(sqlfile, database, creds, driver, foldername, queryaddition="", 
            tablename=""):
    """
    Opens a .sql or .pgsql file, runs the query using the engine made by the 
    makeEngine() function.

    PARAMETERS: 
    sqlfile = string. Path to .sql file containing the query to be executed
    database = string. Name of database being accessed.
    creds = variable containing the VaultUI dictionary with credentials
    driver = string. "postgres" for PostgreSQL or "mysql+pymysql" for MySQL
    foldername = This is the sub folder in /data/current that will be checked
                for an outdated file and where the new data will be stored.
    queryaddition = string. Raw SQL to inject into the query. Can be enabled by 
                placing `{}` in your query file. 
    tablename = string. Used for the filename, so use underscores for spaces.
                Identifies the table or tables data was pulled from.
    
    EXAMPLE:
    orders = SQLtoDF(sqlfile="queries/mko/mode_orders.pgsql",
                    database="backend",
                    creds=pg,
                    driver="postgres",
                    foldername="mko",
                    tablename="orders_with_utms"
                    )
    """
    timeformat = "%Y%m%d_%H%M%S"
    now = pd.Timestamp.now().strftime("{}".format(timeformat))
    with open(sqlfile, 'r') as f:
        query = f.read()
        f.close()
    
    query = db.text(query.format(queryaddition))
    engine = makeEngine(d=database, creds=creds, driver=driver)
    df = pd.read_sql(sql=query, con=engine)

    # check if subdirectory exists
    # check for a file, pull timestamp off filename, check if the timestamp is 
    # before now
    filepath = 'data/current/{}/{}_{}_pull_at_{}.csv'.format(foldername,
                                                            tablename,
                                                            database,
                                                            now)
    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    df.to_csv(filepath, index=False)
 
    return df
```


## Using Git Flow

- [GitFlow Cheatsheet](https://danielkummer.github.io/git-flow-cheatsheet/)
- [Git Flow Commands vs Pure Git Commands](https://gist.github.com/JamesMGreene/cdd0ac49f90c987e45ac)