#%%
import calendar
import json
import os
from datetime import datetime

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import sqlalchemy as db
from dash.dependencies import Input, Output, State
import requests

from app import app, config

os.environ['TZ'] = 'America/Los_Angeles'

pg = config.get('pg')
phi = config.get('phi')
mb = config.get('metabase')

## Acquire Data Function
def sql_to_df(query_text, database, cred_set,  **kwargs):
    try:
        query_string = make_query(query_text,**kwargs)
        engine = makeEngine(d=database,creds=cred_set,driver='postgres')
        return (pd.read_sql(sql=query_string,con=engine))
    except Exception as e:
        print (e)
    

def makeEngine(d, creds, driver = 'postgres'):
    '''
    SQL Alchemy function
    '''
    dburl = db.engine.url.URL(driver,
                                database = d,
                                username = creds['user'],
                                password = creds['pw'],
                                host = creds['host'],
                                port = creds['port'])
    engine = db.create_engine(dburl)
    return engine


def make_query(sql_query,**kwargs):
    string = sql_query.format(**kwargs)
    return string

def generate_table(dataframe, max_rows=1000):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def metabase_pull(metabase_user, metabase_pass, card_id):
    header = {'Content-Type': 'application/json'}
    data ={'username': metabase_user, 'password': metabase_pass}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/{0}/query/json'.format(card_id)
    data = requests.post(card, headers=get_header)
    data_df = pd.DataFrame(data.json())
    return (data_df.to_json(orient='split'))

def read_file(path):
	with open(path,'r') as f:
		query = f.read()
		f.close()
	return query

###### Set Some Initial Values ######
start_date = '2019-01-01'
end_date = datetime.now().date()
today = datetime.today().date()

description = "This dashboard is focused on delivering reliable billing metrics"



topcard = dbc.Card(
    [
        dbc.CardHeader("uBiome Billing Dashboard",style={'font_size':'2em'}),
        dbc.CardBody([
            dbc.CardTitle("How to use"),
            dbc.CardText(dcc.Markdown(description))
            ])
    ], className = "mt-4"
    )

## Tooltips and header defaults
claims_generated_header =["Claims Generated",
                    dbc.Button("\u003f\u20dd", 
                        id = "cg-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nCount of Claims Generated"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2908")
                        ],
                        id='cg-button-collapse',
                        is_open=False)]

claims_submitted_header = ["Claims Submitted",
                    dbc.Button("\u003f\u20dd", 
                        id = "cs-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nCount of Claims Submitted to Payers"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2908")
                        ],
                        id='cs-button-collapse',
                        is_open=False)]

claims_adjudicated_header = ["Claims Adjudicated",
                    dbc.Button("\u003f\u20dd", 
                        id = "ca-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nCount of Claims Adjudicated"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2732")
                        ],
                        id='ca-button-collapse',
                        is_open=False)]

time_to_submission_header = ["Average Time to Claim Submission",
                    dbc.Button("\u003f\u20dd", 
                        id = "tcs-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nAverage Time to Claim Submission"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2911")
                        ],
                        id='tcs-button-collapse',
                        is_open=False)]

time_to_adjudication_header = ["Average Time to Claim Adjudication",
                    dbc.Button("\u003f\u20dd", 
                        id = "tca-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nAverage Time to Claim Adjudication"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2914")
                        ],
                        id='tca-button-collapse',
                        is_open=False)]

claims_adjudicated_submitted = ["Adjudicated to Submitted Ratio",
                    dbc.Button("\u003f\u20dd", 
                        id = "casr-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nRatio of Claims Adjudicated to Submitted."),
                        ],
                        id='casr-button-collapse',
                        is_open=False)]


net_payment_header =["Total Net Payment",
                    dbc.Button("\u003f\u20dd", 
                        id = "snp-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nSum of net payment from simplified EOBs"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2732")
                        ],
                        id='snp-button-collapse',
                        is_open=False)]

allowed_amount_header =["Total Allowed Amount",
                    dbc.Button("\u003f\u20dd", 
                        id = "aa-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [					
                            dbc.CardText("\n Sum of Allowed amounts from simplified EOBs"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2732")
                        ],
                        id='aa-button-collapse',
                        is_open=False)]


denied_claims_header =["Claims Denied",
                    dbc.Button("\u003f\u20dd", 
                        id = "dc-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\n Count of claims denied by payers"),
                            dbc.CardLink('Metabase Card', 
                                href = "https://metabase.ubiome.io/question/2915")
                        ],
                        id='dc-button-collapse',
                        is_open=False)]

denied_claims_ratio_header =["Adjudicated to Denied Ratio",
                    dbc.Button("\u003f\u20dd", 
                        id = "dcr-button-collapse-click",
                        size='sm',
                        outline=True,
                        style={"float":"right"}
                        ), 
                    dbc.Collapse(
                        [
                            dbc.CardHeader(" "),
                            dbc.CardText("\nRatio of claims adjudicated to denied"),
                        ],
                        id='dcr-button-collapse',
                        is_open=False)]


###### Tab Content ######
claims_tab =  [dbc.Row(
            [
            dbc.Col([
                    dbc.CardColumns(
                        [
                            dbc.Card(
                                [
                                dbc.CardHeader(claims_generated_header),
                                dbc.CardBody([
                                    #dbc.CardTitle("Claims Generated"),
                                    dbc.CardText(id='count_claims_generated')]),
                                ]),
                            dbc.Card(
                                [
                                dbc.CardHeader(claims_submitted_header),
                                dbc.CardBody([
                                    dbc.CardText(id='count_claims_submitted')])
                                ]),
                            dbc.Card(
                                [
                                dbc.CardHeader(claims_adjudicated_header),
                                dbc.CardBody([
                                    dbc.CardText(id='count_claims_adjudicated')])
                                    ])
                                ])
                            ]
                        )
                    ]
                ), 
dbc.Row(
            [
            dbc.Col(
                [
                dbc.CardColumns([
                            dbc.Card(
                                [
                                dbc.CardHeader(time_to_submission_header),
                                dbc.CardBody([
                                    dbc.CardText(id='time_to_submission')])
                                ]),
                            dbc.Card(
                                [
                                dbc.CardHeader(time_to_adjudication_header),
                                dbc.CardBody([
                                    dbc.CardText(id='time_to_adjudication')])
                                    ]
                                ),
                            dbc.Card(
                                [
                                dbc.CardHeader(claims_adjudicated_submitted),
                                dbc.CardBody([
                                    dbc.CardText(id='adjudicated_to_submitted_ratio')])
                                    ]
                                )]
                        )]
                )]
        )]
            
payments_tab =  dbc.Row(
            [
            dbc.Col([
                    html.H4('Payment Metrics'),
                    dbc.CardColumns(
                        [
                            dbc.Card([
                                dbc.CardHeader(net_payment_header),
                                dbc.CardBody([
                                    dbc.CardText(id='sum_claims_adjudicated'),
                                    ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader(allowed_amount_header),
                                dbc.CardBody([
                                    dbc.CardText(id='sum_allowed_amount')
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ])
       ])
denied_claims_tab = dbc.Row(
            [
            dbc.Col(        					
                [
                html.H4('Denied Claims Metrics'),
                dbc.CardColumns(
                    [dbc.Card(
                            [
                            dbc.CardHeader(denied_claims_header),
                                dbc.CardBody([
                                dbc.CardText(id='count_claims_denied')])
                            ]
                        ),
                        dbc.Card([
                            dbc.CardHeader(denied_claims_ratio_header),
                                dbc.CardBody([
                                dbc.CardText(id = 'adjudicated_denied_ratio')])
                        ])
                    ]
                )
            ])
        ])

appeals_tab = dbc.Row(
            [
            dbc.Col(        					
                [
                html.H4('Appeals Metrics'),
                dbc.Card(
                    [
                    dbc.CardHeader('Appeals Metrics'),
                        dbc.CardBody([
                            dbc.CardText(id='appeals_table')
                        ])
                    ]
                )]
            )
        ])

goals_tab = dbc.Row(
            [
            dbc.Col(        					
                [
                html.H4('Goal Monthly'),
                dbc.Card(
                    [
                    dbc.CardHeader('Goals'),
                        dbc.CardBody([
                        dbc.CardText(
                            [dbc.Row([
                                dbc.Col([
                                    dcc.DatePickerRange(
                                        id='my-date-picker-range-goals',
                                        min_date_allowed=datetime(2019, 1, 1),
                                        initial_visible_month=datetime(2019, 4, 1),
                                        start_date=today.replace(day=1),
                                        end_date=today.replace(day = calendar.monthrange(today.year,today.month)[1])
                                        )]),
                                dbc.Col([
                                    dbc.Input(id="goal_input", placeholder="Enter Claims Goal", type="text")
                                    
                                        ]),
                                dbc.Col([
                                    html.Button(id='submit_button_goals',n_clicks = 0, children='Submit')
                                        ])
                                    ]),
                            html.Br(),
                            dbc.Row([
                                dbc.Col([
                                     dcc.Graph(id='goals_graph',style={'height':300})
                                    ]),
                                dbc.Col([html.P(id = 'total_count_toward_goal'),
                                            html.Br(),
                                        html.P(id='return_projection'),
                                            html.Br(),
                                        html.P(id='gap_to_goal')
                                        ])
                                ])
                            ])
                        ])
                    ])
                ])
            ])
            
tabs = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Tabs(
                        [
                            dbc.Tab(claims_tab,label='Claims'),
                            dbc.Tab(payments_tab, label='Payments'),
                            dbc.Tab(denied_claims_tab,label='Denied Claims'),
                            dbc.Tab(appeals_tab,label='Appeals'),
                            dbc.Tab(goals_tab,label='Goals')
                        ]
                )
            ]	
        )
    ]
)


###### Body ######

body = dbc.Container(
    [
        dbc.Row([
            dbc.Col([topcard]),
        ]),
        dbc.Row(
            [
            html.H4("Selections")
            ]),
        dbc.Row([
            dbc.Col([
                    dcc.Dropdown(
                            options=[{'label':'SmartGut', 'value':'smart_gut'},
                                     {'label':'SmartJane', 'value':'smart_jane'},
                                     {'label':'SmartFlu', 'value':'smart_flu'}],
                            placeholder='Select Product',
                            multi=True,
                            value=['smart_gut'],
                            id='product_dropdown'),
                    dcc.Dropdown(
                            options=[{'label':'v3', 'value':'v3'},
                                     {'label':'v2','value':'v2'},
                                     {'label':'v1','value':'v1'}],
                            placeholder='Select Report Version',
                            value=['v3'],
                            multi=True,
                            id='version_drop')]),

            dbc.Col([
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        min_date_allowed=datetime(2018, 1, 1),
                        initial_visible_month=datetime(2019, 1, 1),
                        start_date=start_date,
                        end_date=end_date)]
                    ),
            dbc.Col([html.Button(id='submit_button',n_clicks = 0, children='Submit')])
                ]),
        tabs,
    ],className="mt-4"
)

#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app.layout = html.Div([body,
# 						html.Div(id='payment_data_table',style={'display':'none'}),
# 						html.Div(id='denied_claims_table',style={'display':'none'}),
# 						html.Div(id='submitted_claims_table',style={'display':'none'})])
layout = html.Div([body,
                        html.Div(id='payment_data_table',style={'display':'none'}),
                        html.Div(id='denied_claims_table',style={'display':'none'}),
                        html.Div(id='submitted_claims_table',style={'display':'none'}),
                        html.Div(id='goal_output',style={'display':'none'})])


###### Button Callbacks ######
@app.callback(
    Output("cg-button-collapse","is_open"),
    [Input("cg-button-collapse-click","n_clicks")],
    [State("cg-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("snp-button-collapse","is_open"),
    [Input("snp-button-collapse-click","n_clicks")],
    [State("snp-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("aa-button-collapse","is_open"),
    [Input("aa-button-collapse-click","n_clicks")],
    [State("aa-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("cs-button-collapse","is_open"),
    [Input("cs-button-collapse-click","n_clicks")],
    [State("cs-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("ca-button-collapse","is_open"),
    [Input("ca-button-collapse-click","n_clicks")],
    [State("ca-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("tcs-button-collapse","is_open"),
    [Input("tcs-button-collapse-click","n_clicks")],
    [State("tcs-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("tca-button-collapse","is_open"),
    [Input("tca-button-collapse-click","n_clicks")],
    [State("tca-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("casr-button-collapse","is_open"),
    [Input("casr-button-collapse-click","n_clicks")],
    [State("casr-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("dc-button-collapse","is_open"),
    [Input("dc-button-collapse-click","n_clicks")],
    [State("dc-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("dcr-button-collapse","is_open"),
    [Input("dcr-button-collapse-click","n_clicks")],
    [State("dcr-button-collapse","is_open")])
def toggle_collapse(n,is_open):
    if n:
        return not is_open
    return is_open

###### Data Callbacks ########
@app.callback(Output('payment_data_table','children'),
            [Input('submit_button','n_clicks')],
            [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value'),
                State('version_drop','value')])


def create_payment_results_table(submit_button,start_date,end_date,clin_product,version):
    '''
    Will contain data for 
        1. Count Claims Adjudicated
        2. Sum Total Payment (payment in aggregate)
        3. Sum Allowed Amount (allowed amount in aggregate)
        4. Average Payment per claim adjudicated
        5. Average Allowed Amount per claim adjudicated
    '''

    query = read_file('app/queries/billing/payments_table.sql')
    payments_table = sql_to_df(query_text=query, 
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date),
                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product),
                        version = ', '.join("'{0}'".format(product) for product in version) )
    return (payments_table.to_json(orient='split'))

@app.callback(Output('denied_claims_table','children'),
            [Input('submit_button','n_clicks')],
            [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value'),
                State('version_drop','value')])
def create_denied_claims_table(submit_button,start_date,end_date,clin_product,version):
    '''
    Will contain data for 
        1. Count Denied Claims
    '''
    query = read_file('app/queries/billing/denied_claims_table.sql')
    denied_table = sql_to_df(query_text=query,  
                        database = 'billing',
                        cred_set = phi,
                        start_date ="'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date),
                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product),
                        version = ', '.join("'{0}'".format(product) for product in version) )
    return (denied_table.to_json(orient='split'))

@app.callback(Output('submitted_claims_table','children'),
            [Input('submit_button','n_clicks')],
            [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value')])
def create_submitted_claims_table(submit_button,start_date,end_date,clin_product):
    query = read_file('app/queries/billing/count_claims_submitted.sql')
    count_claims_submitted = sql_to_df(query_text =query, 
                                        database = 'billing',
                                        cred_set = phi,
                                        start_date = "'{0}'".format(start_date),
                                        end_date="'{0}'".format(end_date),
                                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product))
    return(count_claims_submitted.to_json(orient='split'))

#Count of Claims Created
@app.callback(Output('count_claims_generated','children'),
                [Input('submit_button','n_clicks')],
                [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value')])
def count_claims_generated_callback(submit_button, start_date,end_date,clin_product):
    query = read_file('app/queries/billing/count_claims_generated.sql')
    count_claims_generated = sql_to_df(query_text =query, 
                                        database = 'billing',
                                        cred_set = phi,
                                        start_date = "'{0}'".format(start_date),
                                        end_date="'{0}'".format(end_date),
                                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product))
    return('{:,}'.format(count_claims_generated['count_claims_generated'][0]))

#Claims Generated Time
@app.callback(Output('time_to_submission','children'),
                [Input('submit_button','n_clicks')],
                [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value')])
def time_to_submission_callback(submit_button,start_date,end_date,clin_product):
    query = read_file('app/queries/billing/time_to_submission.sql')
    data = sql_to_df(query_text =query,
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date),
                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product))
    return ("{:.2f}".format(data['avg_time_to_submission'][0]))

# Time to Claim Adjudication
@app.callback(Output('time_to_adjudication','children'),
            [Input('submit_button','n_clicks')],
            [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value'),
                State('version_drop','value')])
def time_to_adjudication_callback(submit_button,start_date,end_date,clin_product,version):
    query = read_file('app/queries/billing/time_to_adjudication.sql')
    data = sql_to_df(query_text = query, 
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date),
                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product),
                        version = ', '.join("'{0}'".format(v) for v in version))
    return ("{:.2f}".format(data['avg_time_to_adjudication'][0]))

#Count of Claims Submitted
@app.callback(Output('count_claims_submitted','children'),
            [Input('submit_button','n_clicks'),
                Input('submitted_claims_table','children')])
def count_claims_submitted_callback(submit_button,submitted_claims_table):
    data = pd.read_json(submitted_claims_table,orient='split')
    return('{:,}'.format(data['count_claims_submitted'][0]))

#Count of Claims Adjudicated
@app.callback(Output('count_claims_adjudicated','children'),
            [Input('submit_button','n_clicks'),
             Input('payment_data_table','children')])
def count_claims_adjudicated_callback(submit_button, payment_data_table):
    data = pd.read_json(payment_data_table,orient='split')
    return('{:,}'.format(data['count_adjudicated'][0]))

#Sum of Claims Adjudicated
@app.callback(Output('sum_claims_adjudicated','children'),
            [Input('submit_button','n_clicks'),
                Input('payment_data_table','children')])
def sum_claims_adjudicated_callback(submit_button,payment_data_table):
    '''
    Data can be found in metabase questoion 2732
    '''
    data = pd.read_json(payment_data_table,orient='split')
    return('${:,.2f}'.format(data['total_payment'][0]))

#Count Claims Denied
@app.callback(Output('count_claims_denied','children'),
            [Input('submit_button','n_clicks'),
                Input('denied_claims_table','children')])
def count_claims_denied_callback(submit_button,denied_claims_table):
    data = pd.read_json(denied_claims_table,orient='split')
    return ('{:,}'.format(data['count_denied'][0]))


#Claims Adjudicated to Submitted Ratio
@app.callback(Output('adjudicated_to_submitted_ratio','children'),
            [Input('submit_button','n_clicks'),
                Input('payment_data_table','children'),
                Input('submitted_claims_table','children')])
def adjudicated_to_submitted_ratio_callback(submit_button,payments_table,
                                                submitted_claims_table):
    payments = pd.read_json(payments_table,orient='split')
    submitted = pd.read_json(submitted_claims_table,orient='split')
    count_adjudicated = payments['count_adjudicated'][0]
    count_submitted = submitted['count_claims_submitted'][0]

    return('{:.3f}'.format(count_adjudicated/count_submitted))
    

@app.callback(Output('adjudicated_denied_ratio','children'),
            [Input('submit_button','n_clicks'),
                Input('payment_data_table','children'),
                Input('denied_claims_table','children')])
def adjudicated_denied_ratio_callback(submit_button,payments_table,denied_table):
    payments = pd.read_json(payments_table,orient='split')
    denied = pd.read_json(denied_table,orient='split')

    count_adjudicated = payments['count_adjudicated'][0]
    count_denied = denied['count_denied'][0]
    return('{:.3f}'.format(count_adjudicated/count_denied))
    
#Sum Allowed Amount
@app.callback(Output('sum_allowed_amount','children'),
            [Input('submit_button','n_clicks'),
                Input('payment_data_table','children')])
def sum_allowed_amount_callback(submit_button,payment_data_table):
    data = pd.read_json(payment_data_table,orient='split')
    sum_allowed_amount = data['total_allowed'][0]
    return('${:,.2f}'.format(sum_allowed_amount))

@app.callback(Output('appeals_table','children'),
            [Input('submit_button','n_clicks')],
            [State('my-date-picker-range','start_date'),
                State('my-date-picker-range','end_date'),
                State('product_dropdown','value')])
def appeals_table_callback(submit_button,start_date,end_date,clin_product):
    query = read_file('app/queries/billing/appeals_by_type.sql')
    data = sql_to_df(query_text =query,  
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date),
                        clinical_products=', '.join("'{0}'".format(product) for product in clin_product))
    return (generate_table(data))

#Get the value from free input and write
@app.callback(Output('goal_output','children'),
                    [Input('goal_input','value')])
def get_output(goal_input):
    if goal_input == None:
        df = pd.DataFrame({'goal':[0]})
    else:
        df = pd.DataFrame({'goal':[goal_input]})
    return df.to_json(orient='split') 

#Daily Released in Goal
@app.callback(Output('goals_graph','figure'),
            [Input('submit_button_goals',"n_clicks"),
                Input('goal_output','children')],
            [State('my-date-picker-range-goals','start_date'),
                State('my-date-picker-range-goals','end_date')])
def goals_data(submit_button_goals,goals_output,start_date,end_date):
    query = read_file('app/queries/billing/released_count.sql')
    released = sql_to_df(query_text=query,
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date))
    query_pro = read_file('app/queries/billing/billing_projections.sql')
    proj = sql_to_df(query_text=query_pro, 
                        database = 'backend',
                        cred_set = pg,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date)).set_index('prediction')


    released.billing_date = pd.to_datetime(released.billing_date,infer_datetime_format=True)

    released['cumulative_sum'] = released['counts'].cumsum()
    
    released_bd = list(released.billing_date.dt.strftime("%Y-%m-%d"))
    released_counts = list(released['counts'])
    released_cumsum = list(released['cumulative_sum'])
    total_counts = released['counts'].sum()
    lower_bound = proj.loc['lower_bound']['counts'] + total_counts
    upper_bound = proj.loc['upper_bound']['counts'] + total_counts
    if goals_output == None:
        goal = 0
    else:
        goal = pd.read_json(goals_output,orient='split')['goal'][0]
    if datetime.strptime(end_date, '%Y-%m-%d').date() > datetime.today().date():
        goal_box = {
                                "type":"rect",
                                "x0":str(datetime.today().date()),
                                "y0":lower_bound,
                                "x1":end_date,
                                "y1":upper_bound,
                                "line":{
                                    'color':'rgb(40, 164, 40)',
                                    'width':1.5
                                },
                                'fillcolor':'rgba(152, 230, 152, 0.4)'
                            }
    else:
        goal_box = None
    figure = go.Figure(
            data = [
                go.Scatter(x = released_bd,
                y = released_cumsum,
                name = "Released Reports",
                fill = 'tozeroy',
                mode='none')],
            layout = go.Layout(
                title = 'Billing Projections',
                showlegend=False,
                shapes = [{
                                "type":'line',
                                    "x0":start_date,
                                    "x1":end_date,
                                    "y0":goal,
                                    "y1":goal,
                                    'line': {
                                        'color': 'rgb(128, 0, 128)',
                                        'width': 4}},
                            goal_box
                            ],
                legend = go.layout.Legend(
                x=0,
                y=0),
                margin=go.layout.Margin(l=40, r=0, t=40, b=30),
                
            )
        )
    return figure
#Daily Released in Goal
@app.callback(Output('total_count_toward_goal','children'),
            [Input('submit_button_goals',"n_clicks")],
            [State('my-date-picker-range-goals','start_date'),
                State('my-date-picker-range-goals','end_date')])
def total_count_toward_goal(submit_button_goals,start_date,end_date):
    query = read_file('app/queries/billing/released_count.sql')
    released = sql_to_df(query_text=query,  
                            database = 'billing',
                            cred_set = phi,
                            start_date = "'{0}'".format(start_date),
                            end_date="'{0}'".format(end_date))
    start_date = datetime.strptime(start_date,'%Y-%m-%d').strftime('%m/%d')
    end_date = datetime.strptime(end_date,'%Y-%m-%d').strftime('%m/%d')
    total = released['counts'].sum()
    return ("Claims Submitted Between {0}-{1}: {2}".format(start_date,end_date,total))

@app.callback(Output('return_projection','children'),
            [Input('submit_button_goals',"n_clicks"),
                Input('goal_output','children')],
            [State('my-date-picker-range-goals','start_date'),
                State('my-date-picker-range-goals','end_date')])
def goals_data(submit_button_goals,goals_output,start_date,end_date):
    if datetime.strptime(end_date, '%Y-%m-%d').date() > datetime.today().date():
        query = read_file('app/queries/billing/billing_projections.sql')
        proj = sql_to_df(query_text=query, 
                            database = 'backend',
                            cred_set = pg,
                            start_date = "'{0}'".format(start_date),
                            end_date="'{0}'".format(end_date)).set_index('prediction')
        lower_bound = proj.loc['lower_bound']['counts']
        upper_bound = proj.loc['upper_bound']['counts']
        return ("We expect between {0} and {1} additional claims to be submitted\
                        before the end of our goal".format(lower_bound,upper_bound))
    else:
        return (None)

@app.callback(Output('gap_to_goal','children'),
            [Input('submit_button_goals',"n_clicks"),
                Input('goal_output','children')],
            [State('my-date-picker-range-goals','start_date'),
                State('my-date-picker-range-goals','end_date')])
def goals_data(submit_button_goals,target_goal,start_date,end_date):
    query = read_file('app/queries/billing/released_count.sql')
    released = sql_to_df(query_text=query, 
                        database = 'billing',
                        cred_set = phi,
                        start_date = "'{0}'".format(start_date),
                        end_date="'{0}'".format(end_date))
    total_goal = released['counts'].sum()
    
    if (target_goal == None) | (target_goal == 0):
        return("Gap To Goal: Please Enter Goal")
    else:
        target_goal = pd.read_json(target_goal,orient='split')['goal'][0]
        target_goal = int(target_goal)
        total_goal = int(total_goal)
        if target_goal - total_goal > 0:
            return ("Gap To Goal: {} Claims".format(target_goal - total_goal))
        elif target_goal - total_goal < 0:
            return("Gap To Goal: Goal Met!")

## Run 
if __name__ == "__main__":
    app.run_server()
