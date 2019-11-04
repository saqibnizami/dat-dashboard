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


#####
#SQL Querying Function
##Queries and saves to CSV
#####
def sql_to_csv(pg_user, pg_pw, pg_host, pg_port, mysql_user, mysql_pw, phi_user, phi_pw, phi_host, phi_port):
    #orders created (jon query)
    conn = psycopg2.connect(database="backend", user = pg_user, password = pg_pw, host = pg_host, port = pg_port)
    cur = conn.cursor()
    cur.execute("""
    SELECT
        orders.id AS order_id,
        order_flow,
        created_at AS order_created_at,
        order_type.code,
        owner_id,
        state,
        prescription_id,
        sample_id,
        delivery_id
    FROM orders.orders
    INNER JOIN orders.order_type
    ON orders.order_type_id=order_type.id
    WHERE state NOT IN ('DRAFT') AND created_at > '2017-12-31'
    """)
    #place sql query into dataframe
    df_orders = pd.DataFrame(cur.fetchall())
    #get column headers for dataframe
    df_orders.columns = [i[0] for i in cur.description]
    conn.commit()
    conn.close()

    #kits shipped (engineering query)
    conn = psycopg2.connect(database="backend", user = pg_user, password = pg_pw, host = pg_host, port = pg_port)
    cur = conn.cursor()
    cur.execute("""
    SELECT
        ship.id AS shipment_id,
        ship.order_id AS delivery_id,
        o.item_type_id,
        ship.ship_date
    FROM  delivery.shipment_view AS ship
    INNER JOIN delivery.order_item_view AS o on ship.order_id = o.order_id
    WHERE ship.type = 'NORMAL' AND ship_date > '2017-12-31'
    """)
    #place sql query into dataframe
    df_kits = pd.DataFrame(cur.fetchall())
    #get column headers for dataframe
    df_kits.columns = [i[0] for i in cur.description]
    conn.commit()
    conn.close()

    #samples accessioned (erica query)
    mydb = pymysql.connect(
        host='mysql.east',
        user=mysql_user,
        password=mysql_pw,
        db='ubiome',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    cur = mydb.cursor()

    cur.execute("""
    SELECT
        s.received AS sample_received,
        s.id AS sample_id,
        k.kit_type,
        k.registered,
        csss.status AS sample_process_status
    FROM ubiome.samples AS s
    INNER JOIN ubiome.kits AS k ON k.barcode = s.kit_barcode
    LEFT JOIN ubiome.clinical_samples_sequencing_status AS csss ON csss.sample = s.id
    WHERE k.barcode NOT LIKE 'study-%' AND s.received > '2017-12-31'
    """)
    #place sql query into dataframe
    df_samples = pd.DataFrame(cur.fetchall())

    #reports blocked
    mydb = pymysql.connect(
        host='mysql.east',
        user=mysql_user,
        password=mysql_pw,
        db='ubiome',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

    cur = mydb.cursor()

    cur.execute("""
    SELECT
        s.received AS sample_received,
        s.id AS sample_id,
        s.vial_barcode,
        k.kit_type,
        k.registered,
        csss.status AS sample_process_status,
        lsl.tubeId,
        spd.ssr,
        cri.id AS issue_id,
        cri.name AS issue_name
    FROM ubiome.samples AS s
    INNER JOIN ubiome.kits AS k ON k.barcode = s.kit_barcode
    INNER JOIN ubiome.clinical_samples_sequencing_status AS csss ON csss.sample = s.id
    INNER JOIN ubiome.lab_sample_loading_view AS lsl ON s.vial_barcode = lsl.tubeId
    INNER JOIN ubiome.ssr_pipelines_details AS spd ON spd.ssr = lsl.id
    INNER JOIN ubiome.clinical_report_issues_sample_loading AS crisl ON crisl.ssr = spd.ssr AND crisl.version = spd.version
    INNER JOIN ubiome.clinical_report_issues as cri ON cri.id = crisl.issue_id
    WHERE k.barcode NOT LIKE 'study-%' AND s.received > '2017-12-31' AND spd.report_status = 'pending'
    """)
    #place sql query into dataframe
    df_blocked = pd.DataFrame(cur.fetchall())

    #reports released (erica query)
    conn = psycopg2.connect(database="backend", user = pg_user, password = pg_pw, host = pg_host, port = pg_port)
    cur = conn.cursor()
    cur.execute("""
    SELECT
        o.id AS order_id,
        o.state,
        o.sample_id,
        o.order_type_id,
        flow.status AS report_status,
        flow.created_at AS report_created_at,
        o.date_approved
    FROM orders.orders_view AS o
    INNER JOIN orders.order_status_view AS flow ON flow.order_id = o.id
    WHERE flow.created_at > '2017-12-31'
    """)
    #place sql query into dataframe
    df_reports = pd.DataFrame(cur.fetchall())
    #get column headers for dataframe
    df_reports.columns = [i[0] for i in cur.description]
    conn.commit()
    conn.close()

    #report corrections
    conn = psycopg2.connect(database="backend", user = pg_user, password = pg_pw, host = pg_host, port = pg_port)
    cur = conn.cursor()
    cur.execute("""
    SELECT
        id AS result_id,
        order_id,
        status AS result_status,
        created_at AS result_created_at
    FROM orders.order_results
    WHERE created_at > '2017-12-31'
    """)
    #place sql query into dataframe
    df_results = pd.DataFrame(cur.fetchall())
    #get column headers for dataframe
    df_results.columns = [i[0] for i in cur.description]
    conn.commit()
    conn.close()

    df_kits = df_kits[df_kits['item_type_id'].isin(['32708e12-4254-4d46-933a-f44d2ed32f5f', 'd20ee363-ea4c-4411-ab71-cc68e8723670', 'b255e35e-82bf-4436-8195-6c33b0eb9615'])] #smartgut, smartjane, smartflu codes; leaving out returns
    df_kits['ship_date'] = df_kits['ship_date'].astype(dtype='datetime64[ns]')
    df_reports['report_created_at'] = df_reports['report_created_at'].astype(dtype='datetime64[ns]')
    df_results['result_created_at'] = df_results['result_created_at'].astype(dtype='datetime64[ns]')

    df_orders.to_csv('data/current/samples_reports_metrics/orders_data.csv')
    df_kits.to_csv('data/current/samples_reports_metrics/kits_data.csv')
    df_samples.to_csv('data/current/samples_reports_metrics/samples_data.csv')
    df_blocked.to_csv('data/current/samples_reports_metrics/blocked_data.csv')
    df_reports.to_csv('data/current/samples_reports_metrics/reports_data.csv')
    df_results.to_csv('data/current/samples_reports_metrics/results_data.csv')

    print('data pull complete')

def metabase_pull(metabase_user, metabase_pass, card_id, parameters):
    header = {'Content-Type': 'application/json'}
    data ={'username': metabase_user, 'password': metabase_pass}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/{0}/query/json{1}'.format(card_id, parameters)
    data = requests.post(card, headers=get_header)
    data_df = pd.DataFrame(data.json())

    # check if subdirectory exists
    # check for a file, pull timestamp off filename, check if the timestamp is
    # before now
    filepath = 'data/current/samples_reports_metrics/tat_data.csv'

    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    data_df.to_csv(filepath, index=False)

    return
