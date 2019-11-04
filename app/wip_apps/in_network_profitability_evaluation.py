#import necessary libraries
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_table
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import urllib.parse
import hvac
import psycopg2
import plotly.plotly as py
import plotly.graph_objs as go
import calendar
os.environ['TZ'] = 'America/Los_Angeles'

from app import app

description = 'Analysis to determine the profitiability of going in-network with payers.'

#####
#Vault Credentials
##stored as dictionaries
##ex) phi['user'], phi['pw'], phi['host'], phi['port']
#####
def file_home_token(file_name):
    with open(os.path.expanduser(file_name)) as f:
        return f.read()

# Using plaintext
VAULT_ID = file_home_token('~/.vault/dash_vault_id')
client = hvac.Client(url='https://vault.ubiome.com:8200', token=file_home_token('~/.vault/dash_vault_token'))
phi = client.read('secret/production/' + VAULT_ID + '/phi/')['data']
pg = client.read('secret/production/' + VAULT_ID + '/pg/')['data']
mysql = client.read('secret/production/' + VAULT_ID + '/mysql/')['data']

#metabase pull
claims_data_df = pd.read_csv('data/current/in_network_profitability_evaluation/claims_data.csv', parse_dates=['issue_date'], dtype={'claim_number': 'str', 'refnpi': 'str', 'proccode_1': 'str', 'proccode_2': 'str', 'proccode_3': 'str', 'proccode_4': 'str', 'proccode_5': 'str', 'proccode_6': 'str', 'units_1': 'float', 'units_2': 'float', 'units_3': 'float', 'units_4': 'float', 'units_5': 'float', 'units_6': 'float'})

#read in medicare rates
medicare_rates = pd.read_csv('data/current/in_network_profitability_evaluation/medicare_rates.csv')
medicare_rates = medicare_rates.loc[:,'YEAR':'SHORTDESC']
medicare_rates = medicare_rates[medicare_rates['MOD'] != 'QW']

#pre-processing
#keep only relevant columns
claims = claims_data_df[['id', 'issue_date', 'payer_id', 'payer_name', 'payment', 'product', 'proccode_1', 'proccode_2', 'proccode_3', 'proccode_4', 'proccode_5', 'proccode_6', 'units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']]

#start and end dates of sliders
start_date = pd.Timestamp((datetime.today() - timedelta(days=90)).date()) #approximation of a month
end_date = pd.Timestamp(claims['issue_date'].max().date())

#filter to date range
claims_filtered = claims[((claims['issue_date'] >= start_date) & (claims['issue_date'] <= end_date+timedelta(days=1)))]

#list of top 100 payers by claims volume
top_100_payers = claims_filtered.groupby('payer_name').count().sort_values('id', ascending=False)[:100].index.values
#filter to claims paid out by top 100 payers
top_100_payers_df = claims_filtered[claims_filtered['payer_name'].isin(top_100_payers)]

merged = pd.merge(top_100_payers_df, medicare_rates[['HCPCS','RATE2019']], how='left', left_on='proccode_1', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_1_rate'}, inplace=True)
merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_2', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_2_rate'}, inplace=True)
merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_3', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_3_rate'}, inplace=True)
merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_4', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_4_rate'}, inplace=True)
merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_5', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_5_rate'}, inplace=True)
merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_6', right_on='HCPCS')
merged.rename(columns={'RATE2019': 'proccode_6_rate'}, inplace=True)
merged = merged[['id', 'issue_date', 'payer_id', 'payer_name', 'payment', 'product', 'proccode_1', 'proccode_2', 'proccode_3', 'proccode_4', 'proccode_5', 'proccode_6', 'proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate', 'units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']]
merged['proccode_count'] = merged.apply(lambda x: x[['proccode_1', 'proccode_2', 'proccode_3', 'proccode_4', 'proccode_5', 'proccode_6']].count(), axis=1)
merged[['proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate']] = merged[['proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate']].fillna(0)
merged[['units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']] = merged[['units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']].fillna(0)
merged['medicare_1_payment'] = merged['proccode_1_rate'] * merged['units_1']
merged['medicare_2_payment'] = merged['proccode_2_rate'] * merged['units_2']
merged['medicare_3_payment'] = merged['proccode_3_rate'] * merged['units_3']
merged['medicare_4_payment'] = merged['proccode_4_rate'] * merged['units_4']
merged['medicare_5_payment'] = merged['proccode_5_rate'] * merged['units_5']
merged['medicare_6_payment'] = merged['proccode_6_rate'] * merged['units_6']
merged['medicare_rate'] = (merged['medicare_1_payment'] + merged['medicare_2_payment'] + merged['medicare_3_payment'] + merged['medicare_4_payment'] + merged['medicare_5_payment'] + merged['medicare_6_payment']) / merged['proccode_count']
merged['payment_minus_medicare_rate'] = merged['payment'] - merged['medicare_rate']
final_list = merged.groupby('payer_name').payment_minus_medicare_rate.describe().sort_values(by='mean', ascending=False)
final_list['aggregate_payment_difference'] = final_list['count'] * final_list['mean']

#initial sort
final_list = final_list.sort_values(by='aggregate_payment_difference', ascending=True)

#select and rename columns
final_list = final_list.rename({'count': '# Claims', 'mean': 'Average Payment Difference', 'aggregate_payment_difference': 'Aggregate Payment Difference'}, axis='columns')

#change Average Payment values to 2 decimal places
final_list = final_list.round(2)

output = final_list[['# Claims', 'Average Payment Difference', 'Aggregate Payment Difference']]

output = output.reset_index()

########
title = 'In-Network Profitability Evaluation'
subtitle = ['Any questions, please reach out: ', html.A('Email', href = 'mailto:andrew.cho@ubiome.com'), ' / ', html.A('Slack', href = 'https://ubiome.slack.com/messages/DDGBTGQMV')]
functionality_description = 'Displays a list of the top 100 payers (by claims volume) for the past 90 days (adjustable), which can be filtered or sorted by the # Claims, the Average Payment Difference (Payment Received - Medicare Rate), and the Aggregate Payment Difference (# Claims * Average Payment Difference)'
key_assumptions_description = '1. Medicare rates were applied to each unit and summed'
key_assumptions_description2 = '2. Where claims had multiple procedure codes, and thus multiple medicare rates, the medicare rates were averaged'
data_pull_time = time.strftime('%b %d, %Y %H:%M:%S', time.localtime(os.path.getmtime('data/current/in_network_profitability_evaluation/claims_data.csv')))
################################################################################
layout = html.Div([
    dbc.Container(
        [
            dbc.Card([
                dbc.CardHeader(title, style={'font-size':'2em'}),
                dbc.CardBody(
                    [
                        dbc.Button("Click here for more information on this dashboard", id="collapse-button_inpe", className="mb-3"),
                        dbc.Collapse(
                            [
                                dbc.CardText(
                                    html.P(children=functionality_description),
                                    #html.H6('Data Pulled', style = {'marginBottom':0}),
                                    #html.Div(id=date_of_pull_srm, children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime('data/samples_reports_metrics/orders_data.csv'))))
                                )
                            ],
                            id='collapse_inpe',
                            is_open=False
                        )
                    ]
                )]),
            dbc.Row([
                dbc.Col(
                    [
                        html.P(children='Claim Issued Between'),
                        dcc.DatePickerRange(
                        id='date_picker_range_state',
                        min_date_allowed=start_date,
                        max_date_allowed=end_date,
                        start_date=start_date,
                        end_date=end_date
                        ),
                ], md=6),
                dbc.Col(
                    [
                        html.P(children='Minimum # Claims per Payer', style = {'marginTop': 10}),
                        dcc.Input(id='count_of_claims', type='number', value='0', style = {'marginBottom': 10}),
                    ],
                    md=6,
                )
                ]
            ),
            dbc.Row([
                dbc.Col(
                [
                    html.P(children='Sort By:'),
                    dcc.Dropdown(
                        id='sort_by_dropdown_state',
                        options=[
                            {'label': '# Claims', 'value': 'count'},
                            {'label': 'Average Payment Difference (Payment Received - Medicare Rate)', 'value': 'mean'},
                            {'label': 'Aggregate Payment Difference (# Claims * Average Payment Difference)', 'value': 'aggregate_payment_difference'}
                        ],
                        value='aggregate_payment_difference',
                        style = {'width': '100%', 'marginBottom': 10}
                    ),
                ], md=6
                ),
                dbc.Col([
                    html.P(children='Sort Type:'),
                    dcc.Dropdown(
                        id='sort_type_dropdown_state',
                        options=[
                            {'label': 'Ascending', 'value': 'ascending'},
                            {'label': 'Descending', 'value': 'descending'}
                        ],
                        value='ascending',
                        style = {'width': '100%', 'marginBottom': 10}
                    )
                    ],
                    md=6,
                )
            ]),
            dbc.Row(
                dbc.Col(
                    html.Button(id='submit_button_inpe', n_clicks=0, children='Submit'),
                )
            ),
            dbc.Row(
                dbc.Col(
                    [
                        dash_table.DataTable(
                        id='table_inpe_state',
                        style_data={'whiteSpace': 'normal'},
                        style_table={'whiteSpace': 'normal'},
                        content_style='grow',
                        data=output.to_dict('rows'),
                        columns=[{"name": i, "id": i} for i in output.columns],
                        style_header={
                            'fontWeight': 'bold'
                        },
                        style_cell={
                            'whiteSpace': 'wrap',
                            'maxWidth': 0,
                        },
                        style_cell_conditional=[
                            {'if': {'column_id': '# Claims'},
                             'width': '10%'}
                        ]
                        )
                    ],
                ),
            )
        ],
        className="mt-4",
    ),
])

@app.callback(
    Output("collapse_inpe", "is_open"),
    [Input("collapse-button_inpe", "n_clicks")],
    [State("collapse_inpe", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output('table_inpe_state', 'data'),
[Input('submit_button_inpe', 'n_clicks')],
[State('date_picker_range_state', 'start_date'),
State('date_picker_range_state', 'end_date'),
State('count_of_claims', 'value'),
State('sort_by_dropdown_state', 'value'),
State('sort_type_dropdown_state', 'value')])
def update_data(submit_button, date_picker_range_state_start, date_picker_range_state_end, count_of_claims, sort_by_dropdown_state, sort_type_dropdown_state):
    #filter to date range
    claims_filtered = claims[((claims['issue_date'] >= pd.Timestamp(datetime.strptime(date_picker_range_state_start, '%Y-%m-%d').date())) & (claims['issue_date'] < pd.Timestamp(datetime.strptime(date_picker_range_state_end, '%Y-%m-%d').date())+timedelta(days=1)))]

    #list of top 100 payers by claims volume
    top_100_payers = claims_filtered.groupby('payer_name').count().sort_values('id', ascending=False)[:100].index.values
    #filter to claims paid out by top 100 payers
    top_100_payers_df = claims_filtered[claims_filtered['payer_name'].isin(top_100_payers)]

    merged = pd.merge(top_100_payers_df, medicare_rates[['HCPCS','RATE2019']], how='left', left_on='proccode_1', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_1_rate'}, inplace=True)
    merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_2', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_2_rate'}, inplace=True)
    merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_3', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_3_rate'}, inplace=True)
    merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_4', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_4_rate'}, inplace=True)
    merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_5', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_5_rate'}, inplace=True)
    merged = pd.merge(merged, medicare_rates[['HCPCS', 'RATE2019']], how='left', left_on='proccode_6', right_on='HCPCS')
    merged.rename(columns={'RATE2019': 'proccode_6_rate'}, inplace=True)
    merged = merged[['id', 'issue_date', 'payer_id', 'payer_name', 'payment', 'product', 'proccode_1', 'proccode_2', 'proccode_3', 'proccode_4', 'proccode_5', 'proccode_6', 'proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate', 'units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']]
    merged['proccode_count'] = merged.apply(lambda x: x[['proccode_1', 'proccode_2', 'proccode_3', 'proccode_4', 'proccode_5', 'proccode_6']].count(), axis=1)
    merged[['proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate']] = merged[['proccode_1_rate', 'proccode_2_rate', 'proccode_3_rate', 'proccode_4_rate', 'proccode_5_rate', 'proccode_6_rate']].fillna(0)
    merged[['units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']] = merged[['units_1', 'units_2', 'units_3', 'units_4', 'units_5', 'units_6']].fillna(0)
    merged['medicare_1_payment'] = merged['proccode_1_rate'] * merged['units_1']
    merged['medicare_2_payment'] = merged['proccode_2_rate'] * merged['units_2']
    merged['medicare_3_payment'] = merged['proccode_3_rate'] * merged['units_3']
    merged['medicare_4_payment'] = merged['proccode_4_rate'] * merged['units_4']
    merged['medicare_5_payment'] = merged['proccode_5_rate'] * merged['units_5']
    merged['medicare_6_payment'] = merged['proccode_6_rate'] * merged['units_6']
    merged['medicare_rate'] = (merged['medicare_1_payment'] + merged['medicare_2_payment'] + merged['medicare_3_payment'] + merged['medicare_4_payment'] + merged['medicare_5_payment'] + merged['medicare_6_payment']) / merged['proccode_count']
    merged['payment_minus_medicare_rate'] = merged['payment'] - merged['medicare_rate']
    final_list = merged.groupby('payer_name').payment_minus_medicare_rate.describe().sort_values(by='mean', ascending=False)
    final_list['aggregate_payment_difference'] = final_list['count'] * final_list['mean']

    #filtering & sorting
    final_list = final_list[final_list['count'] >= int(count_of_claims)]
    if sort_type_dropdown_state == 'ascending':
        final_list = final_list.sort_values(by=sort_by_dropdown_state, ascending=True)
    else: final_list = final_list.sort_values(by=sort_by_dropdown_state, ascending=False)

    #select and rename columns
    final_list = final_list.rename({'count': '# Claims', 'mean': 'Average Payment Difference', 'aggregate_payment_difference': 'Aggregate Payment Difference'}, axis='columns')

    #change Average Payment values to 2 decimal places
    final_list = final_list.round(2)

    output = final_list[['# Claims', 'Average Payment Difference', 'Aggregate Payment Difference']]

    output = output.reset_index()

    return output.to_dict("rows")
