#%% IMPORTS ###################################################################
#
###############################################################################
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import requests
import json
import os
import hvac
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from sklearn.linear_model import LinearRegression
import time
from datetime import datetime, timedelta

from app import app

#%% DESCRIPTION ###############################################################
#
###############################################################################

description = "Checkout Analysis Dashboard"

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

metabase = client.read('secret/production/' + VAULT_ID + '/metabase/')['data']

#%% QUERY FUNCTIONS############################################################
#
###############################################################################

def metabase_pull(metabase_user, metabase_pass):
    header = {'Content-Type': 'application/json'}
    data ={'username': metabase_user, 'password': metabase_pass}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/3115/query/json'
    data = requests.post(card, headers=get_header)
    data_df = pd.DataFrame(data.json())

    # check if subdirectory exists
    # check for a file, pull timestamp off filename, check if the timestamp is
    # before now
    filepath = 'data/current/checkout_analysis/orders_data.csv'

    parent = os.path.dirname(filepath)
    os.makedirs(parent, exist_ok=True)
    data_df.to_csv(filepath, index=False)

    return

#%% HELPER FUNCTIONS ##########################################################
#
###############################################################################
def filter_dataframe(cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = pd.read_csv('data/current/checkout_analysis/orders_data.csv', parse_dates=['cart_created_date'])

    #start and end date filter
    dff = df[(df['cart_created_date'] >= pd.Timestamp(datetime.strptime(cart_start_date, '%Y-%m-%d').date())) & (df['cart_created_date'] < (datetime.strptime(cart_end_date, '%Y-%m-%d').date()) + timedelta(days=1))]

    #product filter
    if (product != 'all'):
        dff = dff[dff['product'] == product]

    return dff

#%% CHARTING FUNCTIONS ##########################################################
#
###############################################################################
def data_df_orders_by_source(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'day'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).order_id_modified.nunique().reset_index()
    elif(frequency == 'week'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W'), 'source']).order_id_modified.nunique().reset_index()
    elif(frequency == 'month'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='M'), 'source']).order_id_modified.nunique().reset_index()

    return df

def data_df_orders_by_program(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'day'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'program_category']).order_id_modified.nunique().reset_index()
    elif(frequency == 'week'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W'), 'program_category']).order_id_modified.nunique().reset_index()
    elif(frequency == 'month'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='M'), 'program_category']).order_id_modified.nunique().reset_index()

    return df

#%% PULL ORDERS DATA ##########################################################
#
###############################################################################

try:
    df_orders = pd.read_csv('data/current/checkout_analysis/orders_data.csv', parse_dates=['cart_created_date'])
except:
    metabase_pull(metabase['user'], metabase['pass'])
    df_orders = pd.read_csv('data/current/checkout_analysis/orders_data.csv', parse_dates=['cart_created_date'])

#%% LAYOUT ############################################################
#
###############################################################################
title = 'Checkout Analysis Dashboard'
functionality_description = 'First iteration of Checkout Analyis Dashboard. Data is pulled hourly, and all dates/times are in UTC.'
layout = html.Div([
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
            )]),
    dbc.Tabs([
            dbc.Tab(
            [
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Frequency:'),
                            dcc.Dropdown(
                                id='frequency_dropdown_state_ca',
                                options=[
                                    {'label': 'Day', 'value': 'day'},
                                    {'label': 'Week', 'value': 'week'},
                                    {'label': 'Month', 'value': 'month'}
                                ],
                                value='week',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_ca', n_clicks=0, children='Submit')
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Carts Created Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_ca',
                            min_date_allowed='2018-01-01',
                            max_date_allowed=datetime.now().date().strftime('%Y-%m-%d'),
                            start_date='2019-01-01',
                            end_date=datetime.now().date().strftime('%Y-%m-%d')
                            ),
                        ],
                        md=2.5,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_ca',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'SmartGut', 'value': 'SMART_GUT'},
                                    {'label': 'SmartJane', 'value': 'SMART_JANE'},
                                    {'label': 'SmartFlu', 'value': 'SMART_FLU'}
                                ],
                                value='all',
                                style={'marginBottom': 10}
                            )
                        ],
                        md=2,
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6('Data Pulled', style = {'marginBottom':0}),
                        html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime('data/current/checkout_analysis/orders_data.csv')))),
                        html.Div(id='orders_summary')
                    ])
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='orders_by_source'),
                            dcc.Graph(
                                id='orders_by_source_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(id='orders_by_source_table')
                        ],
                        md=6
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='orders_by_program'),
                            dcc.Graph(
                                id='orders_by_program_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(id='orders_by_program_table')
                        ],
                        md=6
                    )
                ]),
            ], label=''),
    ]),
    dcc.Interval(
    id='interval_component_ca',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    )
])

@app.callback(
Output('orders_by_source_chart', 'figure'),
[Input('submit_button_ca', 'n_clicks')],
[State('frequency_dropdown_state_ca', 'value'),
State('date_picker_range_state_ca', 'start_date'),
State('date_picker_range_state_ca', 'end_date'),
State('product_dropdown_state_ca', 'value')])
def update_orders_by_source_chart(submit_button, frequency, start_date, end_date, product):
    dff = filter_dataframe(start_date, end_date, product)

    df_orders_by_source = data_df_orders_by_source(dff, frequency)

    trace1 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL'].order_id_modified,
        mode='lines',
        name='Clinical',
        stackgroup='one'
    )
    trace2 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_K'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_K'].order_id_modified,
        mode='lines',
        name='Clinical K',
        stackgroup='one'
    )
    trace3 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_UPGRADES'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_UPGRADES'].order_id_modified,
        mode='lines',
        name='Clinical Upgrades',
        stackgroup='one'
    )
    trace4 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_BIOBANKED'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_BIOBANKED'].order_id_modified,
        mode='lines',
        name='Clinical Biobanked',
        stackgroup='one'
    )
    trace5 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'ROADRUNNER'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'ROADRUNNER'].order_id_modified,
        mode='lines',
        name='RoadRunner',
        stackgroup='one'
    )

    return go.Figure(
        data=[
            trace1, trace2, trace3, trace4, trace5
        ],
        layout=go.Layout(
            title='Kit 1 Orders by Source',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': '# Kit 1 Orders'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('orders_by_source_table', 'children'),
[Input('submit_button_ca', 'n_clicks')],
[State('frequency_dropdown_state_ca', 'value'),
State('date_picker_range_state_ca', 'start_date'),
State('date_picker_range_state_ca', 'end_date'),
State('product_dropdown_state_ca', 'value')])
def update_orders_by_source_table(submit_button, frequency, start_date, end_date, product):
    dff = filter_dataframe(start_date, end_date, product)

    df_orders_by_source = data_df_orders_by_source(dff, frequency)

    df_orders_by_source = df_orders_by_source.pivot(index='cart_created_date', columns='source', values='order_id_modified').reset_index()

    return [
        html.H6('Kit 1 Orders by Source'),
        dash_table.DataTable(
            data=df_orders_by_source.to_dict('rows'),
            columns=[
                {'name': i, 'id': i} for i in df_orders_by_source.columns
            ]
        ),
    ]


@app.callback(
Output('orders_by_program_chart', 'figure'),
[Input('submit_button_ca', 'n_clicks')],
[State('frequency_dropdown_state_ca', 'value'),
State('date_picker_range_state_ca', 'start_date'),
State('date_picker_range_state_ca', 'end_date'),
State('product_dropdown_state_ca', 'value')])
def update_orders_by_program_chart(submit_button, frequency, start_date, end_date, product):
    dff = filter_dataframe(start_date, end_date, product)

    df_orders_by_program = data_df_orders_by_program(dff, frequency)

    trace1 = dict(
        x=df_orders_by_program[df_orders_by_program['program_category'] == '1. pap'].cart_created_date,
        y=df_orders_by_program[df_orders_by_program['program_category'] == '1. pap'].order_id_modified,
        mode='lines',
        name='PAP',
        stackgroup='one'
    )
    trace2 = dict(
        x=df_orders_by_program[df_orders_by_program['program_category'] == '2. cash_pay_program'].cart_created_date,
        y=df_orders_by_program[df_orders_by_program['program_category'] == '2. cash_pay_program'].order_id_modified,
        mode='lines',
        name='Cash Pay Program',
        stackgroup='one'
    )
    trace3 = dict(
        x=df_orders_by_program[df_orders_by_program['program_category'] == '3. patient_responsibility'].cart_created_date,
        y=df_orders_by_program[df_orders_by_program['program_category'] == '3. patient_responsibility'].order_id_modified,
        mode='lines',
        name='Patient Responsibility',
        stackgroup='one'
    )
    trace4 = dict(
        x=df_orders_by_program[df_orders_by_program['program_category'] == '4. legacy_or_misc_programs'].cart_created_date,
        y=df_orders_by_program[df_orders_by_program['program_category'] == '4. legacy_or_misc_programs'].order_id_modified,
        mode='lines',
        name='Legacy or Misc. Programs',
        stackgroup='one'
    )

    return go.Figure(
        data=[
            trace1, trace2, trace3, trace4
        ],
        layout=go.Layout(
            title='Kit 1 Orders by Program',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': '# Kit 1 Orders'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('orders_by_program_table', 'children'),
[Input('submit_button_ca', 'n_clicks')],
[State('frequency_dropdown_state_ca', 'value'),
State('date_picker_range_state_ca', 'start_date'),
State('date_picker_range_state_ca', 'end_date'),
State('product_dropdown_state_ca', 'value')])
def update_orders_by_program_table(submit_button, frequency, start_date, end_date, product):
    dff = filter_dataframe(start_date, end_date, product)

    df_orders_by_program = data_df_orders_by_program(dff, frequency)

    df_orders_by_program = df_orders_by_program.pivot(index='cart_created_date', columns='program_category', values='order_id_modified').reset_index()

    return [
        html.H6('Kit 1 Orders by Program'),
        dash_table.DataTable(
            data=df_orders_by_program.to_dict('rows'),
            columns=[
                {'name': i, 'id': i} for i in df_orders_by_program.columns
            ]
        ),
    ]
