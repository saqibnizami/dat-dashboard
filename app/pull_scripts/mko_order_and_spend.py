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

def get_creds(id_file, token_file, sub):
    """
    Returns a dictionary containing credentials from Vault

    PARAMETERS:
    id_file : path of vault id file
    token_file : path of vault token file
    sub : sub folder in the vault, eg. 'pg', 'phi', 'mysql'
    """
    with open(os.path.expanduser(id_file)) as f:
        v_id = f.read()

    with open(os.path.expanduser(token_file)) as ft:
        v_token = ft.read()
    
    client = hvac.Client(url='https://vault.ubiome.com:8200',
                         token=v_token)
    cred_path = 'secret/production/{}/{}/'.format(v_id, sub)
    creds = client.read(cred_path)['data']
    return creds
    

#%%
id_path = '~/.vault/dash_vault_id'
token_path = '~/.vault/dash_vault_token'
print(get_creds(id_path, token_path, 'pg'))

# #%%
# # Using plaintext
# VAULT_ID = file_home_token('~/.vault/dash_vault_id')
# client = hvac.Client(url='https://vault.ubiome.com:8200', 
#                      token=file_home_token('~/.vault/dash_vault_token'))

# phi = client.read('secret/production/' + VAULT_ID + '/phi/')['data']
# pg = client.read('secret/production/' + VAULT_ID + '/pg/')['data']
# mysql = client.read('secret/production/' + VAULT_ID + '/mysql/')['data']

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
#%%
orders = SQLtoDF(sqlfile="queries/mko/mode_orders.pgsql",
                 database="backend",
                 creds=pg,
                 driver="postgres",
                 foldername="mko",
                 tablename="orders_with_utms"
                 )
#%%
testengine = makeEngine(d='backend', creds=pg, driver='postgres')
#%%
os.getcwd()

#%%
# get the age of a file

config = Path('data/current/mko/orders_with_utms_backend_pull_at_20190318_182929.csv')


#%%
created = config.stat().st_ctime
modified = config.stat().st_mtime


#%%
print(\
dt.fromtimestamp(created),
dt.fromtimestamp(modified))
#%%
dt.now().strftime("%Y%m%d%H%M%S")

#%%
# pull off the timestamp from the data file
config.stem

#%%

#%%

p = Path('data/current/mko')

#%%
[re.search(timepattern,x.stem).group() for x in p.glob("orders*.csv")]
for x in p.glob("orders*.csv"):
    
#%%
def tree(directory):
    print(f'+ {directory}')
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = '    ' * depth
        print(f'{spacer}+ {path.name}')

#%%
tree(p)

#%%
foldername = 'cartmetrics'
tablename = 'orders_utms'
database = 'products'
now = pd.Timestamp.now().round('s')

filepath = 'data/current/{}/{}_{}_pull_at_{}.csv'.format(foldername, 
                                                        tablename,
                                                        database,
                                                        now)

parent = os.path.dirname(filepath)
os.makedirs(parent, exist_ok=True)

#%%

foldername = 'cartmetrics'
tablename = 'orders_utms'
database = 'products'

now = pd.Timestamp.now().round('s')
timeformat = "%Y%m%d_%H%M%S"

# now = pd.Timestamp.now().round('s')#.strftime("{}".format(timeformat))
# regex pattern for timestamp in filename

timepattern = re.compile(r"(\d{8}_\d{6})")
datapath = Path('data/current/mko').glob("*")
filedelta = {}
for f in datapath:
    stem = f.stem
    if tablename in stem:
        search = re.search(timepattern, stem)
        if search:
            stamp = pd.to_datetime(search.group(), format = timeformat)
            delta = now-stamp
            filedelta[delta] = f
            
#%%
filedelta[min(filedelta.keys())]


#%%
# TODO: add in move files in current that are greater than latest

def loadNewest(foldername, tablename):
    """
    Returns the latest data from the folder and tablename
    """
    now = pd.Timestamp.now().round('s')
    timeformat = "%Y%m%d_%H%M%S"

    # now = pd.Timestamp.now().round('s')#.strftime("{}".format(timeformat))
    # regex pattern for timestamp in filename

    timepattern = re.compile(r"(\d{8}_\d{6})")
    datapath = Path('data/current/{}'.format(foldername)).glob("*")
    filedelta = {}
    for f in datapath:
        stem = f.stem
        if tablename in stem:
            search = re.search(timepattern, stem)
            if search:
                stamp = pd.to_datetime(search.group(), format = timeformat)
                delta = now-stamp
                filedelta[delta] = f
    latest = filedelta[min(filedelta.keys())]
    df = pd.read_csv(latest)
    
    return df
    
    

#%%
latest = filedelta[min(filedelta.keys())]

#%%
[x for x in pd.read_csv(latest).columns]

#%%
loadNewest(foldername='mko', tablename='orders_utms')

#%%
