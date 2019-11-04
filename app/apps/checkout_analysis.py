import os
import time
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from app import app, config, logger

description = "Checkout Analysis Dashboard"


class CheckoutAnalyisDAO:

    @staticmethod
    def get_orders_data():
        try:
            df_orders = pd.read_csv('~/data_pulls/checkout_analysis/orders_data.csv')
            df_orders['cart_created_date'] = pd.to_datetime(df_orders['cart_created_date'])
            df_orders['cart_created_date'] = df_orders['cart_created_date'].apply(lambda x: x.replace(tzinfo=None))

            return df_orders
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_samples_data():
        try:
            df_samples = pd.read_csv('~/data_pulls/checkout_analysis/samples_data.csv')
            df_samples['cart_created_date'] = pd.to_datetime(df_samples['cart_created_date'])
            df_samples['cart_created_date'] = df_samples['cart_created_date'].apply(lambda x: x.replace(tzinfo=None))

            return df_samples
        except Exception as e:
            logger.exception('')


metabase = config.get('metabase')

#%% HELPER FUNCTIONS ##########################################################
#
###############################################################################
def filter_dataframe(df, cart_start_date, cart_end_date, product):
    #cart start and end date filter
    dff = df[(df['cart_created_date'] >= pd.Timestamp(datetime.strptime(cart_start_date, '%Y-%m-%d').date())) & (df['cart_created_date'] < (datetime.strptime(cart_end_date, '%Y-%m-%d').date()) + timedelta(days=1))]

    #product filter
    if (product != 'All'):
        dff = dff[dff['product'] == product]

    return dff

#%% CHARTING FUNCTIONS ##########################################################
#
###############################################################################
def data_df_orders_by_source(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'Daily'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).order_id_modified.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'source']).order_id_modified.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'source']).order_id_modified.nunique().reset_index()

    return df

def data_df_orders_by_program(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'Daily'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'program_category']).order_id_modified.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'program_category']).order_id_modified.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'program_category']).order_id_modified.nunique().reset_index()

    return df

def data_df_orders_to_cart(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'Daily'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D')]).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D')]).cart_id.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left')]).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left')]).cart_id.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS')]).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS')]).cart_id.nunique().reset_index()

    df = pd.merge(df_orders, df_carts, how='outer', on=['cart_created_date'])

    df['orders_to_cart_ratio'] = df['order_id_modified']/df['cart_id']

    return df

def data_df_orders_to_cart_by_source(df, frequency):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    if(frequency == 'Daily'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).cart_id.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'source']).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'source']).cart_id.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df_orders = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'source']).order_id_modified.nunique().reset_index()
        df_carts = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'source']).cart_id.nunique().reset_index()

    df = pd.merge(df_orders, df_carts, how='outer', on=['cart_created_date', 'source'])

    df['orders_to_cart_ratio'] = df['order_id_modified']/df['cart_id']

    return df

def data_df_sample_received_to_kit_shipped(df, frequency, sample_received_within):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    df_samples = df[df.kit_received_time_in_days.notnull()]
    df_samples = df_samples[df_samples['kit_received_time_in_days'] <= int(sample_received_within)]

    if(frequency == 'Daily'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D')]).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='D')]).sample_id.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left')]).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left')]).sample_id.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS')]).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='MS')]).sample_id.nunique().reset_index()

    df = pd.merge(df_samples, df_ships, how='outer', on=['cart_created_date'])

    df['sample_received_to_kit_shipped_ratio'] = df['sample_id']/df['delivery_id']

    return df

def data_df_sample_received_to_kit_shipped_by_source(df, frequency, sample_received_within):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    df_samples = df[df.kit_received_time_in_days.notnull()]
    df_samples = df_samples[df_samples['kit_received_time_in_days'] <= int(sample_received_within)]

    if(frequency == 'Daily'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'source']).sample_id.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'source']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'source']).sample_id.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'source']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'source']).sample_id.nunique().reset_index()

    df = pd.merge(df_samples, df_ships, how='outer', on=['cart_created_date', 'source'])

    df['sample_received_to_kit_shipped_ratio'] = df['sample_id']/df['delivery_id']

    return df

def data_df_sample_received_to_kit_shipped_by_program(df, frequency, sample_received_within):
    df['cart_created_date'] = pd.to_datetime(df['cart_created_date'])

    df_samples = df[df.kit_received_time_in_days.notnull()]
    df_samples = df_samples[df_samples['kit_received_time_in_days'] <= int(sample_received_within)]

    if(frequency == 'Daily'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'program_category']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='D'), 'program_category']).sample_id.nunique().reset_index()
    elif(frequency == 'Weekly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'program_category']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='W-MON', label='left'), 'program_category']).sample_id.nunique().reset_index()
    elif(frequency == 'Monthly'):
        df_ships = df.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'program_category']).delivery_id.nunique().reset_index()
        df_samples = df_samples.groupby([pd.Grouper(key = 'cart_created_date', freq='MS'), 'program_category']).sample_id.nunique().reset_index()

    df = pd.merge(df_samples, df_ships, how='outer', on=['cart_created_date', 'program_category'])

    df['sample_received_to_kit_shipped_ratio'] = df['sample_id']/df['delivery_id']

    return df

#generate table function
def generate_table(dataframe, max_rows=1000):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

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
                                id='frequency_dropdown_state_ca_orders',
                                options=[
                                    {'label': 'Daily', 'value': 'Daily'},
                                    {'label': 'Weekly', 'value': 'Weekly'},
                                    {'label': 'Monthly', 'value': 'Monthly'}
                                ],
                                value='Weekly',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_ca_orders', n_clicks=0, children='Submit')
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Carts Created Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_ca_orders',
                            min_date_allowed='2018-01-01',
                            max_date_allowed=datetime.now().date().strftime('%Y-%m-%d'),
                            start_date='2019-01-01',
                            end_date=datetime.now().date().strftime('%Y-%m-%d')
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_ca_orders',
                                options=[
                                    {'label': 'All', 'value': 'All'},
                                    {'label': 'SmartGut', 'value': 'SMART_GUT'},
                                    {'label': 'SmartJane', 'value': 'SMART_JANE'},
                                    {'label': 'SmartFlu', 'value': 'SMART_FLU'}
                                ],
                                value='All',
                                style={'marginBottom': 10}
                            )
                        ],
                    ),
                    html.Hr(),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6('Data Pulled', style = {'marginBottom':0}),
                        html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/checkout_analysis/orders_data.csv'))))),
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
                            html.Div(
                                id='orders_by_source_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    ),
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
                            html.Div(
                                id='orders_by_program_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
            ], label='# Orders'),
            dbc.Tab(
            [
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Frequency:'),
                            dcc.Dropdown(
                                id='frequency_dropdown_state_ca_orders_to_cart',
                                options=[
                                    {'label': 'Daily', 'value': 'Daily'},
                                    {'label': 'Weekly', 'value': 'Weekly'},
                                    {'label': 'Monthly', 'value': 'Monthly'}
                                ],
                                value='Weekly',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_ca_orders_to_cart', n_clicks=0, children='Submit')
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Carts Created Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_ca_orders_to_cart',
                            min_date_allowed='2018-01-01',
                            max_date_allowed=datetime.now().date().strftime('%Y-%m-%d'),
                            start_date='2019-01-01',
                            end_date=datetime.now().date().strftime('%Y-%m-%d')
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_ca_orders_to_cart',
                                options=[
                                    {'label': 'All', 'value': 'All'},
                                    {'label': 'SmartGut', 'value': 'SMART_GUT'},
                                    {'label': 'SmartJane', 'value': 'SMART_JANE'},
                                    {'label': 'SmartFlu', 'value': 'SMART_FLU'}
                                ],
                                value='All',
                                style={'marginBottom': 10}
                            )
                        ],
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6('Data Pulled', style = {'marginBottom':0}),
                        html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/checkout_analysis/orders_data.csv'))))),
                        html.Div(id='orders_summary')
                    ])
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='orders_to_cart'),
                            dcc.Graph(
                                id='orders_to_cart_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id='orders_to_cart_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='orders_to_cart_by_source'),
                            dcc.Graph(
                                id='orders_to_cart_by_source_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id='orders_to_cart_by_source_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
            ], label='Orders to Cart Ratio'),
            dbc.Tab(
            [
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Frequency:'),
                            dcc.Dropdown(
                                id='frequency_dropdown_state_ca_sample_to_kit',
                                options=[
                                    {'label': 'Daily', 'value': 'Daily'},
                                    {'label': 'Weekly', 'value': 'Weekly'},
                                    {'label': 'Monthly', 'value': 'Monthly'}
                                ],
                                value='Weekly',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_ca_sample_to_kit', n_clicks=0, children='Submit')
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Carts Created Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_ca_sample_to_kit',
                            min_date_allowed='2018-01-01',
                            max_date_allowed=datetime.now().date().strftime('%Y-%m-%d'),
                            start_date='2019-01-01',
                            end_date=datetime.now().date().strftime('%Y-%m-%d')
                            ),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Sample Received Within X Days:'),
                            dcc.Input(id='input_sample_received_within', type='number', value='14', min='0'),
                        ],
                    ),
                    dbc.Col(
                        [
                            html.P(children='Product:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_ca_sample_to_kit',
                                options=[
                                    {'label': 'All', 'value': 'All'},
                                    {'label': 'SmartGut', 'value': 'SMART_GUT'},
                                    {'label': 'SmartJane', 'value': 'SMART_JANE'},
                                    {'label': 'SmartFlu', 'value': 'SMART_FLU'}
                                ],
                                value='All',
                                style={'marginBottom': 10}
                            )
                        ],
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H6('Data Pulled', style = {'marginBottom':0}),
                        html.P(id='date_of_pull_o', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/checkout_analysis/orders_data.csv'))))),
                        html.Div(id='orders_summary')
                    ])
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='sample_received_to_kit_shipped'),
                            dcc.Graph(
                                id='sample_received_to_kit_shipped_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id='sample_received_to_kit_shipped_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='sample_received_to_kit_shipped_by_source'),
                            dcc.Graph(
                                id='sample_received_to_kit_shipped_by_source_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id='sample_received_to_kit_shipped_by_source_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='sample_received_to_kit_shipped_by_program'),
                            dcc.Graph(
                                id='sample_received_to_kit_shipped_by_program_chart'
                            ),
                        ],
                        md=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id='sample_received_to_kit_shipped_by_program_table',
                                style={'overflowX': 'scroll'}
                            )
                        ],
                        md=6
                    )
                ]),
            ], label='Sample Received to Kit Shipped Ratio'),

    ]),
    dcc.Interval(
    id='interval_component_ca',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    ),
    html.Div(id='hidden_div_ca', style={'display':'none'}),
])

##########
#CALLBACKS
##########

@app.callback(
Output('orders_by_source_chart', 'figure'),
[Input('submit_button_ca_orders', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders', 'value'),
State('date_picker_range_state_ca_orders', 'start_date'),
State('date_picker_range_state_ca_orders', 'end_date'),
State('product_dropdown_state_ca_orders', 'value')])
def update_orders_by_source_chart(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_by_source = data_df_orders_by_source(dff, frequency)

    trace1 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CAPITAL_TYPING'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CAPITAL_TYPING'].order_id_modified,
        mode='lines',
        name='Capital Typing',
        stackgroup='one'
    )
    trace2 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL'].order_id_modified,
        mode='lines',
        name='Clinical',
        stackgroup='one'
    )
    trace3 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_BIOBANKED'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_BIOBANKED'].order_id_modified,
        mode='lines',
        name='Clinical Biobanked',
        stackgroup='one'
    )
    trace4 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_K'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_K'].order_id_modified,
        mode='lines',
        name='Clinical K',
        stackgroup='one'
    )
    trace5 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_UPGRADES'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'CLINICAL_UPGRADES'].order_id_modified,
        mode='lines',
        name='Clinical Upgrades',
        stackgroup='one'
    )
    trace6 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'DXPORTAL'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'DXPORTAL'].order_id_modified,
        mode='lines',
        name='DX Portal',
        stackgroup='one'
    )
    trace7 = dict(
        x=df_orders_by_source[df_orders_by_source['source'] == 'ROADRUNNER'].cart_created_date,
        y=df_orders_by_source[df_orders_by_source['source'] == 'ROADRUNNER'].order_id_modified,
        mode='lines',
        name='RoadRunner',
        stackgroup='one'
    )

    return go.Figure(
        data=[
            trace7, trace6, trace5, trace4, trace3, trace2, trace1
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Orders by Source',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': '# Orders'},
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
[Input('submit_button_ca_orders', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders', 'value'),
State('date_picker_range_state_ca_orders', 'start_date'),
State('date_picker_range_state_ca_orders', 'end_date'),
State('product_dropdown_state_ca_orders', 'value')])
def update_orders_by_source_table(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_by_source = data_df_orders_by_source(dff, frequency)

    df_orders_by_source = df_orders_by_source.pivot(index='cart_created_date', columns='source', values='order_id_modified').reset_index()

    df_orders_by_source = df_orders_by_source[df_orders_by_source['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    columns = []
    for column in df_orders_by_source.columns:
        if column == 'cart_created_date':
            columns.append('Cart Created Date')
        elif column == 'CAPITAL_TYPING':
            columns.append('Capital Typing')
        elif column == 'CLINICAL':
            columns.append('Clinical')
        elif column == 'CLINICAL_BIOBANKED':
            columns.append('Clinical Biobanked')
        elif column == 'CLINICAL_K':
            columns.append('Clinical K')
        elif column == 'CLINICAL_UPGRADES':
            columns.append('Clinical Upgrades')
        elif column == 'DXPORTAL':
            columns.append('DX Portal')
        elif column == 'ROADRUNNER':
            columns.append('RoadRunner')

    df_orders_by_source.columns = columns

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Orders by Source (Past 30 Days)'),
        generate_table(df_orders_by_source)
    ]


@app.callback(
Output('orders_by_program_chart', 'figure'),
[Input('submit_button_ca_orders', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders', 'value'),
State('date_picker_range_state_ca_orders', 'start_date'),
State('date_picker_range_state_ca_orders', 'end_date'),
State('product_dropdown_state_ca_orders', 'value')])
def update_orders_by_program_chart(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

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
            trace4, trace3, trace2, trace1
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Orders by Program',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': '# Orders'},
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
[Input('submit_button_ca_orders', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders', 'value'),
State('date_picker_range_state_ca_orders', 'start_date'),
State('date_picker_range_state_ca_orders', 'end_date'),
State('product_dropdown_state_ca_orders', 'value')])
def update_orders_by_program_table(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_by_program = data_df_orders_by_program(dff, frequency)

    df_orders_by_program = df_orders_by_program.pivot(index='cart_created_date', columns='program_category', values='order_id_modified').reset_index()

    df_orders_by_program = df_orders_by_program[df_orders_by_program['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    columns = []
    for column in df_orders_by_program.columns:
        if column == 'cart_created_date':
            columns.append('Cart Created Date')
        elif column == '1. pap':
            columns.append('PAP')
        elif column == '2. cash_pay_program':
            columns.append('Cash Pay Program')
        elif column == '3. patient_responsibility':
            columns.append('Patient Responsibility')
        elif column == '4. legacy_or_misc_programs':
            columns.append('Legacy or Misc. Programs')

    df_orders_by_program.columns = columns

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Orders by Program (Past 30 Days)'),
        generate_table(df_orders_by_program)
    ]


##########
#ORDERS TO CART FUNCTIONS
##########
@app.callback(
Output('orders_to_cart_chart', 'figure'),
[Input('submit_button_ca_orders_to_cart', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders_to_cart', 'value'),
State('date_picker_range_state_ca_orders_to_cart', 'start_date'),
State('date_picker_range_state_ca_orders_to_cart', 'end_date'),
State('product_dropdown_state_ca_orders_to_cart', 'value')])
def update_orders_to_cart_chart(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_to_cart = data_df_orders_to_cart(dff, frequency)

    df_orders_to_cart = round(df_orders_to_cart, 2)

    trace1 = dict(
        x=df_orders_to_cart.cart_created_date,
        y=df_orders_to_cart.orders_to_cart_ratio,
        mode='lines',
        name='Ratio',
    )

    return go.Figure(
        data=[
            trace1
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Orders to Cart Ratio',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': 'Ratio'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )


@app.callback(
Output('orders_to_cart_table', 'children'),
[Input('submit_button_ca_orders_to_cart', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders_to_cart', 'value'),
State('date_picker_range_state_ca_orders_to_cart', 'start_date'),
State('date_picker_range_state_ca_orders_to_cart', 'end_date'),
State('product_dropdown_state_ca_orders_to_cart', 'value')])
def update_orders_to_cart_table(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_to_cart = data_df_orders_to_cart(dff, frequency)

    df_orders_to_cart = df_orders_to_cart.drop(['order_id_modified', 'cart_id'], axis=1)

    df_orders_to_cart = round(df_orders_to_cart, 2)

    df_orders_to_cart = df_orders_to_cart[df_orders_to_cart['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    df_orders_to_cart.columns = ['Cart Created Date', 'Orders to Cart Ratio']

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Orders to Cart Ratio (Past 30 Days)'),
        generate_table(df_orders_to_cart)
    ]


@app.callback(
Output('orders_to_cart_by_source_chart', 'figure'),
[Input('submit_button_ca_orders_to_cart', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders_to_cart', 'value'),
State('date_picker_range_state_ca_orders_to_cart', 'start_date'),
State('date_picker_range_state_ca_orders_to_cart', 'end_date'),
State('product_dropdown_state_ca_orders_to_cart', 'value')])
def update_orders_to_cart_by_source_chart(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_to_cart_by_source = data_df_orders_to_cart_by_source(dff, frequency)

    df_orders_to_cart_by_source = round(df_orders_to_cart_by_source, 2)

    trace1 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CAPITAL_TYPING'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CAPITAL_TYPING'].orders_to_cart_ratio,
        mode='lines',
        name='Capital Typing'
    )
    trace2 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL'].orders_to_cart_ratio,
        mode='lines',
        name='Clinical'
    )
    trace3 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_BIOBANKED'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_BIOBANKED'].orders_to_cart_ratio,
        mode='lines',
        name='Clinical Biobanked'
    )
    trace4 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_K'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_K'].orders_to_cart_ratio,
        mode='lines',
        name='Clinical K'
    )
    trace5 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_UPGRADES'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'CLINICAL_UPGRADES'].orders_to_cart_ratio,
        mode='lines',
        name='Clinical Upgrades'
    )
    trace6 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'DXPORTAL'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'DXPORTAL'].orders_to_cart_ratio,
        mode='lines',
        name='DX Portal'
    )
    trace7 = dict(
        x=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'ROADRUNNER'].cart_created_date,
        y=df_orders_to_cart_by_source[df_orders_to_cart_by_source['source'] == 'ROADRUNNER'].orders_to_cart_ratio,
        mode='lines',
        name='RoadRunner'
    )

    return go.Figure(
        data=[
            trace1, trace2, trace3, trace4, trace5, trace6, trace7
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Orders to Cart Ratio by Source',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': 'Ratio'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )


@app.callback(
Output('orders_to_cart_by_source_table', 'children'),
[Input('submit_button_ca_orders_to_cart', 'n_clicks')],
[State('frequency_dropdown_state_ca_orders_to_cart', 'value'),
State('date_picker_range_state_ca_orders_to_cart', 'start_date'),
State('date_picker_range_state_ca_orders_to_cart', 'end_date'),
State('product_dropdown_state_ca_orders_to_cart', 'value')])
def update_orders_to_cart_by_source_table(submit_button, frequency, cart_start_date, cart_end_date, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_orders_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_orders_to_cart_by_source = data_df_orders_to_cart_by_source(dff, frequency)

    df_orders_to_cart_by_source = df_orders_to_cart_by_source.pivot(index='cart_created_date', columns='source', values='orders_to_cart_ratio').reset_index()

    df_orders_to_cart_by_source = round(df_orders_to_cart_by_source, 2)

    df_orders_to_cart_by_source = df_orders_to_cart_by_source[df_orders_to_cart_by_source['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    columns = []
    for column in df_orders_to_cart_by_source.columns:
        if column == 'cart_created_date':
            columns.append('Cart Created Date')
        elif column == 'CAPITAL_TYPING':
            columns.append('Capital Typing')
        elif column == 'CLINICAL':
            columns.append('Clinical')
        elif column == 'CLINICAL_BIOBANKED':
            columns.append('Clinical Biobanked')
        elif column == 'CLINICAL_K':
            columns.append('Clinical K')
        elif column == 'CLINICAL_UPGRADES':
            columns.append('Clinical Upgrades')
        elif column == 'DXPORTAL':
            columns.append('DX Portal')
        elif column == 'ROADRUNNER':
            columns.append('RoadRunner')

    df_orders_to_cart_by_source.columns = columns

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Orders to Cart Ratio by Source (Past 30 Days)'),
        generate_table(df_orders_to_cart_by_source)
    ]


##########
#Sample Received to Kit Shipped Functions
##########
@app.callback(
Output('sample_received_to_kit_shipped_chart', 'figure'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_chart(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped = data_df_sample_received_to_kit_shipped(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped = round(df_sample_received_to_kit_shipped, 2)

    trace1 = dict(
        x=df_sample_received_to_kit_shipped.cart_created_date,
        y=df_sample_received_to_kit_shipped.sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Ratio',
    )

    return go.Figure(
        data=[
            trace1
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': 'Ratio'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )


@app.callback(
Output('sample_received_to_kit_shipped_table', 'children'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_table(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped = data_df_sample_received_to_kit_shipped(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped = df_sample_received_to_kit_shipped.drop(['delivery_id', 'sample_id'], axis=1)

    df_sample_received_to_kit_shipped = round(df_sample_received_to_kit_shipped, 2)

    df_sample_received_to_kit_shipped = df_sample_received_to_kit_shipped[df_sample_received_to_kit_shipped['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    df_sample_received_to_kit_shipped.columns = ['Cart Created Date', 'Sample Received to Kit Shipped Ratio']

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio (Past 30 Days)'),
        generate_table(df_sample_received_to_kit_shipped)
    ]

@app.callback(
Output('sample_received_to_kit_shipped_by_source_chart', 'figure'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_by_source_chart(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped_by_source = data_df_sample_received_to_kit_shipped_by_source(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped_by_source = round(df_sample_received_to_kit_shipped_by_source, 2)

    trace1 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CAPITAL_TYPING'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CAPITAL_TYPING'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Capital Typing'
    )
    trace2 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Clinical'
    )
    trace3 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_BIOBANKED'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_BIOBANKED'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Clinical Biobanked'
    )
    trace4 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_K'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_K'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Clinical K'
    )
    trace5 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_UPGRADES'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'CLINICAL_UPGRADES'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Clinical Upgrades'
    )
    trace6 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'DXPORTAL'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'DXPORTAL'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='DX Portal'
    )
    trace7 = dict(
        x=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'ROADRUNNER'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['source'] == 'ROADRUNNER'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='RoadRunner'
    )

    return go.Figure(
        data=[
            trace1, trace2, trace3, trace4, trace5, trace6, trace7
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio by Source',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': 'Ratio'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )


@app.callback(
Output('sample_received_to_kit_shipped_by_source_table', 'children'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_by_source_table(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped_by_source = data_df_sample_received_to_kit_shipped_by_source(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped_by_source = df_sample_received_to_kit_shipped_by_source.pivot(index='cart_created_date', columns='source', values='sample_received_to_kit_shipped_ratio').reset_index()

    df_sample_received_to_kit_shipped_by_source = round(df_sample_received_to_kit_shipped_by_source, 2)

    df_sample_received_to_kit_shipped_by_source = df_sample_received_to_kit_shipped_by_source[df_sample_received_to_kit_shipped_by_source['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    columns = []
    for column in df_sample_received_to_kit_shipped_by_source.columns:
        if column == 'cart_created_date':
            columns.append('Cart Created Date')
        elif column == 'CAPITAL_TYPING':
            columns.append('Capital Typing')
        elif column == 'CLINICAL':
            columns.append('Clinical')
        elif column == 'CLINICAL_BIOBANKED':
            columns.append('Clinical Biobanked')
        elif column == 'CLINICAL_K':
            columns.append('Clinical K')
        elif column == 'CLINICAL_UPGRADES':
            columns.append('Clinical Upgrades')
        elif column == 'DXPORTAL':
            columns.append('DX Portal')
        elif column == 'ROADRUNNER':
            columns.append('RoadRunner')

    df_sample_received_to_kit_shipped_by_source.columns = columns

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio by Source (Past 30 Days)'),
        generate_table(df_sample_received_to_kit_shipped_by_source)
    ]


@app.callback(
Output('sample_received_to_kit_shipped_by_program_chart', 'figure'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_by_program_chart(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped_by_program = data_df_sample_received_to_kit_shipped_by_program(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped_by_program = round(df_sample_received_to_kit_shipped_by_program, 2)

    trace1 = dict(
        x=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '1. pap'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '1. pap'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='PAP',
    )
    trace2 = dict(
        x=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '2. cash_pay_program'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '2. cash_pay_program'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Cash Pay Program',
    )
    trace3 = dict(
        x=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '3. patient_responsibility'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '3. patient_responsibility'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Patient Responsibility',
    )
    trace4 = dict(
        x=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '4. legacy_or_misc_programs'].cart_created_date,
        y=df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['program_category'] == '4. legacy_or_misc_programs'].sample_received_to_kit_shipped_ratio,
        mode='lines',
        name='Legacy or Misc. Programs',
    )

    return go.Figure(
        data=[
            trace1, trace2, trace3, trace4
        ],
        layout=go.Layout(
            title=frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio by Program',
            xaxis={'title': 'Cart Created Date'},
            yaxis={'title': 'Ratio'},
            showlegend=True,
            legend=go.layout.Legend(
                x=1,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )


@app.callback(
Output('sample_received_to_kit_shipped_by_program_table', 'children'),
[Input('submit_button_ca_sample_to_kit', 'n_clicks')],
[State('frequency_dropdown_state_ca_sample_to_kit', 'value'),
State('date_picker_range_state_ca_sample_to_kit', 'start_date'),
State('date_picker_range_state_ca_sample_to_kit', 'end_date'),
State('input_sample_received_within', 'value'),
State('product_dropdown_state_ca_sample_to_kit', 'value')])
def update_sample_received_to_kit_shipped_by_program_table(submit_button, frequency, cart_start_date, cart_end_date, sample_received_within, product):
    #read in DataFrame
    df = CheckoutAnalyisDAO.get_samples_data()

    dff = filter_dataframe(df, cart_start_date, cart_end_date, product)

    df_sample_received_to_kit_shipped_by_program = data_df_sample_received_to_kit_shipped_by_program(dff, frequency, sample_received_within)

    df_sample_received_to_kit_shipped_by_program = round(df_sample_received_to_kit_shipped_by_program, 2)

    df_sample_received_to_kit_shipped_by_program = df_sample_received_to_kit_shipped_by_program.pivot(index='cart_created_date', columns='program_category', values='sample_received_to_kit_shipped_ratio').reset_index()

    df_sample_received_to_kit_shipped_by_program = df_sample_received_to_kit_shipped_by_program[df_sample_received_to_kit_shipped_by_program['cart_created_date'] >= (datetime.now().date() - timedelta(days=30))]

    columns = []
    for column in df_sample_received_to_kit_shipped_by_program.columns:
        if column == 'cart_created_date':
            columns.append('Cart Created Date')
        elif column == '1. pap':
            columns.append('PAP')
        elif column == '2. cash_pay_program':
            columns.append('Cash Pay Program')
        elif column == '3. patient_responsibility':
            columns.append('Patient Responsibility')
        elif column == '4. legacy_or_misc_programs':
            columns.append('Legacy or Misc. Programs')

    df_sample_received_to_kit_shipped_by_program.columns = columns

    return [
        html.H6(frequency + ' ' +  product + ' ' + 'Sample Received to Kit Shipped Ratio by Program (Past 30 Days)'),
        generate_table(df_sample_received_to_kit_shipped_by_program)
    ]

###########
#automated data pull
###########
@app.callback(
Output('hidden_div_ca', 'children'),
[Input('interval_component_ca', 'n_intervals')])
def update_data(n):
    pass