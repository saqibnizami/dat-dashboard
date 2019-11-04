from configparser import ConfigParser
import psycopg2
import sys
import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)

import plotly.offline as pyo
import plotly.graph_objs as go
from app import app
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from warnings import filterwarnings
filterwarnings('ignore')

dft = pd.read_csv('data/df_20190114-110105.csv', index_col=0)
dft.index = pd.to_timedelta(dft.index)
# dash app dropdown 
# initialize dash app
def graph_campaign(camp, y):
    amount_options = ['billed_amount', 'charge', 'allowed_amount', 'payment']
    order_options = ['order_id']
    if y in order_options:
        campdf = dft[dft['utm_campaign']==camp]
        ydf = dft[dft['utm_campaign']==camp].groupby('timedelta')['order_id'].count().cumsum()
        trace = go.Scatter(y = ydf,
                          x = ydf.index.days,
                          mode = 'lines+markers',
                          name = str(camp),
                          connectgaps=True)
    else: 
        campdf = dft[dft['utm_campaign']==camp].resample('D').sum().cumsum()
        trace = go.Scatter(y = campdf[y],
                          x = campdf.index.days,
                          mode = 'lines+markers',
                          name = str(camp),
                          connectgaps=True)
    return trace
def insurance_bar(camp, y):
    campdf = dft[dft['utm_campaign']==camp].sort_values('payment', 
                                                        ascending=False).head(5)
    trace = go.Bar(y = campdf[y],
                      x = campdf['payer_name'],
                      name = str(camp))
    return trace
def utm_medium(camp):
    campdf = dft[dft['utm_campaign']==camp]
    trace = go.Bar(y = campdf['utm_medium'].value_counts().values,
                    x = campdf['utm_medium'],
                    name = str(camp))
    return trace

# load data 
# df = pd.read_csv("./df_20190114-110105.csv")
summary ='''
## Summary
This Dashboard is designed to help track Marketing Campaign performance over 
the selected campaigns' lifetime. It is measured from 'Days After Start' to
normalize dates.

## Usage
1. Use the first dropdown to select your Campaigns of interest based on UTM names.
2. Use the second dropdown to select a metric:
    >`order_id` = Order Volume
    >
    >`payment` = Cumulative Payment Received
***
Please address requests, questions, or comments to:

Saqib Nizami, Data Analytics, NYC.diff 
- [E-mail](mailto:saqib.nizami@ubiome.com)
- [Slack](https://ubiome.slack.com/messages/DD5F1SN02)
'''
campaigns = dft['utm_campaign'].unique()
y_options = ['order_id', 'billed_amount', 'charge', 'allowed_amount', 'payment']

layout = html.Div([
    html.Div([
        html.Img(src="http://daks2k3a4ib2z.cloudfront.net/57fc663070f215f15acf3"+\
             "fa1/5807eb69e8ffbad5081b9691_uBiome_Logo_F16_RGB_Legacy-p-800"+\
             "x182.png", width='200', height='45.5',
             style = {'display':'inline-block'}),
        html.H1(["Marketing Campaign: Waterfall"], 
            style = {'display':'inline-block',
                     'font-family':'Helvetica',
                     'color':'#00536e',
                     'font-size':'40px',
                     'padding-left':'20px'}),
        html.Div([dcc.Markdown(summary)],
             style = {'display':'inline-block',
                     'font-family':'Helvetica',
                     'color':'#00536e'}),
        html.Hr(),
    ]),
    html.Div([
        dcc.Dropdown(
            options=[{'label': i, 'value': i} for i in campaigns],
            placeholder='Select UTM Campaign',
            multi=True,
            id='x-drop'
        )], style = {'width':'45%', 'display':'inline-block'}),    
    html.Div([
        dcc.Dropdown(
            options=[{'label': i, 'value': i} for i in y_options],
            placeholder='Select Y-Axis',
            multi=False,
            id='y-drop'
        )], style = {'width':'45%', 'display':'inline-block'}),
    html.Div([dcc.Graph(id='timeline')]),
    html.Div([
        html.Div([dcc.Graph(id='topins')], 
                 style = {'width':'45%', 'display':'inline-block'}),
        html.Div([dcc.Graph(id='utmsource')], 
                 style = {'width':'45%', 'display':'inline-block'})
    ]),
])

@app.callback(Output('timeline', 'figure'),
              [Input('x-drop','value'),
              Input('y-drop','value')])
def timeline(value1, value2):
    return {'data':[graph_campaign(i, value2) for i in value1],
            'layout':{'title':'Campaign Performance Timeline',
                      'xaxis':{'title':'Days After Campaign Start'},
                      'yaxis':{'title':str(value2)}
                     }
           }
@app.callback(Output('topins', 'figure'),
              [Input('x-drop','value'),
               Input('y-drop','value')])
def InsuranceByCampaign(value1, value2):
    return {
        'data':[insurance_bar(i, value2) for i in value1],
            'layout':{'title':'Best Payers in Campaign',
                      'xaxis':{'title':'Payer Name'},
                      'yaxis':{'title':str(value2)}
                     }
    }
@app.callback(Output('utmsource', 'figure'),[Input('x-drop','value')])
def InsuranceByCampaign(value):
    return {
        'data':[utm_medium(i) for i in value],
            'layout':{'title':'UTM Sources By Campaign',
                      'xaxis':{'title':'UTM Source'}
                     }
    }

# if __name__ == '__main__':
#     app.run_server(debug=False)