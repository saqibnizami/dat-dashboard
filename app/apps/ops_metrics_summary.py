import os
import time
import urllib.parse
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State

os.environ['TZ'] = 'America/Los_Angeles'

from app import app, logger

description = 'Operations Metrics Summary'

class OpsDAO:

    @staticmethod
    def get_orders():
        try:
            df_orders = pd.read_csv('~/data_pulls/ops_metrics/orders_data.csv')
            df_orders['order_created_at'] = df_orders['order_created_at'].astype(dtype='datetime64[ns]')
            df_orders['order_created_at'].apply(lambda x: x.replace(tzinfo=None))
            return df_orders
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_kits():
        try:
            df_kits = pd.read_csv('~/data_pulls/ops_metrics/kits_data.csv')
            df_kits['ship_date'] = df_kits['ship_date'].astype(dtype='datetime64[ns]')
            df_kits['ship_date'].apply(lambda x: x.replace(tzinfo=None))
            return df_kits
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_samples():
        try:
            df_samples = pd.read_csv('~/data_pulls/ops_metrics/samples_data.csv')
            df_samples['sample_received'] = df_samples['sample_received'].astype(dtype='datetime64[ns]')
            df_samples['sample_received'].apply(lambda x: x.replace(tzinfo=None))
            return df_samples
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_released_reports():
        try:
            df_reports = pd.read_csv('~/data_pulls/ops_metrics/reports_data.csv')
            df_reports['report_created_at'] = df_reports['report_created_at'].astype(dtype='datetime64[ns]')
            df_reports['report_created_at'].apply(lambda x: datetime.replace(x, tzinfo=None))
            return df_reports
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_bills():
        try:
            df_bills = pd.read_csv('~/data_pulls/ops_metrics/bills_data.csv')
            df_bills['billing_date'] = df_bills['billing_date'].astype(dtype='datetime64[ns]')
            df_bills['billing_date'].apply(lambda x: x.replace(tzinfo=None))
            return df_bills
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_payments():
        try:
            df_payments = pd.read_csv('~/data_pulls/ops_metrics/payments_data.csv')
            df_payments['production_date'] = df_payments['production_date'].astype(dtype='datetime64[ns]')
            df_payments['production_date'].apply(lambda x: x.replace(tzinfo=None))
            df_payments['issue_date'] = df_payments['issue_date'].astype(dtype='datetime64[ns]')
            df_payments['issue_date'].apply(lambda x: x.replace(tzinfo=None))

            for item in ['charge', 'allowed', 'payment', 'coinsurance', 'deductible', 'rk']:
                df_payments[item] = df_payments[item].astype(float)
            return df_payments
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_fiscal_calendar():
        try:
            df_calendar = pd.read_csv('app/data/static/fiscal_calendar.csv', dtype={'Month': 'str', 'Quarter': 'str', 'Year': 'str'}, parse_dates=['Date', 'Week'])
            return df_calendar
        except Exception as e:
            logger.exception('')


    @staticmethod
    def get_cohort_orders_data():
        df_orders = OpsDAO.get_orders()
        df_kits = OpsDAO.get_kits()
        df_samples = OpsDAO.get_samples()
        df_reports = OpsDAO.get_released_reports()
        df_bills = OpsDAO.get_bills()
        df_payments = OpsDAO.get_payments()

        df_orders_kits = pd.merge(df_orders, df_kits, left_on='delivery_id', right_on='order_item_id', how='left')
        df_orders_kits = df_orders_kits.sort_values(by=['order_id', 'ship_date'], ascending=True).drop_duplicates(subset='order_id', keep='first', inplace=False)
        df_orders_kits_samples = pd.merge(df_orders_kits, df_samples, on='sample_id', how='left')
        df_orders_kits_samples_reports = pd.merge(df_orders_kits_samples, df_reports, on='order_id', how='left')
        df_orders_kits_samples_reports = df_orders_kits_samples_reports.sort_values(by=['order_id', 'report_created_at'], ascending=True).drop_duplicates(subset='order_id', keep='first', inplace=False)
        df_orders_kits_samples_reports_bills = pd.merge(df_orders_kits_samples_reports, df_bills, on='order_id', how='left')
        df_orders_kits_samples_reports_bills_payments = pd.merge(df_orders_kits_samples_reports_bills, df_payments, on='order_id', how='left')

        return df_orders_kits_samples_reports_bills_payments

#data manip functions
def data_for_noncohort_summary_table(start_date, end_date, date_aggregation, product, orientation):
    df_orders = OpsDAO.get_orders()
    df_kits = OpsDAO.get_kits()
    df_samples = OpsDAO.get_samples()
    df_reports = OpsDAO.get_released_reports()
    df_bills = OpsDAO.get_bills()
    df_payments = OpsDAO.get_payments()
    fiscal_calendar = OpsDAO.get_fiscal_calendar()

    #date filter
    try:
        df_orders_filtered = df_orders[(df_orders['order_created_at'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_orders['order_created_at'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
        df_kits_filtered = df_kits[(df_kits['ship_date'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_kits['ship_date'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
        df_samples_filtered = df_samples[(df_samples['sample_received'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_samples['sample_received'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
        df_reports_filtered = df_reports[(df_reports['report_created_at'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_reports['report_created_at'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
        df_bills_filtered = df_bills[(df_bills['billing_date'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_bills['billing_date'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
        df_payments_filtered = df_payments[(df_payments['issue_date'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_payments['issue_date'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    #Date Aggregation
    df_orders_filtered['order_created_at'] = df_orders_filtered['order_created_at'].dt.normalize()
    df_kits_filtered['ship_date'] = df_kits_filtered['ship_date'].dt.normalize()
    df_samples_filtered['sample_received'] = df_samples_filtered['sample_received'].dt.normalize()
    df_reports_filtered['report_created_at'] = df_reports_filtered['report_created_at'].dt.normalize()
    df_bills_filtered['billing_date'] = df_bills_filtered['billing_date'].dt.normalize()
    df_payments_filtered['issue_date'] = df_payments_filtered['issue_date'].dt.normalize()

    try:
        df_orders_merged = pd.merge(df_orders_filtered, fiscal_calendar, how = 'left', left_on = 'order_created_at', right_on = 'Date')
        df_kits_merged = pd.merge(df_kits_filtered, fiscal_calendar, how = 'left', left_on = 'ship_date', right_on = 'Date')
        df_samples_merged = pd.merge(df_samples_filtered, fiscal_calendar, how = 'left', left_on = 'sample_received', right_on = 'Date')
        df_reports_merged = pd.merge(df_reports_filtered, fiscal_calendar, how = 'left', left_on = 'report_created_at', right_on = 'Date')
        df_bills_merged = pd.merge(df_bills_filtered, fiscal_calendar, how = 'left', left_on = 'billing_date', right_on = 'Date')
        df_payments_merged = pd.merge(df_payments_filtered, fiscal_calendar, how = 'left', left_on = 'issue_date', right_on = 'Date')
        if date_aggregation == 'Weekly':
            df_orders_merged['date_agg'] = df_orders_merged['Week']
            df_kits_merged['date_agg'] = df_kits_merged['Week']
            df_samples_merged['date_agg'] = df_samples_merged['Week']
            df_reports_merged['date_agg'] = df_reports_merged['Week']
            df_bills_merged['date_agg'] = df_bills_merged['Week']
            df_payments_merged['date_agg'] = df_payments_merged['Week']
        elif date_aggregation == 'Monthly':
            df_orders_merged['date_agg'] = df_orders_merged['Month'] + '/' + df_orders_merged['Year']
            df_kits_merged['date_agg'] = df_kits_merged['Month'] + '/' + df_kits_merged['Year']
            df_samples_merged['date_agg'] = df_samples_merged['Month'] + '/' + df_samples_merged['Year']
            df_reports_merged['date_agg'] = df_reports_merged['Month'] + '/' + df_reports_merged['Year']
            df_bills_merged['date_agg'] = df_bills_merged['Month'] + '/' + df_bills_merged['Year']
            df_payments_merged['date_agg'] = df_payments_merged['Month'] + '/' + df_payments_merged['Year']
        elif date_aggregation == 'Quarterly':
            df_orders_merged['date_agg'] = df_orders_merged['Year'] + 'Q' + df_orders_merged['Quarter']
            df_kits_merged['date_agg'] = df_kits_merged['Year'] + 'Q' + df_kits_merged['Quarter']
            df_samples_merged['date_agg'] = df_samples_merged['Year'] + 'Q' + df_samples_merged['Quarter']
            df_reports_merged['date_agg'] = df_reports_merged['Year'] + 'Q' + df_reports_merged['Quarter']
            df_bills_merged['date_agg'] = df_bills_merged['Year'] + 'Q' + df_bills_merged['Quarter']
            df_payments_merged['date_agg'] = df_payments_merged['Year'] + 'Q' + df_payments_merged['Quarter']
        elif date_aggregation == 'Yearly':
            df_orders_merged['date_agg'] = df_orders_merged['Year']
            df_kits_merged['date_agg'] = df_kits_merged['Year']
            df_samples_merged['date_agg'] = df_samples_merged['Year']
            df_reports_merged['date_agg'] = df_reports_merged['Year']
            df_bills_merged['date_agg'] = df_bills_merged['Year']
            df_payments_merged['date_agg'] = df_payments_merged['Year']
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders_merged = df_orders_merged[df_orders_merged['code'] == 'smart_gut']
            df_kits_merged = df_kits_merged[df_kits_merged['item_type_id'] == '32708e12-4254-4d46-933a-f44d2ed32f5f']
            df_samples_merged = df_samples_merged[df_samples_merged['product'] == 16]
            df_reports_merged = df_reports_merged[df_reports_merged['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
            df_bills_merged = df_bills_merged[df_bills_merged['product'] == 'smart_gut']
            df_payments_merged = df_payments_merged[df_payments_merged['product'] == 'smart_gut']
        elif product == 'smartjane':
            df_orders_merged = df_orders_merged[df_orders_merged['code'] == 'smart_jane']
            df_kits_merged = df_kits_merged[df_kits_merged['item_type_id'] == 'd20ee363-ea4c-4411-ab71-cc68e8723670']
            df_samples_merged = df_samples_merged[df_samples_merged['product'] == 17]
            df_reports_merged = df_reports_merged[df_reports_merged['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
            df_bills_merged = df_bills_merged[df_bills_merged['product'] == 'smart_jane']
            df_payments_merged = df_payments_merged[df_payments_merged['product'] == 'smart_jane']
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    table = pd.DataFrame()
    table = table.append(df_orders_merged.groupby('date_agg').order_id.nunique())
    table = table.append(df_orders_merged[df_orders_merged['state'] == 'APPROVED'].groupby('date_agg').order_id.nunique()) #Orders Approved
    table = table.append(df_kits_merged.groupby('date_agg').shipment_id.nunique())
    table = table.append(df_samples_merged.groupby('date_agg').sample_id.nunique())
    table = table.append(df_reports_merged.groupby('date_agg').order_id.nunique())
    table = table.append(df_bills_merged.groupby('date_agg').bill_id.nunique())
    df_payments_merged['payment'] = df_payments_merged['payment'].astype(float)
    table = table.append(df_payments_merged.groupby('date_agg').claim_id.nunique())
    table = table.append(df_payments_merged.groupby('date_agg').payment.sum())
    table = table.append(df_payments_merged.groupby('date_agg').payment.mean())
    table = round(table, 2)
    table.index = ['Orders Generated', 'Orders Approved*', 'Kits Shipped', 'Samples Accessioned', 'Reports Released', 'Claims Billed', 'Claims w/ EOB (Payments)*', 'Aggregate Payment*', 'Average Payment*']
    table = table.transpose()
    table = table.fillna(0)
    table = table.applymap(lambda x: '{:,}'.format(x))
    table = table.reset_index().rename(columns={'index':'Date'})
    table = table.sort_index(ascending=False)

    if orientation == 'Horizontal':
        table['Date'] = table['Date'].astype(str)
        table = table.transpose()
        table.reset_index(level=0, inplace= True)
        new_header = table.iloc[0] #grab the first row for the header
        table = table[1:] #take the data less the header row
        table.columns = new_header #set the header row as the df header
    return(table)

def data_for_cohort_summary_table(start_date, end_date, date_aggregation, product, orientation):
    df_cohort_orders = OpsDAO.get_cohort_orders_data()
    fiscal_calendar = OpsDAO.get_fiscal_calendar()

    #date filter
    try:
        df_cohort_orders_filtered = df_cohort_orders[(df_cohort_orders['order_created_at'] >= pd.Timestamp(datetime.strptime(start_date, '%Y-%m-%d').date())) & (df_cohort_orders['order_created_at'] < pd.Timestamp(datetime.strptime(end_date, '%Y-%m-%d').date()) + timedelta(days=1))]
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    #Date Aggregation
    df_cohort_orders_filtered['order_created_at'] = df_cohort_orders_filtered['order_created_at'].dt.normalize()

    try:
        df_merged = pd.merge(df_cohort_orders_filtered, fiscal_calendar, how = 'left', left_on = 'order_created_at', right_on = 'Date')
        if date_aggregation == 'Weekly':
            df_merged['date_agg'] = df_merged['Week']
        elif date_aggregation == 'Monthly':
            df_merged['date_agg'] = df_merged['Month'] + '/' + df_merged['Year']
        elif date_aggregation == 'Quarterly':
            df_merged['date_agg'] = df_merged['Year'] + 'Q' + df_merged['Quarter']
        elif date_aggregation == 'Yearly':
            df_merged['date_agg'] = df_merged['Year']
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    #Product Filter
    try:
        if product == 'smartgut':
            df_merged = df_merged[df_merged['code'] == 'smart_gut']
        elif product == 'smartjane':
            df_merged = df_merged[df_merged['code'] == 'smart_jane']
    except Exception as e:
        logger.exception('')
        return pd.DataFrame()

    table = pd.DataFrame()
    table = table.append(df_merged.groupby('date_agg').order_id.nunique())
    table = table.append(df_merged[df_merged.shipment_id.notnull()].groupby('date_agg').order_id.nunique())
    table = table.append(df_merged[df_merged.sample_id.notnull()].groupby('date_agg').order_id.nunique())
    table = table.append(df_merged[df_merged.status_id.notnull()].groupby('date_agg').order_id.nunique())
    table = table.append(df_merged[df_merged.bill_id.notnull()].groupby('date_agg').order_id.nunique())
    df_merged['payment'] = df_merged['payment'].astype(float)
    table = table.append(df_merged.groupby('date_agg').claim_id.nunique())
    table = table.append(df_merged.groupby('date_agg').payment.sum())
    table = table.append(df_merged.groupby('date_agg').payment.mean())
    table = round(table, 2)
    table.index = ['Orders Generated', 'Kits Shipped', 'Samples Accessioned', 'Reports Released', 'Claims Billed', 'Claims w/ EOB (Payments)*', 'Aggregate Payment*', 'Average Payment*']
    table = table.transpose()
    table = table.fillna(0)
    table = table.applymap(lambda x: '{:,}'.format(x))
    table = table.reset_index().rename(columns={'index':'Date'})
    table = table.sort_index(ascending=False)

    if orientation == 'Horizontal':
        table['Date'] = table['Date'].astype(str)
        table = table.transpose()
        table.reset_index(level=0, inplace= True)
        new_header = table.iloc[0] #grab the first row for the header
        table = table[1:] #take the data less the header row
        table.columns = new_header #set the header row as the df header

    return(table)

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


########
title = 'Ops Metrics Summary'
functionality_description = 'Displays a table with a number of metrics relating to orders. Data is refreshed every hour. Weeks are aggregated with weeks starting Sunday. Months are aggregated at a daily level (ex. Jan: 1/1/18 - 1/31/18, Feb: 2/1/18 - 2/28/18, etc.). Quarters are aggregated at a monthly level (ex. Q1: 1/1/18 - 3/31/18, Q2: 4/1/18 - 6/30/18, etc.).'
################################################################################

layout = html.Div([
    dbc.Card([
        dbc.CardHeader(title, style={'font-size':'2em'}),
        dbc.CardBody(
            [
                dbc.Button("Click here for more information on this dashboard", id="collapse-button_srm", className="mb-3"),
                dbc.Collapse(
                    [
                        dbc.CardText([
                            html.P(children=functionality_description),
                        ])
                    ],
                    id='collapse_srm',
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
                            html.P(children='Product Filter:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_noncohort_kom',
                                options=[
                                    {'label': 'SmartGut', 'value': 'smartgut'},
                                    {'label': 'SmartJane', 'value': 'smartjane'}
                                ],
                                value='smartgut',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_summary_noncohort_kom', n_clicks=0, children='Submit'),
                            html.A(
                                'Download Data',
                                id='download_link_noncohort',
                                download="rawdata.csv",
                                href="",
                                target="_blank"
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Date Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_noncohort_kom',
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
                            html.P(children='Date Aggregation:'),
                            dcc.Dropdown(
                                id='date_aggregation_dropdown_state_noncohort_kom',
                                options=[
                                    {'label': 'Weekly', 'value': 'Weekly'},
                                    {'label': 'Monthly', 'value': 'Monthly'},
                                    {'label': 'Quarterly', 'value': 'Quarterly'},
                                    {'label': 'Yearly', 'value': 'Yearly'}
                                ],
                                value='Monthly',
                                style = {'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Orientation:'),
                            dcc.Dropdown(
                                id='orientation_dropdown_state_noncohort_kom',
                                options=[
                                    {'label': 'Vertical', 'value': 'Vertical'},
                                    {'label': 'Horizontal', 'value': 'Horizontal'}
                                ],
                                value='Vertical',
                                style = {'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(
                                id='summary_table_noncohort',
                                style={'overflowX': 'scroll'}
                            ),
                            dbc.Button("Table Details", id="button_summary_table_noncohort_kom", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_kom', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/ops_metrics/orders_data.csv'))))),
                                    html.P(children='Columns in asterisks have not yet been confirmed.')
                                ],
                                id='collapse_summary_table_noncohort_kom',
                                is_open=False
                            )
                        ],
                        md=12
                    ),
                ]),
            ], label='Non-Cohort Metrics Summary'),
            dbc.Tab([
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Product Filter:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_cohort_kom',
                                options=[
                                    {'label': 'SmartGut', 'value': 'smartgut'},
                                    {'label': 'SmartJane', 'value': 'smartjane'}
                                ],
                                value='smartgut',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_summary_cohort_kom', n_clicks=0, children='Submit'),
                            html.A(
                                'Download Data',
                                id='download_link_cohort',
                                download="rawdata.csv",
                                href="",
                                target="_blank"
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Date Between:'),
                            dcc.DatePickerRange(
                            id='date_picker_range_state_cohort_kom',
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
                            html.P(children='Date Aggregation:'),
                            dcc.Dropdown(
                                id='date_aggregation_dropdown_state_cohort_kom',
                                options=[
                                    {'label': 'Weekly', 'value': 'Weekly'},
                                    {'label': 'Monthly', 'value': 'Monthly'},
                                    {'label': 'Quarterly', 'value': 'Quarterly'},
                                    {'label': 'Yearly', 'value': 'Yearly'}
                                ],
                                value='Monthly',
                                style = {'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.P(children='Orientation:'),
                            dcc.Dropdown(
                                id='orientation_dropdown_state_cohort_kom',
                                options=[
                                    {'label': 'Vertical', 'value': 'Vertical'},
                                    {'label': 'Horizontal', 'value': 'Horizontal'}
                                ],
                                value='Vertical',
                                style = {'marginBottom': 10}
                            ),
                        ],
                        md=2,
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(
                                id='summary_table_cohort',
                                style={'overflowX': 'scroll'}
                            ),
                            dbc.Button("Table Details", id="button_summary_table_cohort_kom", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/ops_metrics/orders_data.csv'))))),
                                    html.P(children='Groups data into cohorts by date of order generation. Columns in asterisks have not yet been confirmed. In addition, Claims billed numbers are sometimes higher than reports released numbers, because there are orders that match to a bill or claim ID, but dont match to any released reports.')
                                ],
                                id='collapse_summary_table_cohort_kom',
                                is_open=False
                            )
                        ],
                        md=12
                    ),
                ]),
            ], label='Cohort Metrics Summary')
    ]),
    dcc.Interval(
    id='interval_component_kom',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    ),
    html.Div(id='hidden_div_kom', style={'display':'none'})
])

#####################
@app.callback(
Output("collapse_summary_table_noncohort_kom", "is_open"),
[Input("button_summary_table_noncohort_kom", "n_clicks")],
[State("collapse_summary_table_noncohort_kom", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_summary_table_cohort_kom", "is_open"),
[Input("button_summary_table_cohort_kom", "n_clicks")],
[State("collapse_summary_table_cohort_kom", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output('summary_table_noncohort', 'children'),
[Input('submit_button_summary_noncohort_kom', 'n_clicks')],
[State('date_picker_range_state_noncohort_kom', 'start_date'),
State('date_picker_range_state_noncohort_kom', 'end_date'),
State('date_aggregation_dropdown_state_noncohort_kom', 'value'),
State('product_dropdown_state_noncohort_kom', 'value'),
State('orientation_dropdown_state_noncohort_kom', 'value')])
def update_table_noncohort(submit_button, start_date, end_date, date_aggregation, product, orientation):
    t0 = time.time()
    dff = data_for_noncohort_summary_table(start_date, end_date, date_aggregation, product, orientation)
    elapsed_time = time.time() - t0
    logger.info('Updating noncohort data took {}s'.format(elapsed_time))

    return generate_table(dff)

@app.callback(
Output('summary_table_cohort', 'children'),
[Input('submit_button_summary_cohort_kom', 'n_clicks')],
[State('date_picker_range_state_cohort_kom', 'start_date'),
State('date_picker_range_state_cohort_kom', 'end_date'),
State('date_aggregation_dropdown_state_cohort_kom', 'value'),
State('product_dropdown_state_cohort_kom', 'value'),
State('orientation_dropdown_state_cohort_kom', 'value')])
def update_table_cohort(submit_button, start_date, end_date, date_aggregation, product, orientation):
    t0 = time.time()
    dff = data_for_cohort_summary_table(start_date, end_date, date_aggregation, product, orientation)
    elapsed_time = time.time()-t0
    logger.info('Updating cohort data took {}s'.format(elapsed_time))
    return generate_table(dff)

@app.callback(
Output('download_link_noncohort', 'href'),
[Input('submit_button_summary_noncohort_kom', 'n_clicks')],
[State('date_picker_range_state_noncohort_kom', 'start_date'),
State('date_picker_range_state_noncohort_kom', 'end_date'),
State('date_aggregation_dropdown_state_noncohort_kom', 'value'),
State('product_dropdown_state_noncohort_kom', 'value'),
State('orientation_dropdown_state_noncohort_kom', 'value')])
def update_download_link(submit_button, start_date, end_date, date_aggregation, product, orientation):
    dff = data_for_noncohort_summary_table(start_date, end_date, date_aggregation, product, orientation)
    csv_string = dff.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
Output('download_link_cohort', 'href'),
[Input('submit_button_summary_cohort_kom', 'n_clicks')],
[State('date_picker_range_state_cohort_kom', 'start_date'),
State('date_picker_range_state_cohort_kom', 'end_date'),
State('date_aggregation_dropdown_state_cohort_kom', 'value'),
State('product_dropdown_state_cohort_kom', 'value'),
State('orientation_dropdown_state_cohort_kom', 'value')])
def update_download_link(submit_button, start_date, end_date, date_aggregation, product, orientation):
    dff = data_for_cohort_summary_table(start_date, end_date, date_aggregation, product, orientation)
    csv_string = dff.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
Output('hidden_div_kom', 'children'),
[Input('interval_component_kom', 'n_intervals')])
def update_data(n):
    pass

@app.callback(
Output('date_of_pull_kom', 'children'),
[Input('interval_component_kom', 'n_intervals')])
def update_date_of_pull(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/ops_metrics/orders_data.csv'))))

@app.callback(
Output('date_picker_range_state_noncohort_kom', 'max_date_allowed'),
[Input('interval_component_kom', 'n_intervals')])
def update_noncohort_max_date(n):
    return datetime.now().date().strftime('%Y-%m-%d')

@app.callback(
Output('date_picker_range_state_cohort_kom', 'max_date_allowed'),
[Input('interval_component_kom', 'n_intervals')])
def update_cohort_max_date(n):
    return datetime.now().date().strftime('%Y-%m-%d')

@app.callback(
Output('date_picker_range_state_noncohort_kom', 'end_date'),
[Input('interval_component_kom', 'n_intervals')])
def update_noncohort_end_date(n):
    return datetime.now().date().strftime('%Y-%m-%d')

@app.callback(
Output('date_picker_range_state_cohort_kom', 'end_date'),
[Input('interval_component_kom', 'n_intervals')])
def update_cohort_end_date(n):
    return datetime.now().date().strftime('%Y-%m-%d')
