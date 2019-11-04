import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import requests
import sqlalchemy as db
from dash.dependencies import Input, Output, State

from app import app, config

pg = config.get('pg')
phi = config.get('phi')
mb = config.get('mb')

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

def metabase_pull(metabase_user, metabase_pass, card_id):
    header = {'Content-Type': 'application/json'}
    data ={'username': metabase_user, 'password': metabase_pass}

    auth = requests.post('https://metabase.ubiome.io/api/session', data=json.dumps(data), headers=header).json()
    get_header = {'Content-Type': 'application/json', 'X-Metabase-Session': auth['id']}

    card = 'https://metabase.ubiome.io/api/card/{0}/query/json'.format(card_id)
    data = requests.post(card, headers=get_header)
    data_df = pd.DataFrame(data.json())
    return (data_df.to_json(orient='split'))


description = "This dashboard is focused on delivering product analytics for marketing experiments"

topcard = dbc.Card(
    [
        dbc.CardHeader("uBiome Marketing Experiments Dashboard",style={'font_size':'2em'}),
        dbc.CardBody([
            dbc.CardTitle("How to use"),
            dbc.CardText(dcc.Markdown(description))
            ])
    ], className = "mt-4"
    )
experiment_map = [
    {'exp_name':'Remove S&H', 'Product':'SmartGut','exp_id':'FOqgdaAZTpmzBv8TH_IHPA' },
{'exp_name':'Remove S&H','Product':'SmartJane','exp_id':'KJ_Up-AXRgWtBqjBbZNkAQ'},
{"exp_name":"Assume Cashpay",'Product':'SmartGut','exp_id':"4zEazw-US3C53kCrBsKw_A"},
{"exp_name":'Assume Cashpay','Product':'SmartJane','exp_id':"u34A_U77R9eDmx6YRxH1rQ"},
{"exp_name":"Value Proposition",'Product':'SmartGut','exp_id':"otcYL4LLQHeY5OZxLa_DJQ"},
{"exp_name":"Value Proposition", 'Product':'SmartJane','exp_id':"U0Uesb7HTembURqO14IoMw"},
{"exp_name":"1, 3 or 6 Kits",'Product':'SmartGut','exp_id':'5pOcYJXpTYSgDYCmI831RA'},
{"exp_name":"1, 3 or 6 Kits",'Product':'SmartJane','exp_id':'_Pfe18yXS2ivKHnG1A9ROA'}]

cards_group_ctrl = dbc.CardGroup(
                    [ 
                        dbc.Card([
                            dbc.CardHeader('Orders to Cart Ratio'),
                            dbc.CardBody(
                                [
                                    dbc.CardTitle(id='ctrl-o_to_c'),
                                    #dbc.CardText('Orders to Cart')
                                ])
                            ]),
                        dbc.Card([
                            dbc.CardHeader('Average Kits Requested'),
                            dbc.CardBody(
                                [
                                    dbc.CardTitle(id='ctrl-avg_kits_requested',),
                                    #dbc.CardText('Program Breakdown')
                                ]) 
                        ]),
                        dbc.Card([
                            dbc.CardHeader('Count of Kits Returned'),
                            dbc.CardBody(
                                [
                                    dbc.CardTitle(id = 'ctrl-total_kits_requested'),
                                    #dbc.CardText('Program Breakdown')
                                ])     
                        ]),
                        dbc.Card([
                            dbc.CardHeader('Average Kit Return Time'),
                            dbc.CardBody(
                                [
                                    dbc.CardTitle(id = 'ctrl-average_days_to_return')
                                ]
                            )
                        ]),
                        dbc.Card([
                            dbc.CardHeader('Sample Received:Kits Shipped Ratio'),
                            dbc.CardBody(
                                [
                                    dbc.CardTitle(id = 'ctrl-sample_to_shipped_ratio'),
                                    #dbc.CardText('Average Kits requested')
                                ])      
                            ])
                        ])
card_group_exp = dbc.CardGroup(
                            [
                            dbc.Card([
                                dbc.CardHeader('Orders to Cart Ratio'),
                                dbc.CardBody(
                                    [
                                        dbc.CardTitle(id = 'exp-o_to_c'),
                                        #dbc.CardText('Average Kits requested')
                                    ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Average Kits Requested'),
                                dbc.CardBody(
                                    [
                                        dbc.CardTitle(id='exp-avg_kits_requested'),
                                        #dbc.CardText('Average Kits Returned')
                                    ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Count of Kits Returned'),
                                dbc.CardBody(
                                    [
                                        dbc.CardTitle(id = 'exp-total_kits_returned'),
                                        #dbc.CardText('Average Kits Returned')
                                    ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Average Kit Return Time'),
                                dbc.CardBody(
                                    [
                                        dbc.CardTitle(id = 'exp-average_days_to_return')
                                    ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader('Sample Received:Kits Shipped Ratio'),
                                dbc.CardBody(
                                    [
                                        dbc.CardTitle(id = 'exp-sample_to_shipped_ratio'),
                                        #dbc.CardText('Average Kits requested')
                                    ])
                            ])
    ])

body = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                topcard,
                html.Br(),
                #dbc.Row(id='latest_pull',children = 'Latest Pull')
                ])
            ]),

        dbc.Row([html.H4("Please Select An Experiment"), html.Br()]),
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    options = [{'label': 'Remove S&H', 'value':'Remove S&H'},
                                {'label':'Assume Cashpay','value':'Assume Cashpay'},
                                {'label':'Value Proposition','value':'Value Proposition'},
                                {'label':'1, 3 or 6 Kits', 'value':'1, 3 or 6 Kits'}],
                    placeholder = 'Please Select Experiment',
                    multi = False,
                    value = 'Remove S&H',
                    id = 'experiment_selector')]),
            dbc.Col([
                dcc.Dropdown(
                            options=[{'label':'SmartGut', 'value':'SmartGut'},
                                     {'label':'SmartJane', 'value':'SmartJane'}],
                            placeholder='Select Product',
                            multi=False,
                            value='SmartGut',
                            id='product_dropdown')
            ]),
            dbc.Col([html.Button(id = 'submit_button',n_clicks = 0, children = 'Submit')])
                ]),
            html.Br(),
            html.H5('Control Group',style={'align':'center'}),
            dbc.Row([cards_group_ctrl],style={'margin-bottom':'25px'}),
            html.H5('Experiment Group',style={'align':'center'}),
            dbc.Row([card_group_exp]),
            dbc.Row([
                dbc.Col([dcc.Graph(id= 'sample_return_days')]),
                dbc.Col(dcc.Graph(id='programs_donut'))
            ])
    ])

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
layout = html.Div([body,
                    dcc.Interval(id='interval_component',
                                interval = 3600*1000,
                                n_intervals = 0),
                    html.Div(id='table_hidden_div',style={'display':'none'}),
                    html.Div(id='programs_hidden_div',style={'display':'none'}),
                    html.Div(id='sample_return_hidden_div',style={'display':'none'})])

# Helper Functions
def metabase_to_csv(mb_object,name):
    '''
    Get data from Metabase and save as csv

    mb_object: data from Metabase
    '''
    try:
        df = pd.read_json(mb_object,orient='split')
        df.to_csv('data/current/checkout_experiments/'+name+'.csv')
        return (df.to_json(orient='split'))
    except Exception as e:
        return(e)

def get_exp_id(name,clin_product,grp):
    '''
    Using the experiment map, retrieve the experiment id
    '''
    df = pd.DataFrame(experiment_map)
    exp_id = df.exp_id.loc[(df.exp_name == name ) & (df.Product == clin_product)].values[0]
    if grp == 'control':
        return (exp_id+':0')
    elif grp == 'experiment':
        return(exp_id+':1')

def get_metric(df,measurement,exp_id):
    return(df[measurement].loc[df.checkout_version == exp_id].values[0])


def process_data(data,exp_id):
    subset = data[data.checkout_version.str.startswith(exp_id[:-2])]
    subset['returned'] = None
    subset['returned'][subset.order_state.isin(['RELEASED','RECEIVED','RECOLLECTED'])] = 'Yes'
    subset['returned'][~subset.order_state.isin(['RELEASED','RECEIVED','RECOLLECTED'])] = 'No'
    
    ctrl_total_vol = len(subset[subset.checkout_version == exp_id+':0'])
    exp_total_vol = len(subset[subset.checkout_version == exp_id+':1'])
    
    ctrl = subset[(subset.checkout_version == exp_id+':0') & (subset.returned=='Yes')]
    ctrl = ctrl.sort_values(['checkout_version','time_to_sample_return'])
    ctrl['cumcount'] = ctrl.groupby('returned').cumcount()+1
    ctrl['percent_returned'] = (ctrl['cumcount']/ctrl_total_vol)*100
    ctrl = ctrl[['time_to_sample_return','percent_returned']]
    ctrl = ctrl.groupby('time_to_sample_return').max().reset_index()
    
    exp = subset[(subset.checkout_version == exp_id+':1') & (subset.returned=='Yes')]
    exp = exp.sort_values(['checkout_version','time_to_sample_return'])
    exp['cumcount'] = exp.groupby('returned').cumcount()+1
    exp['percent_returned'] = (exp['cumcount']/exp_total_vol)*100
    exp = exp[['time_to_sample_return','percent_returned']]
    exp = exp.groupby('time_to_sample_return').max().reset_index()
    return(ctrl,exp)

### Callbacks
@app.callback(Output('table_hidden_div','children'),
                [Input('interval_component','n_intervals')])
def update_data(n):
    try:
        table = metabase_pull(mb['user'],mb['pass'],'3167')
        metabase_to_csv(table,'table')
        return(table)
    except Exception as e:
        print(e)
        df = pd.read_csv('data/current/checkout_experiments/table.csv') 
        return (df.to_json(orient='split'))

@app.callback(Output('programs_hidden_div','children'),
                [Input('interval_component','n_intervals')])
def update_data(n):
    try:
        programs = metabase_pull(mb['user'],mb['pass'],'3168')
        metabase_to_csv(programs,'programs')
        return(programs)
    except Exception as e:
        print(e)
        df = pd.read_csv('data/current/checkout_experiments/programs.csv') 
        return (df.to_json(orient='split'))

@app.callback(Output('sample_return_hidden_div','children'),
                [Input('interval_component','n_intervals')])
def update_data(n):
    try:
        programs = metabase_pull(mb['user'],mb['pass'],'3192')
        metabase_to_csv(programs,'programs')
        return(programs)
    except Exception as e:
        print(e)
        df = pd.read_csv('data/current/checkout_experiments/sample_return.csv') 
        return (df.to_json(orient='split'))

#Getting Data Callback

#Controls - Orders to Cart
@app.callback(Output('ctrl-o_to_c','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def ctrl_o_to_c(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'orders_to_cart_ratio',exp_id)
    #return("{:.2f}".format(metric))
    return('N/A')
#Control - Average Kits Requests
@app.callback(Output('ctrl-avg_kits_requested','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def ctrl_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'average_kits_requested',exp_id)
    return("{:.2f}".format(metric))
# Control - Total Kits Returned
@app.callback(Output('ctrl-total_kits_requested','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def ctrl_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'total_kits_returned',exp_id)
    return("{:.2f}".format(metric))

#Control Sample to Shipped Ratio
@app.callback(Output('ctrl-sample_to_shipped_ratio','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def ctrl_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'sample_to_kit_delivered_ratio',exp_id)
    return("{:.2f}".format(metric))

##### Experiment Callback
#Exp - Orders to Cart
@app.callback(Output('exp-o_to_c','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def exp_o_to_c(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'orders_to_cart_ratio',exp_id)
    #return("{:.2f}".format(metric))
    return('N/A')
#Exp - Average Kits Requests
@app.callback(Output('exp-avg_kits_requested','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def exp_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'average_kits_requested',exp_id)
    return("{:.2f}".format(metric))

#Exp Total Kits Requested
@app.callback(Output('exp-total_kits_returned','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def exp_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'total_kits_returned',exp_id)
    return("{:.2f}".format(metric))

#Exp Sample to Shipped Ratio
@app.callback(Output('exp-sample_to_shipped_ratio','children'),
                [Input('submit_button','n_clicks'),
                     Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def exp_avg_kits(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'sample_to_kit_delivered_ratio',exp_id)
    return("{:.2f}".format(metric))


# Average Days for Kit Return
@app.callback(Output('ctrl-average_days_to_return','children'),
                [Input('submit_button','n_clicks'),
                    Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def ctrl_avg_kit_return_days(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'kit_received_time_in_days',exp_id)
    return ("{:.2f}".format(metric))

@app.callback(Output('exp-average_days_to_return','children'),
                [Input('submit_button','n_clicks'),
                    Input('table_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def exp_avg_kit_return_days(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    df = pd.read_json(data,orient='split')
    metric = get_metric(df,'kit_received_time_in_days',exp_id)
    return ("{:.2f}".format(metric))

# Cool Return Percentages Chart
@app.callback(Output('sample_return_days','figure'),
                [Input('submit_button','n_clicks'),
                    Input('sample_return_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def sample_return_by_day(submit_button,data,experiment_name,clin_product):
    exp_id = get_exp_id(experiment_name,clin_product,'control')[:-2]
    df = pd.read_json(data,orient='split')
    ctrl, exp = process_data(df,exp_id)
    ctrl_line = go.Scatter(
            x = [0] + list(ctrl['time_to_sample_return'].values),
            y = [0] + list(ctrl['percent_returned'].values),
            mode = 'lines+markers',
            name = 'Control'
        )
    exp_line = go.Scatter(
            x = [0] + list(exp['time_to_sample_return'].values),
            y = [0] + list(exp['percent_returned'].values),
            mode = 'lines+markers',
            name = 'Experiment'
    )
    figure = go.Figure(
        data = [ctrl_line,exp_line],
        layout = go.Layout(
            title = 'Time to Sample Return (Days)',
            height = 700,
            width = 1200,
            xaxis = dict(
                        title='Kit Return Time\n(Sample Accessioned - Kit Ship Date)',
                        titlefont = dict(size=20)
                    ),
            yaxis = dict(
                        title='Percentage of Kits Returned (%)',
                        titlefont = dict(size=20)
                    )
        )
    )
    return(figure)

#Patient Program Donut Chart
@app.callback(Output('programs_donut','figure'),
                [Input('submit_button','n_clicks'),
                     Input('programs_hidden_div','children')],
                [State('experiment_selector','value'),
                    State('product_dropdown','value')])
def donut_chart_control(submit_button,data,experiment_name,clin_product):
    data = pd.read_json(data,orient='split')

    ctrl_exp_id = get_exp_id(experiment_name,clin_product,'control')
    ctrl = data[data['checkout_version'] == ctrl_exp_id]

    exp_exp_id = get_exp_id(experiment_name,clin_product,'experiment')
    exp = data[data.checkout_version == exp_exp_id]

    fig = {
        "data":[
            {
                'values':list(ctrl['program_count'].values),
                'labels':list(ctrl['program'].values),
                'domain':{'column':0},
                "hoverinfo":"label+percent+name",
                "hole":.4,
                "type":"pie"
            },
            {
                'values':list(exp['program_count'].values),
                'labels':list(exp['program'].values),
                'domain':{'column':1},
                'textposition':'inside',
                "hoverinfo":"label+percent+name",
                "hole":.4,
                "type":"pie"
            }
        ],
    "layout":{
            "height":600,
            'width':1200,
            "title":'Patient Program Distributions',
            "grid":{"rows":1,'columns':2},
            'annotations':[
                {
                    'font':{
                        "size":20
                    },
                    'showarrow':False,
                    'text':'Control',
                    "x":.2,
                    'y':.5
                },
                {
                    'font':{
                        "size":20
                    },
                    'showarrow':False,
                    'text':'Experiment',
                    'x':.83,
                    'y':.5
                }
            ]
        }
    }
    figure = go.Figure(fig)
    return figure
# @app.callback(Output('latest_pull','children'),
#                 [Input('interval_component','n_intervals')])
# def update_pull_date(n):
#     return time.strftime('%b %d, %Y %H:%M', \
#         time.localtime(os.path.getmtime('data/current/checkout_experiments/table.feather')))    


## Run 
if __name__ == "__main__":
    app.run_server()
