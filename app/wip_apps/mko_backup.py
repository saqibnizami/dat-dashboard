# consolidated marketing key ops dash
#%% IMPORTS ###################################################################

import hvac
import os
import sqlalchemy as db
import psycopg2
import sys
import pandas as pd
import numpy as np
from plotly import tools
import plotly.offline as pyo
import plotly.graph_objs as go
from datetime import datetime as dt
from datetime import timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_table
from subapps import carts_orders as cartstab
from subapps import cashpay_metrics as cashpaytab
# import the datapull file to use scripts
from pull_scripts import datapull as pull
from pull_scripts import loadNewest as load 
# disable to test just this app
from app import app

#%% DESCRIPTION ###############################################################

description = "Marketing Key Operations Metrics Dashboard"

#%% PULL DATA #################################################################

# # use scripts from pull_scripts/datapull.py to get data
# queryfile = 'queries/mko/mode_orders.pgsql'
# id_path = '~/.vault/dash_vault_id'
# token_path = '~/.vault/dash_vault_token'
# # get creds for pg from vault
# pg = pull.get_creds(id_path, token_path, 'pg')

# orders = pull.SQLtoDF(sqlfile=queryfile, 
#                     database="backend",
#                     creds=pg, 
#                     driver="postgres",
#                     foldername="mko",
#                     tablename="orders_utms")
#%% LOAD DATA ################################################################

orders = load.loadNewest(foldername='mko', tablename='orders_utms')
orders['created_at'] = pd.to_datetime(orders['created_at'])
orders['week_number'] = orders['created_at'].dt.week

#%% UTM Mapping ###############################################################
# Category: Online Performance Marketing
fb_mask = (orders['utm_source'] == 'facebook') & \
            (orders['utm_medium'] == 'paid_social')
orders.loc[fb_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[fb_mask, 'mapped_channel'] = 'Paid Social'
orders.loc[fb_mask, 'mapped_sub_channel'] = 'Facebook'

g_cpc_mask = (orders['utm_source'] == 'google') & \
                (orders['utm_medium'] == 'cpc')
orders.loc[g_cpc_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[g_cpc_mask, 'mapped_channel'] = 'SEM - Performance'
orders.loc[g_cpc_mask, 'mapped_sub_channel'] = 'Google'

sg_mask = (orders['utm_source'] == 'SmartGut') & \
            (orders['utm_medium'] == 'email')
orders.loc[sg_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[sg_mask, 'mapped_channel'] = 'Email'
orders.loc[sg_mask, 'mapped_sub_channel'] = 'Newsletter'

sj_mask = (orders['utm_source'] == 'SmartJane') & \
            (orders['utm_medium'] == 'email')
orders.loc[sj_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[sj_mask, 'mapped_channel'] = 'Email'
orders.loc[sj_mask, 'mapped_sub_channel'] = 'Newsletter'

ex_mask = (orders['utm_source'] == 'SmartJane') & \
            (orders['utm_medium'] == 'email')
orders.loc[ex_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[ex_mask, 'mapped_channel'] = 'Email'
orders.loc[ex_mask, 'mapped_sub_channel'] = 'Newsletter'

blog_org_mask = (orders['utm_source'] == 'blog') & \
                    (orders['utm_medium'] == 'organic')
orders.loc[blog_org_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[blog_org_mask, 'mapped_channel'] = 'Organic'
orders.loc[blog_org_mask, 'mapped_sub_channel'] = 'Newsletter'

blog_email_mask = (orders['utm_source'] == 'blog') & \
                    (orders['utm_medium'] == 'email')
orders.loc[blog_email_mask, 'mapped_category'] = 'Online Performance Marketing'
orders.loc[blog_email_mask, 'mapped_channel'] = 'Organic'
orders.loc[blog_email_mask, 'mapped_sub_channel'] = 'Newsletter'

# Category: Brand Marketing
g_org_mask = (orders['utm_source'] == 'google') & \
                (orders['utm_medium'] == 'organic')
orders.loc[g_org_mask, 'mapped_category'] = 'Brand Marketing'
orders.loc[g_org_mask, 'mapped_channel'] = 'Organic'
orders.loc[g_org_mask, 'mapped_sub_channel'] = 'Google'

fb_ref_mask = (orders['utm_source'] == 'm.facebook.com') & \
                (orders['utm_medium'] == 'referral')
orders.loc[fb_ref_mask, 'mapped_category'] = 'Brand Marketing'
orders.loc[fb_ref_mask, 'mapped_channel'] = 'Social'
orders.loc[fb_ref_mask, 'mapped_sub_channel'] = 'Facebook'

fb_ref_mask2 = (orders['utm_source'] == 'facebook.com') & \
                    (orders['utm_medium'] == 'referral')
orders.loc[fb_ref_mask2, 'mapped_category'] = 'Brand Marketing'
orders.loc[fb_ref_mask2, 'mapped_channel'] = 'Social'
orders.loc[fb_ref_mask2, 'mapped_sub_channel'] = 'Facebook'

none_mask = (orders['utm_source'].isnull()) & \
                (orders['utm_medium'].isnull())
orders.loc[none_mask, 'mapped_category'] = 'Brand Marketing'
orders.loc[none_mask, 'mapped_channel'] = 'Organic'
orders.loc[none_mask, 'mapped_sub_channel'] = 'Direct'
#%% Group by Mapped values ####################################################
# get a weekly'nunique of 'kit1' orders by mapped_category
map_cat_w = \
orders.set_index('created_at')\
            .groupby(['mapped_category', 'week_number'])\
                .resample('W')\
                    .agg({'order_id_modified':'nunique'})\
                        .reset_index()
# display(map_cat_w,#.sort_values('created_at', ascending=False).head(), 
#         map_cat_w.shape)

# get a weekly'nunique of 'kit1' orders by channel
map_channel_w = \
orders.set_index('created_at')\
            .groupby(['mapped_channel','week_number'])\
                .resample('W')\
                    .agg({'order_id_modified':'nunique'})\
                        .reset_index()
# display(map_channel_w,#.sort_values('created_at', ascending=False).head(), 
#         map_channel_w.shape)

# get a weekly'nunique of 'kit1' orders by sub-channel
# ! removed the .resample('W')\ - unnecessary with week_number
map_subchan_w = \
orders.set_index('created_at')\
            .groupby(['mapped_sub_channel', 'week_number'])\
                    .agg({'order_id_modified':'nunique'})\
                        .reset_index()
    
# display(map_subchan_w,#.sort_values('created_at', ascending=False).head(), 
#         map_subchan_w.shape)

# get a weekly'nunique of 'kit1' orders for the order funnel
ordfun_w = \
orders.set_index('created_at')\
            .groupby(['order_funnel'])\
                .resample('W')\
                    .agg({'order_id_modified':'nunique'})\
                        .reset_index()\
                            .sort_values(['created_at', 'order_funnel'], 
                                         ascending=False)
# display(ordfun_w.head(), ordfun_w.shape)
#%% Facebook Spend ############################################################
# manually exported facebook information
# TODO: use facebook ytd spend script to make a new table in analytics
fb = pd.read_csv("data/current/mko/fb_ytdspend.csv")
fb['date_start'] = pd.to_datetime(fb['date_start'])
fb['week_number'] = fb['date_start'].dt.week
fb['amount_spent'] = fb['amount_spent'].astype('float')
# display(fb.shape, fb.head(20))

fb_weekly = \
fb.groupby(['week_number'])\
    .agg({'amount_spent': 'sum'})\
        .round(2)\
            .reset_index()
#%% Merge FB spend with orders ################################################
fb_orders = map_subchan_w[map_subchan_w['mapped_sub_channel'] == 'Facebook']
# display(fb_orders, fb_weekly)
fb_w = fb_weekly.merge(fb_orders, how='left', on='week_number')
fb_w['cac'] = fb_w['amount_spent'] / fb_w['order_id_modified']
#%%
# display(fb_w)

#%% Set x&y for plotting ######################################################
x = fb_w['week_number']
y_o = fb_w['order_id_modified']
y_s = fb_w['amount_spent']
y_c = fb_w['cac'].round(2)

#%% define traces for plotting ################################################
trace_o = go.Bar(
    x=x,
    y=y_o,
    text=y_o,
    textposition= 'outside',
    textfont=dict(size=14),
    cliponaxis=False,
    marker = dict(
        color='rgb(158,202,225)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.5),
        ),
    opacity=0.6
    )
# trace_s = go.Bar(
#     x=x,
#     y=y_s,
#     text=y_s,
#     textposition= 'outside',
#     marker = dict(
#         color='rgb(58,200,225)',
#         line=dict(
#             color='rgb(8,48,107)',
#             width=1.5),
#         ),
#     opacity=0.6
#     )
spendtrace =\
    go.Bar(
            y = y_s,
            x = x,
            name = 'Facebook Spend',
            text=y_s,
            textposition="outside",
            textfont=dict(size=14),
            # keeps the text 
            cliponaxis=False,
            marker=dict(
                color='rgb(220,242,155)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=1.5
                    )
                )
            )
trace_c = go.Bar(
    x=x,
    y=y_c,
    text=y_c,
    name = 'Facebook CAC',
    textposition= 'outside',
    textfont=dict(size=14),
    cliponaxis=False,
    marker = dict(
        color='rgb(58,200,225)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.5),
        ),
    opacity=0.6
    )
# data=[trace_s, trace_c]
# pyo.plot(data)

#%% SUBPLOT CHART #############################################################


# plot orders by channel and add spend
df = map_subchan_w
channels = sorted(df['mapped_sub_channel'].unique())

data = []
for channel in channels:
    _ = df[df['mapped_sub_channel'] == channel]
    x = _['week_number']
    y = _['order_id_modified']
    trace = go.Bar(
                y = y,
                x = x,
                name = channel,
                text=y,
                textposition="outside",
                textfont= dict(
                    size=12
                ),
                # keeps the text in view
                constraintext='outside',
                cliponaxis=False,
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.5))
                        )
    data.append(trace)
#%%
totals = map_subchan_w.groupby('week_number').sum().reset_index()

total_trace = go.Bar(
            y = totals['order_id_modified'],
            x = totals['week_number'],
            name = 'Totals',
            text=y,
            textposition="outside",
            textfont= dict(
                size=12
            ),
            # keeps the text in view
            constraintext='outside',
            cliponaxis=False,
            marker=dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=1.5))
                    )
data.append(total_trace)
fig = tools.make_subplots(rows=len(data)+2,
                        cols=1,
                        shared_xaxes=True,
                        subplot_titles=(channels[0],
                                        channels[1],
                                        channels[2],
                                        channels[3],
                                        'Total Orders',
                                        'Spend',
                                        'CAC'),
                        vertical_spacing = .10
                            )
for i in range(len(data)):
    fig.append_trace(data[i], i+1, 1)
    # fig.append_trace(data[i], i+1, 2)

# add fb spend
fig.append_trace(spendtrace, len(data)+1, 1)
# add CAC
fig.append_trace(trace_c, len(data)+2, 1)
#%%
# print(fig)
#%%
fig['layout'].update(
                    margin=dict(pad = 50),
                    height= 650,
                    # title='Channel Specific Order Volumes by Week',
                    xaxis= dict(
                        anchor='y',
                        title=dict(
                            # text='Order Volume (Kit 1)',
                            font=dict(size=16)
                        ),
                        tickmode='linear',
                        tickfont=dict(size=14),
                        side='top',
                        showgrid=True,
                        mirror=False,
                        showline=True,
                        linewidth=3
                    ),
                    xaxis2= dict(
                        anchor = 'y',
                        title=dict(
                            text='Spend',
                            font=dict(size=16)
                        ),
                        tickmode='linear',
                        tickfont=dict(size=14),
                        side='top',
                        showgrid=True,
                        mirror=False,
                        showline=True,
                        linewidth=3
                    ),
                    xaxis3= dict(
                        anchor = 'y',
                        title=dict(
                            text='CAC',
                            font=dict(size=16)
                        ),
                        tickmode='linear',
                        tickfont=dict(size=14),
                        side='top',
                        showgrid=True,
                        mirror=False,
                        showline=True,
                        linewidth=3
                    ),
                    autosize = True,
                    showlegend = False,
                    # plot_bgcolor='rgba(245, 246, 249, 1)',
                    annotations = [
                        # dict(
                        #     x = 0.0,
                        #     y = 1.05,
                        #     showarrow = False,
                        #     text = "Direct",
                        #     xref = "paper",
                        #     yref = "paper",
                        #     align = "right"
                        #     ),
                        # dict(
                        #     x = 0.0,
                        #     y = 0.85,
                        #     showarrow = False,
                        #     text = "Facebook",
                        #     xref = "paper",
                        #     yref = "paper",
                        #     align = "right"
                        #     ),
                        # dict(
                        #     x = 0.0,
                        #     y = 0.6,
                        #     showarrow = False,
                        #     text = "Google",
                        #     xref = "paper",
                        #     yref = "paper",
                        #     align = "right"
                        #     ),
                        # dict(
                        #     x = 0.0,
                        #     y = 0.35,
                        #     showarrow = False,
                        #     text = "Newsletter",
                        #     xref = "paper",
                        #     yref = "paper",
                        #     align = "right"
                        #     ),
                        # dict(
                        #     x = 0.0,
                        #     y = 0.10,
                        #     showarrow = False,
                        #     text = "Totals",
                        #     xref = "paper",
                        #     yref = "paper",
                        #     align = "right"
                        #     )
                        ],
                    # yaxis = dict(anchor='x', 
                    #             visible=False, 
                    #             layer="below traces"),
                    # yaxis2 = dict(anchor='x'),
                    # yaxis3 = dict(anchor='x'),
                    # yaxis4 = dict(anchor='x')
                    )

for i in range(0,7):
    fig['layout']['yaxis{}'.format(i+1)].update(anchor = 'x',
                                                visible=False, 
                                                layer="below traces")
# pyo.plot(fig)

#%%
order_volume = go.Scatter(y = fb_w['order_id_modified'],
                        x = fb_w['week_number'],
                        mode = 'lines+markers',
                        name = 'Order Volume',
                        connectgaps=True,
                        fill='tozeroy')
cac_trace = go.Scatter(y = fb_w['cac'],
                        x = fb_w['week_number'],
                        mode = 'lines+markers',
                        name = 'CAC',
                        connectgaps=True,
                        fill='tozeroy')
order_cac ={
    'data':[order_volume, cac_trace],
    'layout':{'xaxis':{'title':'2019 Week Number','showgrid':False},
                'yaxis':{'title':'Orders/CAC', 'showgrid':False}
                }
            }

#%% SUMMARY ###################################################################

summary ='''
This dashboard is a part of efforts to standardize operations metrics. 
The focus of this page is to consolidate reporting on carts, orders, and kits.
'''
topcard = dbc.Card(
    [
        dbc.CardHeader("Marketing Key Operations Metrics", 
                        style={'font-size':'2em'}),
        dbc.CardBody(
            [
                dbc.Button("Click here to expand more information on this dashboard", 
                            id="mko-collapse-button", className="mb-3"),
                dbc.Collapse(
                    [
                        dbc.CardTitle("UTM Mapping Logic from Growth Marketing"),
                        # dbc.CardText(dcc.Markdown(utm_mapping)),
                        dbc.CardLink('Link to Solution Document', 
                        href="https://docs.google.com/document/d/1vg4B9ctNpLSBts4QnnPrnH4iYL2blv4f_IjiU9iZACo/edit")
                    ],
                    id='mko-collapse',
                    is_open=False
                ),
                # dbc.Row(
                #     [
                #         dbc.Col([
                #             # html.H5('Date Selection')
                #             # dcc.DatePickerRange(
                #             #     id='mko-date-picker',
                #             #     min_date_allowed=dt(2019, 1, 1),
                #             #     initial_visible_month=dt(2019, 1, 1),
                #             #     end_date="{:%Y-%m-%d}".format(dt.now()),
                #             #     start_date="{:%Y-%m-%d}".format(dt.now()-timedelta(30))
                #             #     )
                #             ]
                #         )
                #     ]
                # ),
            ])])

#%% TABS ######################################################################
marketing_keyops = dbc.Col([
    dbc.Row([
        dbc.Col([
            html.H5("Weekly Order Volume Metrics"),
            dcc.Graph(figure= fig, 
                      id='mko-weekly-bars',
                      config={'displayModeBar':False}),
            html.H5("Order Volume vs. CAC"),
            dcc.Graph(figure = order_cac, id='mko-order-cac'),
        ])
    ])
    ])
carts = cartstab.layout
tabs = dbc.Tabs(
    [
        dbc.Tab(marketing_keyops, label='Marketing Key Ops'),
        dbc.Tab(carts, label="Carts Metrics"),
        # dbc.Tab(campaigns, label="Marketing UTM"),
        dbc.Tab("Funnel", label="Funnel")
    ]
)



# APP LAYOUT ##################################################################

layout = html.Div([topcard,tabs])

# CART TAB CALLBACKS ##########################################################

@app.callback(
    Output("mko-collapse", "is_open"),
    [Input("mko-collapse-button", "n_clicks")],
    [State("mko-collapse", "is_open")],
    )
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
#%%
# if __name__ == "__main__":
#     app.run_server(debug=True, dev_tools_hot_reload=True)