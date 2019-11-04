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

def get_creds(id_file, token_file, sub, is_dash=True):
    """
    Returns a dictionary containing credentials from Vault.
    If using ubiome-analytics-dashboard vault, set is_dash to True,
    If using personal vault, set is_dash to False
    PARAMETERS:
    id_file : path of vault id file
    token_file : path of vault token file
    sub : sub folder in the vault, eg. 'pg', 'phi', 'mysql'
    EXAMPLE: 
    id_path = '\~/.vault/dash_vault_id'
    token_path = '\~/.vault/dash_vault_token'
    pg = get_creds(id_path, token_path, 'pg')
    """
    with open(os.path.expanduser(id_file)) as f:
        v_id = f.read()

    with open(os.path.expanduser(token_file)) as ft:
        v_token = ft.read()

    client = hvac.Client(url='https://vault.ubiome.com:8200',
                         token=v_token)
    if is_dash==True:
        cred_path = 'secret/production/{}/{}/'.format(v_id, sub)
        creds = client.read(cred_path)['data']
        return creds
    else:
        cred_path = 'secret/{}/{}/'.format(v_id, sub)
        creds = client.read(cred_path)['data']
        return creds
    

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


def metabase_to_df(question_id, creds, folder_name, query_parameters):
    timeformat = "%Y%m%d_%H%M%S"
    now = pd.Timestamp.now().strftime("{}".format(timeformat))

    header = {'Content-Type': 'application/json'}
    data ={'username': creds['user'], 'password': creds['pass']}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/{}/query/json{}'.format(question_id, query_parameters)
    data = requests.post(card, headers=get_header)
    df = pd.DataFrame(data.json())

    # check if subdirectory exists
    # check for a file, pull timestamp off filename, check if the timestamp is
    # before now
    filepath = 'data/current/{}/metabase_pull_at_{}.csv'.format(folder_name,
                                                            now)
    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    df.to_csv(filepath, index=False)

    return df
