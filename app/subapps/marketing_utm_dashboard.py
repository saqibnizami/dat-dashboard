import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
import datetime as dt
import time
import pandas as pd

from app import app

df = pd.read_csv('data/marketing_utm_dashboard/db_pull.csv', parse_dates=['order_created_at', 'ship_date', 'sample_received_date', 'first_billing_date'])

start_date = df[df.utm_campaign.notnull()]['order_created_at'].min().date()
end_date = df['order_created_at'].max().date()

filtered_df = df
group_by_cols = ['utm_source']
orders = filtered_df.groupby(group_by_cols)['order_created_at'].count().rename('count_of_orders')
shipments = filtered_df.groupby(group_by_cols)['ship_date'].count().rename('count_of_shipments')
samples = filtered_df.groupby(group_by_cols)['sample_received_date'].count().rename('count_of_samples')
claims = filtered_df.groupby(group_by_cols)['first_billing_date'].count().rename('count_of_claims')
payments = filtered_df.groupby(group_by_cols)['first_issue_date'].count().rename('count_of_payments')
sum_of_payments = filtered_df.groupby(group_by_cols)['net_payment'].sum().rename('sum_of_payments')
average_payment_per_claim = (filtered_df.groupby(group_by_cols)['net_payment'].sum() / filtered_df.groupby(group_by_cols)['first_billing_date'].count()).rename('average_payment_per_claim')
output = pd.concat([orders,shipments,samples,claims,payments,sum_of_payments,average_payment_per_claim], axis=1)
output = output.reset_index()

########
title = 'Marketing UTM Dashboard'
subtitle = ['Any questions, please reach out to ', html.A('andrew.cho@ubiome.com', href = 'mailto:andrew.cho@ubiome.com')]
functionality_description = 'Displays a table with various metrics & filtering options'

################################################################################
layout = html.Div([
    html.Div([ #header
        html.H1(children=title, style = {'text-align': 'center', 'marginBottom': -10, 'color': '#00546e'}),
        html.H4(children=subtitle, style = {'text-align': 'center', 'color': '#00546e'}),
        html.H6('Functionality', style = {'marginBottom': 0}),
        html.P(children=functionality_description)
    ]),
    html.Hr(),
    html.P(children='Claim Issued Date Range'),
    dcc.DatePickerRange(
    id='date_picker_range',
    min_date_allowed=start_date,
    max_date_allowed=end_date,
    start_date=start_date,
    end_date=end_date
    ),
    html.P(children='Product Type:', style={'marginTop': 10}),
    dcc.Dropdown(
        id='product_dropdown',
        options=[
            {'label': 'All', 'value': 'all'},
            {'label': 'SmartGut', 'value': 'smartgut'},
            {'label': 'SmartJane', 'value': 'smartjane'}
        ],
        value='all',
        style = {'width': '50%', 'marginBottom': 10}
    ),
    html.P(children='Kit Type:'),
    dcc.Dropdown(
        id='kit_type_dropdown',
        options=[
            {'label': 'All', 'value': 'all'},
            {'label': 'Single Kit', 'value': 'singlekit'},
            {'label': 'Multi Kit', 'value': 'multikit'}
        ],
        value='all',
        style = {'width': '50%', 'marginBottom': 10}
    ),
    html.P(children='Upgrade Type:'),
    dcc.Dropdown(
        id='upgrade_dropdown',
        options=[
            {'label': 'All', 'value': 'all'},
            {'label': 'Upgrade', 'value': 'upgrade'},
            {'label': 'Non-Upgrade', 'value': 'nonupgrade'}
        ],
        value='all',
        style = {'width': '50%', 'marginBottom': 10}
    ),
    html.P(children='Sort By:'),
    dcc.Dropdown(
        id='sort_by_dropdown',
        options=[
            {'label': 'Count of Orders', 'value': 'count_of_orders'},
            {'label': 'Count of Shipments', 'value': 'count_of_shipments'},
            {'label': 'Count of Samples', 'value': 'count_of_samples'},
            {'label': 'Count of Claims', 'value': 'count_of_claims'},
            {'label': 'Count of Payments', 'value': 'count_of_payments'},
            {'label': 'Sum of Payments', 'value': 'sum_of_payments'},
            {'label': 'Average Payment per Claim', 'value': 'average_payment_per_claim'}
        ],
        value='count_of_orders',
        style = {'width': '50%', 'marginBottom': 10}
    ),
    html.P(children='Sort Type:'),
    dcc.Dropdown(
        id='sort_type_dropdown',
        options=[
            {'label': 'Ascending', 'value': 'ascending'},
            {'label': 'Descending', 'value': 'descending'}
        ],
        value='descending',
        style = {'width': '50%', 'marginBottom': 10}
    ),
    dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in output.columns],
    data=output.to_dict("rows")
    )
])

@app.callback(
Output('table', 'data'),
[Input('date_picker_range', 'start_date'),
Input('date_picker_range', 'end_date'),
Input('product_dropdown', 'value'),
Input('kit_type_dropdown', 'value'),
Input('upgrade_dropdown', 'value'),
Input('sort_by_dropdown', 'value'),
Input('sort_type_dropdown', 'value')]
)
def update_data(start_date, end_date, product_value, kit_value, upgrade_value, sort_by, sort_type):
    filtered_df = df

    filtered_df = filtered_df[((filtered_df['order_created_at'] >= datetime.strptime(start_date, '%Y-%m-%d').date()) & (filtered_df['order_created_at'] < (datetime.strptime(end_date, '%Y-%m-%d').date()+timedelta(days=1))))]

    if product_value != 'all':
        filtered_df = filtered_df[filtered_df['clinical_type_name'] == product_value]
    if kit_value != 'all':
        filtered_df = filtered_df[filtered_df['kit_type'] == kit_value]
    if upgrade_value != 'all':
        filtered_df = filtered_df[filtered_df['upgrade_marker'] == upgrade_value]
    group_by_cols = ['utm_source']
    orders = filtered_df.groupby(group_by_cols)['order_created_at'].count().rename('count_of_orders')
    shipments = filtered_df.groupby(group_by_cols)['ship_date'].count().rename('count_of_shipments')
    samples = filtered_df.groupby(group_by_cols)['sample_received_date'].count().rename('count_of_samples')
    claims = filtered_df.groupby(group_by_cols)['first_billing_date'].count().rename('count_of_claims')
    payments = filtered_df.groupby(group_by_cols)['first_issue_date'].count().rename('count_of_payments')
    sum_of_payments = filtered_df.groupby(group_by_cols)['net_payment'].sum().rename('sum_of_payments')
    average_payment_per_claim = (filtered_df.groupby(group_by_cols)['net_payment'].sum() / filtered_df.groupby(group_by_cols)['first_billing_date'].count()).rename('average_payment_per_claim')
    output = pd.concat([orders,shipments,samples,claims,payments,sum_of_payments,average_payment_per_claim], axis=1)

    #sorting
    if sort_type == 'descending':
        output = output.sort_values(by=sort_by, ascending=False)
    else:
        output = output.sort_values(by=sort_by, ascending=True)

    output = output.round(2)

    output = output.reset_index()
    return output.to_dict("rows")
