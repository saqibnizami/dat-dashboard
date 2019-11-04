#%% IMPORTS ###################################################################
#
###############################################################################
import calendar
import json
import os
import time
from datetime import datetime

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import feather
import pandas as pd
import plotly.graph_objs as go
import requests
from dash.dependencies import Input, Output, State
from dateutil.relativedelta import relativedelta
# adding flask-caching for dataset
from flask_caching import Cache
from sklearn.linear_model import LinearRegression

from app import app, config

#%% CACHE #####################################################################
# using filesystem cache
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
TIMEOUT = 60
#%% DESCRIPTION ###############################################################
#
###############################################################################

description = "Orders Dashboard"

metabase = config.get('metabase')

#%% QUERY FUNCTIONS############################################################
#
###############################################################################

def metabase_pull(metabase_user, metabase_pass):
    header = {'Content-Type': 'application/json'}
    data ={'username': metabase_user, 'password': metabase_pass}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/2922/query/json'
    data = requests.post(card, headers=get_header)
    data_df = pd.DataFrame(data.json())

    data_df['order_created_at'] = pd.to_datetime(data_df['order_created_at'])
    data_df['order_created_at'] = data_df['order_created_at'].apply(lambda x: x.replace(tzinfo=None))

    # *Saqib: I added the following to check if the parent folder for your
    # * filpath exists and to make it if it doesn't:

    filepath = 'app/data/current/orders/orders_data.feather'
    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    data_df.to_feather(filepath)

#%% PULL ORDERS DATA ##########################################################
#
###############################################################################

try:
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')
except:
    # TODO: Move this to a scheduled data pull
    metabase_pull(metabase['user'], metabase['pass'])

#%% HELPER FUNCITONS ##########################################################
#
###############################################################################

def month_dates():
    current_year = datetime.now().year
    current_month = datetime.now().month
    if (current_month == 1):
        previous_year = current_year - 1
        previous_month = 12
    else:
        previous_year = current_year
        previous_month = current_month - 1

    #current month
    days_in_current_month = calendar.monthrange(current_year, current_month)[1]
    first_day_current_month = datetime(current_year, current_month, 1)
    last_day_current_month = datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1])

    #previous month
    days_in_previous_month = calendar.monthrange(previous_year, previous_month)
    first_day_previous_month = datetime(previous_year, previous_month, 1)
    last_day_previous_month = datetime(previous_year, previous_month, calendar.monthrange(previous_year, previous_month)[1])

    return first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month

#data manip functions
def data_for_orders_mtd_chart(df_orders, product, kit_type, upgrade_type):
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')
    #identify current and previous month start and end dates
    first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month = month_dates()

    df_orders_filtered = df_orders
    #Product Filtering
    if product != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['code'] == product]

    #Kit Filtering
    if kit_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['kit_type'] == kit_type]

    #Upgrade Filtering
    if upgrade_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['upgrade_type'] == upgrade_type]

    #previous month
    df_orders_previous_month = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_previous_month) & (df_orders_filtered['order_created_at'] < last_day_previous_month + relativedelta(days=1))]
    df_orders_previous_month.index = df_orders_previous_month['order_created_at']
    df_orders_previous_month_daily = df_orders_previous_month.resample('D').order_id.nunique()
    df_orders_previous_month_daily.index = df_orders_previous_month_daily.index.day
    df_orders_previous_month = df_orders_previous_month_daily.cumsum()

    #current month
    df_orders_current_month = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_current_month) & (df_orders_filtered['order_created_at'] < last_day_current_month + relativedelta(days=1))]
    df_orders_current_month.index = df_orders_current_month['order_created_at']
    df_orders_current_month_daily = df_orders_current_month.resample('D').order_id.nunique()
    df_orders_current_month_daily.index = df_orders_current_month_daily.index.day
    while (len(df_orders_current_month_daily) < datetime.now().day):
        df_orders_current_month_daily = df_orders_current_month_daily.append(pd.Series([0]), ignore_index=True)
    df_orders_current_month = df_orders_current_month_daily.cumsum()
    #catch exception for first day of month
    try:
        if min(df_orders_current_month.index) < 1:
            df_orders_current_month.index += 1
        if min(df_orders_current_month_daily.index) < 1:
            df_orders_current_month_daily.index += 1
    except: pass

    #combine previous and current into same dataframe
    df_orders_mtd = pd.concat([df_orders_previous_month, df_orders_current_month, df_orders_current_month_daily, df_orders_previous_month_daily], axis=1)
    df_orders_mtd.columns = [['previous_month_count', 'current_month_count', 'current_month_daily', 'previous_month_daily']]
    df_orders_mtd['previous_month_count'] = df_orders_mtd['previous_month_count'].fillna(0)
    df_orders_mtd['previous_month_daily'] = df_orders_mtd['previous_month_daily'].fillna(0)

    #linreg trendline
    #catch exception for first day of month
    try:
        if len(df_orders_mtd['current_month_count'] >= 2):
            linear_regressor = LinearRegression()
            linear_regressor.fit(df_orders_mtd['current_month_count'].dropna().index.values.reshape(-1, 1), df_orders_mtd['current_month_count'].dropna().unstack().values.reshape(-1,1))
            Y_pred = linear_regressor.predict(df_orders_mtd['current_month_count'].index[:last_day_current_month.day].values.reshape(-1,1))
            predicted_values = pd.Series(Y_pred.flatten()).round(0)
            predicted_values.index = predicted_values.index + 1
            predicted_values = predicted_values[df_orders_mtd[df_orders_mtd['current_month_count'].isnull().any(axis=1)].index[0] - 1:]
            df_orders_mtd['predicted_count'] = predicted_values
        else: df_orders_mtd['predicted_count'] = ''
    except: df_orders_mtd['predicted_count'] = ''

    return df_orders_mtd

def data_for_orders_hod_chart(df_orders, product, kit_type, upgrade_type):
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')
    #identify current and previous month start and end dates
    first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month = month_dates()

    df_orders_filtered = df_orders
    #Product Filtering
    if product != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['code'] == product]

    #Kit Filtering
    if kit_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['kit_type'] == kit_type]

    #Upgrade Filtering
    if upgrade_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['upgrade_type'] == upgrade_type]

    #previous month
    df_orders_previous_month = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_previous_month) & (df_orders_filtered['order_created_at'] < last_day_previous_month + relativedelta(days=1))]
    df_orders_previous_month['order_created_hour'] = df_orders_previous_month.order_created_at.dt.hour
    df_orders_previous_month_hourly = df_orders_previous_month.groupby('order_created_hour').order_id.nunique()

    #current month
    df_orders_current_month = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_current_month) & (df_orders_filtered['order_created_at'] < last_day_current_month + relativedelta(days=1))]
    df_orders_current_month['order_created_hour'] = df_orders_current_month.order_created_at.dt.hour
    df_orders_current_month_hourly = df_orders_current_month.groupby('order_created_hour').order_id.nunique()

    #combine previous and current into same dataframe
    df_orders_hod = pd.concat([ df_orders_previous_month_hourly, df_orders_current_month_hourly], axis=1)
    df_orders_hod.columns = [['previous_month_hourly', 'current_month_hourly']]

    return df_orders_hod


#%% LAYOUT ############################################################
#
###############################################################################
title = 'Orders Dashboard'
functionality_description = 'First iteration of Orders Dashboard. Data is pulled hourly, and all dates/times are in UTC.'
topcard = \
    dbc.Card([
        dbc.CardHeader(title, style={'font-size':'2em'}),
        dbc.CardBody(
            [
                dbc.Button("Click here for more information on this dashboard", id="collapse_button_o", className="mb-3"),
                dbc.Collapse(
                    [
                        dbc.CardText([
                            html.P(children=functionality_description),
                        ])
                    ],
                    id='collapse_o',
                    is_open=False
                )
            ]
            )])
mtd_summary = dbc.Col([
    dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_o_summary',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'SmartGut', 'value': 'smart_gut'},
                                    {'label': 'SmartJane', 'value': 'smart_jane'},
                                    {'label': 'SmartFlu', 'value': 'smart_flu'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='filter_button_o_summary', n_clicks=0, children='Filter')
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Kit Type:'),
                            dcc.Dropdown(
                                id='kit_type_dropdown_state_o_summary',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Single Kit', 'value': 'singlekit'},
                                    {'label': 'Multi Kit', 'value': 'multikit'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Upgrade:'),
                            dcc.Dropdown(
                                id='upgrade_dropdown_state_o_summary',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Upgrade', 'value': 'upgrade'},
                                    {'label': 'Non-Upgrade', 'value': 'nonupgrade'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    )
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6('Data Pulled', style = {'marginBottom':0}),
                        html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime('app/data/current/orders/orders_data.feather')))),
                        html.Div(id='orders_summary')
                    ])
                ])
])
mtd_summary_tab = dbc.Tab([mtd_summary], label='Orders MTD Summary')
mtd_charts_tab = \
    dbc.Tab(
            [
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_o_chart',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'SmartGut', 'value': 'smart_gut'},
                                    {'label': 'SmartJane', 'value': 'smart_jane'},
                                    {'label': 'SmartFlu', 'value': 'smart_flu'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='filter_button_o_chart', n_clicks=0, children='Filter')
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Kit Type:'),
                            dcc.Dropdown(
                                id='kit_type_dropdown_state_o_chart',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Single Kit', 'value': 'singlekit'},
                                    {'label': 'Multi Kit', 'value': 'multikit'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Upgrade:'),
                            dcc.Dropdown(
                                id='upgrade_dropdown_state_o_chart',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Upgrade', 'value': 'upgrade'},
                                    {'label': 'Non-Upgrade', 'value': 'nonupgrade'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.H6('Data Pulled', style = {'marginBottom':0}),
                            html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime('app/data/current/orders/orders_data.feather')))),
                        ],
                        md=6
                    ),
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            dcc.Graph(
                                id='orders_mtd_chart',
                                style={'height': 500, 'marginBottom': 20},
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(
                                id='orders_hod_chart',
                                style={'height': 500, 'marginBottom': 20},
                            )
                        ],
                        md=6
                    ),
                ]),
            ], label='Orders MTD Charts')

tabs = dbc.Tabs([ mtd_summary_tab, mtd_charts_tab ])


layout = html.Div([
    # topcard,
    tabs,
    dcc.Interval(
    id='interval_component_o',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    )
])



#############

@app.callback(
Output("collapse_o", "is_open"),
[Input("collapse_button_o", "n_clicks")],
[State("collapse_o", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output('orders_summary','children'),
[Input('filter_button_o_summary', 'n_clicks')],
[State('product_dropdown_state_o_summary', 'value'),
State('kit_type_dropdown_state_o_summary', 'value'),
State('upgrade_dropdown_state_o_summary', 'value')])
def orders_card(submit_button, product, kit_type, upgrade_type):
    t0 = time.time()
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')

    orders_cards_current = []
    orders_cards_previous = []

    #date variables
    current_day = pd.Timestamp(datetime.now().date())
    first_day_current_month = month_dates()[0]
    current_day_previous_month = current_day - relativedelta(months=1)
    first_day_previous_month = month_dates()[2]

    df_orders_filtered = df_orders
    #Product Filtering
    if product != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['code'] == product]

    #Kit Filtering
    if kit_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['kit_type'] == kit_type]

    #Upgrade Filtering
    if upgrade_type != 'all':
        df_orders_filtered = df_orders_filtered[df_orders_filtered['upgrade_type'] == upgrade_type]

    #Count of Orders MTD
    count_orders_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_current_month) & (df_orders_filtered['order_created_at'] < (current_day + relativedelta(days=1)))].order_id.nunique()
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Current MTD # Orders", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_orders_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_current.append(card)

    #Count of Upgrades MTD
    count_upgrades_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_current_month) & (df_orders_filtered['order_created_at'] < (current_day + relativedelta(days=1))) & (df_orders_filtered['upgrade_type'] == 'upgrade')].order_id.nunique() #change date
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Current MTD # Upgrades", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_upgrades_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_current.append(card)

    #Count of Kit 1 Orders MTD
    count_kit_1_orders_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_current_month) & (df_orders_filtered['order_created_at'] < (current_day + relativedelta(days=1)))].kit_1_id.nunique()
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Current MTD # Kit 1 Orders", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_kit_1_orders_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_current.append(card)

    #Count of Orders Previous MTD
    count_orders_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_previous_month) & (df_orders_filtered['order_created_at'] < current_day_previous_month + relativedelta(days=1))].order_id.nunique() #change date
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Previous MTD # Orders", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_orders_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_previous.append(card)

    #Count of Upgrades Previous MTD
    count_upgrades_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_previous_month) & (df_orders_filtered['order_created_at'] < current_day_previous_month + relativedelta(days=1)) & (df_orders_filtered['upgrade_type'] == 'upgrade')].order_id.nunique() #change date
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Previous MTD # Upgrades", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_upgrades_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_previous.append(card)

    #Count of Kit 1 Orders Previous MTD
    count_kit_1_orders_mtd = df_orders_filtered[(df_orders_filtered['order_created_at'] >= first_day_previous_month) & (df_orders_filtered['order_created_at'] < current_day_previous_month + relativedelta(days=1))].kit_1_id.nunique() #change date
    card = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.CardHeader("Previous MTD # Kit 1 Orders", style={'font-size':'1em'}),
                dbc.CardText("{}".format(count_kit_1_orders_mtd), style={'font-size':'2em'}),
            ]
        ),
    ])
    orders_cards_previous.append(card)

    t1 = time.time()
    print('orders cards', t1-t0)

    return dbc.CardColumns(orders_cards_current, style={'text-align':'center'}), dbc.CardColumns(orders_cards_previous, style={'text-align':'center'})

@app.callback(
Output('orders_mtd_chart', 'figure'),
[Input('filter_button_o_chart', 'n_clicks')],
[State('product_dropdown_state_o_chart', 'value'),
State('kit_type_dropdown_state_o_chart', 'value'),
State('upgrade_dropdown_state_o_chart', 'value')])
def update_orders_mtd_chart(submit_button, product, kit_type, upgrade_type):
    t0 = time.time()
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')

    df_orders_mtd = data_for_orders_mtd_chart(df_orders, product, kit_type, upgrade_type)

    t1 = time.time()
    print('orders mtd chart', t1-t0)

    return go.Figure(
        data=[
            go.Scatter(
                x=df_orders_mtd.index,
                y=df_orders_mtd.iloc[:,0],
                mode='lines',
                name='Previous Month to Date',
                marker=go.scatter.Marker(
                    color='#0098c8'
                )
            ),
            go.Scatter(
                x=df_orders_mtd.index,
                y=df_orders_mtd.iloc[:,1],
                mode='lines',
                name='Current Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            ),
            go.Scatter(
                x=df_orders_mtd.index,
                y=df_orders_mtd.iloc[:,2],
                mode='lines',
                name='Daily Count',
                marker=go.scatter.Marker(
                    color='#000000'
                )
            ),
            go.Scatter(
                x=df_orders_mtd.index,
                y=df_orders_mtd.iloc[:,4],
                mode='markers',
                name='Predicted Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            )
        ],
        layout=go.Layout(
            title='Orders Month to Date',
            xaxis={'title': 'Day of Month'},
            yaxis={'title': '# Orders'},
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('orders_hod_chart', 'figure'),
[Input('filter_button_o_chart', 'n_clicks')],
[State('product_dropdown_state_o_chart', 'value'),
State('kit_type_dropdown_state_o_chart', 'value'),
State('upgrade_dropdown_state_o_chart', 'value')])
def update_orders_hod_chart(submit_button, product, kit_type, upgrade_type):
    t0 = time.time()
    df_orders = feather.read_dataframe('app/data/current/orders/orders_data.feather')

    df_orders_hod = data_for_orders_hod_chart(df_orders, product, kit_type, upgrade_type)

    t1 = time.time()
    print('orders hod', t1-t0)

    return go.Figure(
        data=[
            go.Scatter(
                x=df_orders_hod.index,
                y=df_orders_hod.iloc[:,0],
                mode='lines',
                name='Previous Month to Date Hour of Day',
                marker=go.scatter.Marker(
                    color='#0098c8'
                )
            ),
            go.Scatter(
                x=df_orders_hod.index,
                y=df_orders_hod.iloc[:,1],
                mode='lines',
                name='Current Month to Date Hour of Day',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            )
        ],
        layout=go.Layout(
            title='Orders Month to Date Hour of Day',
            xaxis={'title': 'Hour'},
            yaxis={'title': '# Orders'},
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('date_of_pull_o', 'children'),
[Input('interval_component_o', 'n_intervals')])
def update_data(n):
    metabase_pull(metabase['user'], metabase['pass'])

    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime('app/data/current/orders/orders_data.feather')))
