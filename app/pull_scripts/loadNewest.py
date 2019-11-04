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
    
    try:
        df = pd.read_csv(latest)
        print("Loading {}".format(latest))
    except Exception as e:
        print("Exception, {}, occurred with loading {}".format(e, latest))
    
    return df
    