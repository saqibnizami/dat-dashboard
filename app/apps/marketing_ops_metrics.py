from datetime import datetime as dt

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from plotly import tools

from app import app, logger
from ..subapps import carts_orders as cartstab
from ..subapps import orders as orderstab

# adding flask-caching for dataset
# from flask_caching import Cache
#%% CACHE #####################################################################
# using filesystem cache
# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'filesystem',
#     'CACHE_DIR': 'cache-directory'
# })
# TIMEOUT = 60
#%% DESCRIPTION ###############################################################

description = "Measure Marketing efforts and performance"

class MarketingOpsDAO:

    @staticmethod
    def get_orders():
        try:
            df_orders = pd.read_csv('~/data_pulls/marketing_ops_metrics/mode_orders.csv')
            return df_orders
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_fb_spend():
        try:
            fb_spend = pd.read_csv('~/data_pulls/marketing_ops_metrics/fb_spend.csv')
            return fb_spend
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_ga_spend():
        try:
            ga_spend = pd.read_csv('~/data_pulls/marketing_ops_metrics/ga_spend.csv')
            return ga_spend
        except Exception as e:
            logger.exception('')


orders = MarketingOpsDAO.get_orders()
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
    
# #%%
# display(map_subchan_w,#.sort_values('created_at', ascending=False).head(), 
#         map_subchan_w.shape)
#%%
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
# ! Facebook spending
# manually exported facebook information
# TODO: use facebook ytd spend script to make a new table in analytics
# fb = pd.read_csv("data/current/mko/fb_ytdspend.csv")
fb = MarketingOpsDAO.get_fb_spend()
fb['date_start'] = pd.to_datetime(fb['date_start'])
fb['week_number'] = fb['date_start'].dt.week
# fb['spend'] = fb['spend'].astype('float')
# display(fb.shape, fb.head(100))
#%%
fb_weekly = \
fb.groupby(['week_number'])\
    .agg({'spend': 'sum'})\
        .round(2)\
            .reset_index()
#%%
fb_weekly.head()
#%% Merge FB spend with orders ################################################
fb_orders = map_subchan_w[map_subchan_w['mapped_sub_channel'] == 'Facebook']
# display(fb_orders, fb_weekly)
fb_w = fb_weekly.merge(fb_orders, how='left', on='week_number')
fb_w['cac'] = fb_w['spend'] / fb_w['order_id_modified']
#%% 
# ! Google Ads Spending

ga_orders = map_subchan_w[map_subchan_w['mapped_sub_channel'] == 'Google']

ga = MarketingOpsDAO.get_ga_spend()
ga['day'] = pd.to_datetime(ga['day'])
ga['week_number'] = ga['day'].dt.week
# ga['Cost'] = ga['Cost'].str.replace(',','')
ga['spend'] = ga['spend'].astype('float')
# display(ga)
#%%
ga_weekly = \
ga.groupby(['week_number'])\
    .agg({'spend': 'sum'})\
        .round(2)\
            .reset_index()
# display(ga_weekly)

#%%
ga_w = ga_weekly.merge(ga_orders, how='left', on='week_number')
ga_w['cac'] = ga_w['spend'] / ga_w['order_id_modified']
#%%
# display(ga_w, fb_w)
#%%
other_subchan = \
map_subchan_w[(map_subchan_w['mapped_sub_channel'] != 'Google') &\
                (map_subchan_w['mapped_sub_channel'] != 'Facebook')]
#%%

#%%
odf = \
orders[['created_at','mapped_sub_channel','order_id_modified', 'week_number']]
odf['mapped_sub_channel'] = odf['mapped_sub_channel'].fillna('No Channel')
# display(odf[odf['mapped_sub_channel'].isnull()], odf)
#%%
o_w = \
odf.groupby(['mapped_sub_channel','week_number'])\
    .agg({'order_id_modified':'nunique'}).reset_index()
# display(o_w)
#%%
fbow=\
o_w.merge(fb_w, how='left', on=['week_number','mapped_sub_channel'])
gafbow = \
fbow.merge(ga_w, how='left', on=['week_number','mapped_sub_channel'])
#%%
# display(gafbow)
#%%
gafbow['spend'] = gafbow['spend_x'].combine_first(gafbow['spend_y'])
gafbow['kit_1_orders'] = gafbow['order_id_modified_x'].combine_first(gafbow['order_id_modified_y'])
#%%
df = \
gafbow[['mapped_sub_channel','week_number', 'spend','kit_1_orders']]
#%%
# display(df)
#%%
# ! totals 
totals = \
    df[['week_number','spend','kit_1_orders']]
totals=\
totals.groupby('week_number')\
    .agg({'spend':'sum','kit_1_orders':'sum'})\
        .reset_index()
totals['cac'] = totals['spend'] / totals['kit_1_orders']
totals['cac'] = totals['cac'].round(2)
#%%
# display(totals)
#%% Set x&y for plotting ######################################################
x = fb_w['week_number']
y_o = fb_w['order_id_modified']
y_s = fb_w['spend']
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
            y = totals['spend'],
            x = totals['week_number'],
            name = 'Combined Spend',
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
    x=totals['week_number'],
    y=totals['cac'],
    text=totals['cac'],
    name = 'Combined CAC',
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
# for channel in channels:
#     _ = df[df['mapped_sub_channel'] == channel]
#     x = _['week_number']
#     y = _['order_id_modified']
#     trace = go.Bar(
#                 y = y,
#                 x = x,
#                 name = channel,
#                 text=y,
#                 textposition="outside",
#                 textfont= dict(
#                     size=12
#                 ),
#                 # keeps the text in view
#                 constraintext='outside',
#                 cliponaxis=False,
#                 marker=dict(
#                     color='rgb(158,202,225)',
#                     line=dict(
#                         color='rgb(8,48,107)',
#                         width=1.5))
#                         )
#     data.append(trace)
#%%
# totals = map_subchan_w.groupby('week_number').sum().reset_index()

total_trace = go.Bar(
            y = totals['kit_1_orders'],
            x = totals['week_number'],
            name = 'Totals',
            text=totals['kit_1_orders'],
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
# data.append(total_trace)
# fig = tools.make_subplots(rows=len(data)+2,
#                         cols=1,
#                         shared_xaxes=True,
#                         subplot_titles=(channels[0],
#                                         channels[1],
#                                         channels[2],
#                                         channels[3],
#                                         'Total Orders',
#                                         'Spend',
#                                         'CAC'),
#                         vertical_spacing = .10
#                             )
fig = tools.make_subplots(rows=3,
                        cols=1,
                        shared_xaxes=True,
                        subplot_titles=('Total Orders',
                                        'Combined Spend',
                                        'Blended CAC'),
                        vertical_spacing = .10
                            )
# for i in range(len(data)):
#     fig.append_trace(data[i], i+1, 1)
    # fig.append_trace(data[i], i+1, 2)
# add total
fig.append_trace(total_trace, 1, 1)
# add fb spend
fig.append_trace(spendtrace, 2, 1)
# add CAC
fig.append_trace(trace_c, 3, 1)
#%%
# print(fig)
#%%
fig['layout'].update(
                    margin=dict(pad = 50),
                    height= 450,
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
                            text='Combined Spend',
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
                            text='Blended CAC',
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

for i in range(0,3):
    fig['layout']['yaxis{}'.format(i+1)].update(anchor = 'x',
                                                visible=False, 
                                                layer="below traces")
# pyo.plot(fig)

#%%
order_volume = go.Scatter(y = totals['kit_1_orders'],
                        x = totals['week_number'],
                        mode = 'lines+markers',
                        name = 'Order Volume',
                        connectgaps=True)
                        # fill='tozeroy')
cac_trace = go.Scatter(y = totals['cac'],
                        x = totals['week_number'],
                        mode = 'lines+markers',
                        name = 'CAC',
                        connectgaps=True)
                        # fill='tozeroy')
order_cac ={
    'data':[order_volume, cac_trace],
    'layout':{'xaxis':{'title':'2019 Week Number','showgrid':False},
                'yaxis':{'title':'Orders/CAC', 'showgrid':False}
                }
            }

#%% SUMMARY ###################################################################

summary ='''
Metrics for Marketing operations. This dashboard provides information on orders
generated from marketing efforts.
'''
topcard = dbc.Card(
    [
        dbc.CardHeader("Marketing Ops Metrics", 
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
                dbc.Row(
                    [
                        dbc.Col([
                            html.H5('Date Selection'),
                            dcc.DatePickerRange(
                                id='mko-date-picker',
                                min_date_allowed=dt(2019, 1, 1),
                                initial_visible_month=dt(2019, 1, 1),
                                end_date="{:%Y-%m-%d}".format(dt.now()),
                                start_date="2019-01-01"
                                # start_date="{:%Y-%m-%d}".format(dt.now()-timedelta(30))
                                )
                            ]
                        ),
                        dbc.Col([
                            html.H5("Time Frequency"),
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Daily', 'value': 'daily'},
                                    {'label': 'Weekly', 'value': 'weekly'},
                                    {'label': 'Month', 'value': 'monthly'}
                                    ],
                                value='weekly',
                                labelStyle={'display': 'inline-block',
                                            'padding-right' : '50px'}
                                    )
                        ])
                    ]
                ),
            ])])

#%% TABS ######################################################################

mko = \
dbc.Col([
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
orders = orderstab.layout

tabs = dbc.Tabs(
    [
        dbc.Tab(mko, label='Marketing Ops'),
        dbc.Tab(orders, label="Order Metrics"),
        # dbc.Tab(campaigns, label="Marketing UTM"),
        dbc.Tab(carts, label="Cart Metrics")
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