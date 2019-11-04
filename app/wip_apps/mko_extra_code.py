#%% Pull Orders and UTM data ##################################################
#
###############################################################################

# possibly use a spider chart to visualize the number of orders by utm_source
# and by week
# orders = SQLtoDF(sqlfile="queries/mko/mode_orders.pgsql", 
#                  database="backend",
#                  creds=pg, 
#                  driver="postgres",
#                  foldername="mko" ,
#                  tablename="orders_utms")

# script running time: %%timeit -n 1 -r 1
# 1min 17s ± 0 ns per loop (mean ± std. dev. of 1 run, 1 loop each)
# orders = pd.read_pickle("data/orders_utms_backend_pull_at__20190307_131203.pkl")
# Get week numbers from datetime
# orders = pd.read_csv('data/current/mko/orders_utms_backend_pull_at_20190318_145231.csv')
# orders['created_at'] = pd.to_datetime(orders['created_at'])
# orders['week_number'] = orders['created_at'].dt.week

# df = pd.read_pickle("data/orders_utms_backend_pull_at__20190304_162455.pkl")
#%% APP #######################################################################
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app.scripts.config.serve_locally = False
# app.config['suppress_callback_exceptions'] = True
#%%
# display(orders.shape, sorted(orders.columns),
#         orders['created_at'].min(), orders['created_at'].max(),
#         orders[sorted(orders.columns)].head())
# fb = pd.read_csv('data/current/mko/fb_spend_export.csv')
# x = fb_weekly['week_number']
# y = fb_weekly['Amount Spent (USD)']
# #%%
# def current_Table():
#     df = fb_w.sort_values('week_number', ascending=False).head(3)
#     table = dash_table.DataTable(
#         id='mko-current-fb-table',
#         columns=[{'name': i, 'id':i} for i in df.columns],
#         data=df.to_dict("rows")
#         # pagination_settings={'current_page': 0},
#         # pagination_mode='fe'
#         )
#     return table
#%%
# currenttable = fb_w.sort_values('week_number', ascending=False).head(3)
# current_dt = dash_table.DataTable(
#     id='mko-current-fb-table',
#     columns=[{'name': i, 'id':i} for i in currenttable.columns],
#     data=currenttable.to_dict("rows")
#     # pagination_settings={'current_page': 0},
#     # pagination_mode='fe'
#     )
#%%
# x = fb_weekly['week_number']
# y = fb_weekly['Amount Spent (USD)']

# spend_data = [go.Bar(y = y,
#                 x = x,
#                 name = 'Facebook Spend',
#                 text=y,
#                 textposition="outside",
#                 textfont=dict(
#                     size=12
#                 ),
#                 # keeps the text 
#                 cliponaxis=False,
#                 # marker=dict(
#                 #     color='rgb(158,202,225)',
#                 #     line=dict(
#                 #         color='rgb(8,48,107)',
#                 #         width=1.5))
#                         )]

# spend_layout = go.Layout(
#     # title='Facebook Weekly Spend',
#     margin=dict(pad = 50),
#     # title='Channel Specific Order Volumes by Week',
#     xaxis= dict(
#         title=dict(
#             text='Week Number',
#             font=dict(size=20)
#         ),
#         tickmode='linear',
#         tickfont=dict(size=14),
#         side='top',
#         showgrid=True,
#         mirror=False,
#         showline=True,
#         linewidth=3
#     ),
#     autosize = True,
#     showlegend = False
# )
# spend_fig =go.Figure(data=spend_data, layout=spend_layout)

#%% 
# utm_mapping ="""
# | UTM Source  | UTM Medium  | Mapped Category  | Mapped Channel  | Mapped Sub-Channel  |
# |------------|-------------|------------------|-----------------|---------------------|
# | `facebook` | `paid_social` | Online Performance Marketing | Paid Social | Facebook |
# | (direct)  | (none)       | Brand Marketing | Organic | Direct |
# | `google`   | `organic`  | Brand Marketing | Organic | Google |
# | `google`   | `cpc`  | Online Performance Marketing | SEM - Performance | Google |
# | `m.facebook.com` | `referral` | Brand Marketing | Social | Facebook |
# | `SmartGut` | `email` | Online Performance Marketing | Email | Newsletter | 
# | `Blog`  | `email` | Online Performance Marketing | Email | Newsletter |
# | `facebook.com`  | `referral` | Brand Marketing | Social | Facebook |
# """
#%% APP #######################################################################
#%%
# display(fb_w)

#%%
# thisweek = pd.datetime.now().isocalendar()[1]
# # get the last 3 weeks
# fb_w.sort_values('week_number', ascending=False).head(3)
# # get the last two week before the current week. (Completed weeks)
# fb_w.sort_values('week_number', ascending=False).head(3).iloc[1:,:]

#%%

#%%
# def currentmetrics():
#     mask = (cart_no['cart_created_date'] > s) & (cart_no['cart_created_date'] <= e)
#     cdf =cart_no[mask]
#     cdf_sum = cdf.groupby(['program']).agg({'cart_number':'sum'}).reset_index()
#     totals =[(i, cdf_sum[cdf_sum['program'] == i].iloc[0]['cart_number']) \
#         for i in cdf_sum['program']]
#     cards = []
#     for x in totals:
#         card = \
#         dbc.Card(
#         [
#             # dbc.CardHeader("{}".format(x[0])),
#             dbc.CardBody(
#                 [
#                     dbc.CardTitle("{}".format(x[1]), style={'font-size':'2em'}),
#                     dbc.CardText("{}".format(x[0].replace("_"," "))),
#                 ]
#             ),
#         ])
#         cards.append(card)
#     return cards

#%%
# fb_w.sort_values('week_number', ascending=False).head(3)

# #%%
# # current week
# orders[orders['created_at'] == orders['created_at'].dt.date.max()]

# #%%
# orders['created_date'] = orders['created_at'].dt.date


# #%%
# pd.datetime.now().date()

# #%%
# pd.datetime.now().date()  orders['created_date'][0]
