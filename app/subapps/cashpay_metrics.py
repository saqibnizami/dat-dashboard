#%%

import hvac
import os
# import sqlalchemy as db
import psycopg2
import sys
import pandas as pd
import numpy as np
import plotly.offline as pyo
import plotly.graph_objs as go

from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_table
from app import app


###############################################################################
#### CREDENTIALS 
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

###############################################################################
#### FUNCTIONS
###############################################################################

def timenow():
    '''
    Return timestamp for filename
    '''
    time = pd.datetime.now().strftime("%Y%m%d-%H%M%S")
    return time

def return_df(sql, params, name):
    '''
    Returns a dataframe from a given SQL Query string. 

    Parameters:
    sql : Query string 
    params : Parameter string.
            ex: backend_conn_str = f"host={backend_pgdata['host']} " +\
                   f"dbname={backend_pgdata['database']} " +\
                   f"user={pg_user} " +\
                   f"password={pg_pass}"
    name : String for filename
    '''
    conn = None
    try:
        conn = psycopg2.connect(params)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        # pd.DataFrame.to_csv(df, 'data/{}_returned_{}.csv'.format(name, timenow()))
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def connString(vaultdict, database):
    db = vaultdict
    conn_str = "host={} dbname={} user={} password={}".format(db['host'],
                                                             database,
                                                             db['user'],
                                                             db['pw'])
    return conn_str

def selectdata(selection):
    rr_sql = '''
    SELECT *
    FROM roadrunner.cart
    WHERE "program" = 'cash_pay_program'
    '''
    order_sql = '''
    SELECT * 
    FROM orders.orders
    WHERE "order_flow" LIKE '%cashpay%' OR "order_flow" LIKE '%cash%'
    '''

    if selection == 'roadrunner':
        rr_conn = connString(pg, 'products')
        df = return_df(rr_sql, rr_conn, "rr" )
        return df
    elif selection == 'orders':
        backend_conn = connString(pg, 'backend')
        df = return_df(order_sql, backend_conn, "orders")
        return df

def sourceRatio(source):
    sql = '''
    SELECT DATE_TRUNC('week', cart_created_date) AS cart_created_date, source, ((COUNT(DISTINCT order_id_modified) * 1.0) / COUNT(DISTINCT cart_id)) AS orders_to_cart_ratio
    FROM
    (SELECT
    	id AS cart_id,
        insurance_id,
        COALESCE(prescription_id, order_id) AS order_id_modified,
        created_at as cart_created_date,
	    program,
	    product,
	    eligibility,
	    source
    FROM roadrunner.cart_view) as base
    -- WHERE program LIKE '%cash%'
    -- [[WHERE cart_created_date >= {{cart_created_start}} AND cart_created_date < {{cart_created_end}}]]
    GROUP BY DATE_TRUNC('week', cart_created_date), source
    ORDER BY DATE_TRUNC('week', cart_created_date) DESC'''

    rr_conn = connString(pg, 'products')
    ratio_rr = return_df(sql, rr_conn, 'rr_ratio')

    _ = ratio_rr[ratio_rr['source'] == source]
    trace = go.Scatter(y = _['orders_to_cart_ratio'],
                       x = _['cart_created_date'],
                       mode = 'lines+markers',
                       name = str(source),
                       connectgaps=True
                      )
    return trace

def generateTrace(source, ident = 'id'):
    
    result = df[df['source']==source]\
                .groupby("created_at")\
                .agg({ident: pd.Series.nunique})\
                .cumsum()
    
    trace = go.Scatter(y = result[ident],
                       x = result.reset_index()['created_at'],
                       mode = 'lines+markers',
                       name = str(source),
                       connectgaps=True
                      )
    
    return trace

def totalTrace(ident = 'id'):
    result = df.groupby("created_at")\
                .agg({ident: pd.Series.nunique})\
                .cumsum()
    
    trace = go.Scatter(y = result[ident],
                       x = result.reset_index()['created_at'],
                       mode = 'lines+markers',
                       name = str(df),
                       connectgaps=True
                      )
    
    return trace

def portalbar(y):
    cts = df.groupby('source')['id','owner_id','prescription_id','order_id']\
                .count().reset_index()
    
    trace = go.Bar(y = cts[y],
                   x = cts['source']
                  )
    return trace

###############################################################################
#### VARIABLES
###############################################################################

df = selectdata('roadrunner')

# order_flows = list(df['order_flow'].unique())

y_options = ['id', 'prescription_id', 'owner_id', 'order_id']

###############################################################################
#### Components
###############################################################################
summary ='''
Cash Pay metrics can be viewed here. 
1. Use the first dropdown to select the order flow of interest.
2. Use the second dropdown to select a metric:
    >`id = every order placed`
    >
    >`owner_id = multikits taken into account, and counted as 1`
***
Use the *Questions? Contact* dropdown for support on the Cash Pay Program or
this Dashboard

__Site Event Analytics can be viewed on the 
[RoadRunner Analytics by Ian Mathew on HEAP](https://heapanalytics.com/app/dashboard/Cashpay-Dashboard-71320)__

__[Checkout Analysis by Doh Jung on Metabase](https://metabase.ubiome.io/dashboard/264?freqeuncy=week)__
'''
topcard = dbc.Card(
    [
        dbc.CardHeader("Cash Pay Program Metrics", style={'font-size':'2em'}),
        dbc.CardBody(
            [
                dbc.CardTitle("How to Use"),
                dbc.CardText(dcc.Markdown(summary))
            ])])

###############################################################################
#### NAVBAR
###############################################################################

# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem(dbc.NavLink("Dashboard Home", href="#")),
#         dbc.DropdownMenu(
#             nav=True,
#             in_navbar=True,
#             label="Questions? Contact:",
#             children=[
#                 dbc.DropdownMenuItem("Cash Pay PM: Devon Rose", 
#                                      href="mailto:devon.rose@ubiome.com"),
#                 dbc.DropdownMenuItem(divider=True),
#                 dbc.DropdownMenuItem("Dashboard Questions: Saqib Nizami", 
#                                      href="mailto:saqib.nizami@ubiome.com"),
#                 dbc.DropdownMenuItem("HEAP Analytics Questions: Ian Mathew", 
#                                      href="mailto:ian.mathew@ubiome.com"),
#                 dbc.DropdownMenuItem("Director of Analytics: Doh Jung", 
#                                      href="mailto:doh.jung@ubiome.com"),
#             ],
#         ),
#     ],
#     brand="uBiome Data Analytics Dashboards",
#     brand_href="#",
#     sticky="top",
# )
###############################################################################
#### BODY
###############################################################################

body = dbc.Container(
    [
        dbc.Row([
            dbc.Col([topcard]),
        ]),
        dbc.Row([
            dbc.Col([
                        html.H4("Selections"),
                        dcc.Dropdown(
                            options=[{'label': i, 'value': i} \
                                     for i in df['source'].unique()],
                            placeholder='Select Order Flow',
                            multi=True,
                            value=['CLINICAL','ROADRUNNER'],
                            id='flow_drop'),
                        dcc.Dropdown(
                            options=[{'label': i, 'value': i} \
                                     for i in y_options],
                            placeholder='Select Y-Axis',
                            value='order_id',
                            multi=False,
                            id='id_drop'),
                        dcc.DatePickerRange(
                            id='my-date-picker-range',
                            min_date_allowed=dt(2019, 1, 1),
                            initial_visible_month=dt(2019, 1, 1),
                            end_date=dt.now())
                    ]),
            dbc.Col([
                html.H4("Data Information"),
                html.Ul([
                    html.Li('Database: products.roadrunner.cart'),
                    html.Li(id='rr_date_range')
                ])
            ])
        ]),
        dbc.Row([
            dbc.Col([html.H4('Total Trend'),
                        dcc.Graph(id='total_trend', animate=True)
                    ])]),
        dbc.Row([
            dbc.Col([
                html.H4("Portal Trend"),
                dcc.Graph(id='portal_trend'),
            ]),
            dbc.Col([
                html.H4("Portal Breakdown"),
                dcc.Graph(id='portal_bar')
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.H4("Order to Cart Ratio by Source"),
                dcc.Graph(id='ratio_trend')
            ])
        ]),
    ], 
    className="mt-4"
)
###############################################################################
#### Initialize App
###############################################################################

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app.layout = html.Div([navbar, body])
layout = html.Div([body])


###############################################################################
#### Callbacks
###############################################################################

@app.callback(Output('portal_trend', 'figure'),
              [Input('flow_drop','value'),
              Input('id_drop','value')])
def timeline(value1, value2):
    return {'data':[generateTrace(i, value2) for i in value1],
            'layout':{'title':'Order Volume by Flow',
                      'xaxis':{'title':'Date'},
                      'yaxis':{'title':str(value2)}
                     }
           }
@app.callback(Output('total_trend', 'figure'),
              [Input('id_drop','value')])
def totalTimeline(value1):
    return {'data':[totalTrace(value1)],
            'layout':{'title':'Total Volume Trend',
                      'xaxis':{'title':'Date'},
                      'yaxis':{'title':str(value1)}
                     }
           }
@app.callback(Output('portal_bar', 'figure'), [Input('id_drop','value')])
def make_portalbar(value1):
    return {'data':[portalbar(value1)],
            'layout':{'title':'Clinical vs. RoadRunner Usage',
                      'xaxis':{'title':'Portal Source'},
                      'yaxis':{'title':'Count'}
                     }
           }
@app.callback(Output('rr_date_range', 'children'), [Input('id_drop','value')])
def df_date_range():
    return "Date Range: {} to {}".format(df['created_at'].min(), df['created_at'].max())

@app.callback(Output('ratio_trend', 'figure'), [Input('flow_drop','value')])
def ratio_timeline(value):
    return {'data':[sourceRatio(i) for i in value],
            'layout':{'title':'Orders to Cart Ratio by Source',
                      'xaxis':{'title':'Cart Created Date'},
                      'yaxis':{'title':'Orders to Cart Ratio'}
                     }
           }
    
if __name__ == "__main__":
    app.run_server()

#%%
