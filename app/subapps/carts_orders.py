#%%


###############################################################################
#### IMPORTS 
###############################################################################


import os
from datetime import datetime as dt
from datetime import timedelta

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
import sqlalchemy as db
from dash.dependencies import Input, Output, State

from app import app, config

#%%
###############################################################################
#### DESCRIPTION 
###############################################################################

description = "Key Operations Metrics Dashboard for Carts, Orders, and Kits"

#%%
###############################################################################
#### CREDENTIALS 
###############################################################################

phi = config.get('phi')
pg = config.get('pg')

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
    filepath = 'app/data/current/{}/{}_{}_pull_at_{}.csv'.format(foldername,
                                                            tablename,
                                                            database,
                                                            now)
    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    df.to_csv(filepath, index=False)

    return df
#%%
# path = os.path.join(os.getcwd(), 'apps')
cart_no = SQLtoDF(sqlfile='app/queries/cart_number.sql',
                  database="products",
                  creds=pg,
                  driver='postgres',
                  foldername='mko',
                  tablename='carts')

# orders_to_cart = SQLtoDF(sqlfile=path + '/orders_to_cart_ratio.sql',
#                          queryaddition=" ",
#                          database='products')

# order_state = SQLtoDF(sqlfile=path + '/order_state_count.sql',
#                       queryaddition=" ",
#                       database='backend')

#%%
###############################################################################
#### APP
###############################################################################



# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# app.scripts.config.serve_locally = False

PAGE_SIZE = 15

# app.config['suppress_callback_exceptions'] = True


#%%
###############################################################################
#### CHARTING FUNCTIONS
###############################################################################



# cart_no.head(20)
#- generate traces for cart number

# def cartNoTrace(df, program):
#     df = df[df['program'] == program]
#     trace = go.Scatter(y = df['cart_number'],
#                        x = df['cart_created_date'],
#                        mode = 'lines+markers',
#                        name = str(program),
#                        connectgaps=True,
#                        fill='tozeroy')
#     return trace


#%%
###############################################################################
#### SUMMARY
###############################################################################



summary ='''
This dashboard is a part of efforts to standardize operations metrics. 

The focus of this page is to consolidate reporting on carts, orders, and kits.

'''
topcard = dbc.Card(
    [
        # dbc.CardHeader("Key Operations Metrics", style={'font-size':'2em'}),
        dbc.CardBody(
            [
                # dbc.Button("Click here to expand more information on this dashboard", 
                #             id="collapse-button", className="mb-3"),
                # dbc.Collapse(
                #     [
                #         dbc.CardTitle("How to Use"),
                #         dbc.CardText(dcc.Markdown(summary))
                #     ],
                #     id='collapse',
                #     is_open=False
                # ),
                dbc.Row(
                    [
                        dbc.Col([
                            html.H5('Date Selection'),
                            dcc.DatePickerRange(
                                id='cart-no-date-picker',
                                min_date_allowed=dt(2019, 1, 1),
                                initial_visible_month=dt(2019, 1, 1),
                                end_date="{:%Y-%m-%d}".format(dt.now()),
                                start_date="{:%Y-%m-%d}".format(dt.now()-timedelta(30))
                                )
                            ]
                        )
                    ]
                ),
            ])])


#%%
###############################################################################
#### NAVBAR
###############################################################################


# navbar = html.Div([
#     dbc.NavbarSimple(
#     children=[
#         dbc.NavItem(dbc.NavLink("", href="/")),
#         dbc.DropdownMenu(
#             nav=True,
#             in_navbar=True,
#             label="Questions? Contact:",
#             children=[
#                 dbc.DropdownMenuItem("Data Analytics Team"),
#                 dbc.DropdownMenuItem(divider=True),
#                 dbc.DropdownMenuItem("Saqib Nizami", 
#                                      href="mailto:saqib.nizami@ubiome.com"),
#                 dbc.DropdownMenuItem("Andrew Cho", 
#                                      href="mailto:andrew.cho@ubiome.com"),
#                 dbc.DropdownMenuItem("Ian Mathew", 
#                                      href="mailto:ian.mathew@ubiome.com"),
#                 dbc.DropdownMenuItem("Doh Jung", 
#                                      href="mailto:doh.jung@ubiome.com"),
#             ],
#         ),
#     ],
#     brand="uBiome Data Analytics Dashboards",
#     brand_href="/",
#     sticky="top",
#     brand_style={'font-size':'1em'},
#     dark=True,
#     color='dark'
# )])


#%%
###############################################################################
#### TABS
###############################################################################



cart_tab = dbc.Col([
    dbc.Row([
        dbc.Col([
            html.H5("Overall Cart Totals"),
            dbc.CardGroup(id='cart-totals-card', style={'text-align':'center'}),
            dcc.Graph(id='cart-no-total-graph')
        ])
    ]),
    dbc.Button("Click to View Cart Numbers by Program", 
                id="cart-no-button",color='primary',outline=True),
    dbc.Collapse(
        [
            dbc.Row([
                # html.H4("View Cart Numbers by Program"),
                dbc.Col([
                            dcc.Dropdown(
                                options=[{'label': i, 'value': i} \
                                        for i in cart_no['program'].unique()],
                                placeholder='Select Program',
                                value='cash_pay_program',
                                multi=False,
                                id='cart-program-dd')
                        ]),
                ]),
            dbc.Row([
                dbc.Col([html.Div(id='cart-no-table-col')]),
                dbc.Col([dcc.Graph(id='cart-no-graph')])
        ])
        ], id='cart-no-collapse', is_open=True
    )])

# orders_tab = dbc.Col([
#     dbc.Row([
#         dbc.Col([
#             html.H5("Overall Order Totals"),
#             dbc.CardGroup(id='order-totals-card', style={'text-align':'center'}),
#             dcc.Graph(id='order-no-total-graph')
#         ])
#     ]),
#     dbc.Button("Click to View order Numbers by Program", 
#                 id="order-no-button",color='primary',outline=True),
#     dbc.Collapse(
#         [
#             dbc.Row([
#                 # html.H4("View order Numbers by Program"),
#                 dbc.Col([
#                             dcc.Dropdown(
#                                 options=[{'label': i, 'value': i} \
#                                         for i in order_no['program'].unique()],
#                                 placeholder='Select Program',
#                                 value='cash_pay_program',
#                                 multi=False,
#                                 id='order-program-dd')
#                         ]),
#                 ]),
#             dbc.Row([
#                 dbc.Col([html.Div(id='order-no-table-col')]),
#                 dbc.Col([dcc.Graph(id='order-no-graph')])
#         ])
#         ], id='order-no-collapse', is_open=True
#     )])

# tabs = dbc.Tabs(
#     [
#         dbc.Tab(cart_tab, label='Cart Metrics'),
#         dbc.Tab("Orders Metrics Coming Soon!", label="Order Metrics"),
#         dbc.Tab("Kit Metrics Coming Soon!", label="Kit Metrics"),
#         dbc.Tab("Funnel", label="Funnel")
#     ]
# )



###############################################################################
#### APP LAYOUT
###############################################################################



# body = \
#     dbc.Container([
#             topcard,
#             tabs
#             # dbc.Card([dbc.CardBody([tabs])])
#             ])
    
# REMOVED NAVBAR FROM LAYOUT. NAVBAR IS NOW IN INDEX

layout = html.Div([topcard,cart_tab])



###############################################################################
#### CART TAB CALLBACKS
###############################################################################




@app.callback(
    Output('cart-totals-card','children'),
    [Input('cart-no-date-picker', 'start_date'),
    Input('cart-no-date-picker', 'end_date')]
)
def cartTotalscard(s, e):
    mask = (cart_no['cart_created_date'] > s) & (cart_no['cart_created_date'] <= e)
    cdf =cart_no[mask]
    cdf_sum = cdf.groupby(['program']).agg({'cart_number':'sum'}).reset_index()
    totals =[(i, cdf_sum[cdf_sum['program'] == i].iloc[0]['cart_number']) \
        for i in cdf_sum['program']]
    cards = []
    for x in totals:
        card = \
        dbc.Card(
        [
            # dbc.CardHeader("{}".format(x[0])),
            dbc.CardBody(
                [
                    dbc.CardTitle("{}".format(x[1]), style={'font-size':'2em'}),
                    dbc.CardText("{}".format(x[0].replace("_"," "))),
                ]
            ),
        ])
        cards.append(card)
    return cards

@app.callback(Output('cart-no-total-graph', 'figure'),
             [Input('cart-no-date-picker', 'start_date'),
              Input('cart-no-date-picker', 'end_date')])
def cartTotalGraph(start, end):
    df = cart_no
    mask = (df['cart_created_date'] > start) & (df['cart_created_date'] <= end)
    df = df[mask]

    def totalTrace(df, program):
        df = df[df['program'] == program]
        trace = go.Scatter(y = df['cart_number'],
                        x = df['cart_created_date'],
                        mode = 'lines+markers',
                        name = str(program),
                        connectgaps=True,
                        fill='tozeroy')
        return trace

    graph ={
        'data':[totalTrace(df, i) for i in df['program'].unique()],
        'layout':{'title':'Cart Numbers by Program',
                  'xaxis':{'title':'Date','showgrid':False},
                  'yaxis':{'title':'Cart Number', 'showgrid':False}
                  }
                }
    return graph

# @app.callback(
#     Output("collapse", "is_open"),
#     [Input("collapse-button", "n_clicks")],
#     [State("collapse", "is_open")],
#     )
# def toggle_collapse(n, is_open):
#     if n:
#         return not is_open
#     return is_open

@app.callback(
    Output("cart-no-collapse", "is_open"),
    [Input("cart-no-button", "n_clicks")],
    [State("cart-no-collapse", "is_open")],
    )
def toggle_cart_no_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output('cart-no-table-col', 'children'),
    [Input('cart-program-dd', 'value')]
    )
def chooseCartProgram(value):
    df = cart_no
    df = df[df['program'] == str(value)]
    table = dash_table.DataTable(
        id='cart-no-table',
        columns=[{'name': i, 'id':i} for i in df.columns],
        data=df.to_dict("rows"),
        pagination_settings={'current_page': 0, 'page_size': PAGE_SIZE},
        pagination_mode='fe'
        )
    return table

@app.callback(Output('cart-no-graph', 'figure'),
             [Input('cart-program-dd', 'value'),
              Input('cart-no-date-picker', 'start_date'),
              Input('cart-no-date-picker', 'end_date')])
def cartNoGraph(value, start, end):
    df = cart_no
    df = df[df['program'] == str(value)]
    mask = (df['cart_created_date'] > start) & (df['cart_created_date'] <= end)
    df = df[mask]
    trace = go.Scatter(y = df['cart_number'],
                       x = df['cart_created_date'],
                       mode = 'lines+markers',
                       connectgaps=True,
                       fill='tozeroy')
    graph ={
        'data':[trace],
        'layout':{'title':'Order Volume by Flow',
                  'xaxis':{'title':'Date',
                            'showgrid':False},
                  'yaxis':{'title':str(value),
                            'showgrid':False}
                  }
                }
    return graph

# if __name__ == "__main__":
#     app.run_server(debug=False)
#%%
###############################################################################
#### DEVELOP ORDERS TAB
###############################################################################

# order_state = SQLtoDF(sqlfile='apps/order_state_count.sql', 
#                         queryaddition="'day'", 
#                         database='backend')
# display(order_state.shape, order_state.head())
# #%%
# order_state['created'] = pd.to_datetime(order_state['created'])
# order_state.set_index('created').resample('W').sum().sort_index(ascending=False)
#%% [markdown]
###############################################################################
#### DEVELOP FUNNEL CHART
###############################################################################

# Totals Needed for the chart:
# 1. Cart Number
# 2. Orders Number
# 3. Kits Sent Number
# 4. Kits Returned Number




# #%%
# kits = SQLtoDF(sqlfile="apps/kit_query.sql", database="backend" )
# display(kits.shape, kits.head())

# #%%
# os.getcwd()


#%%
