# #%%
# import os
# import ast
# try:
# 	os.chdir(os.path.join(os.getcwd(), 'dash_apps/dash'))
# 	print(os.getcwd())
# except:
# 	pass

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import os
from app.utils.url_helper import relpath

from app import app, logger

from app.apps import ops_metrics_summary
from app.apps import lab_ops_metrics
from app.apps import checkout_analysis
from app.apps import marketing_ops_metrics
from app.apps import billing_ops_metrics
#from app.apps import marketing_experiments

# initialize the server here
server = app.server
# app.config.suppress_callback_exceptions = True
# app.scripts.config.serve_locally = False

# the following finds all files in the /apps/ folder and places the file names
# into a dictionary

dashboards = dict()
for file in os.listdir('app/apps'):
    if file.endswith(".py") and file != "__init__.py":
        dashboards[os.path.splitext(file)[0].replace("_", " ").title()] = \
                "/{}".format(os.path.splitext(file)[0])


#%%


###############################################################################
#### NAVBAR
###############################################################################



navbar = html.Div([
    dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("", href=relpath("/"))),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Questions? Contact:",
            children=[
                dbc.DropdownMenuItem("Data Analytics Team"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Saqib Nizami",
                                     href="mailto:saqib.nizami@ubiome.com"),
                dbc.DropdownMenuItem("Andrew Cho",
                                     href="mailto:andrew.cho@ubiome.com"),
                dbc.DropdownMenuItem("Ian Mathew",
                                     href="mailto:ian.mathew@ubiome.com"),
                dbc.DropdownMenuItem("Doh Jung",
                                     href="mailto:doh.jung@ubiome.com"),
            ],
        ),
    ],
    brand="uBiome Data Analytics Dashboards",
    brand_href=relpath("/"),
    sticky="top",
    brand_style={'font-size':'1em'},
    dark=True,
    color='dark'
)])



###############################################################################
#### BODY
###############################################################################
logo = html.Img(src=app.get_asset_url("datdash-main.png"),
            width='332',height='254',
            style={'display':'block',
                    'margin-left':'auto',
                    'margin-right':'auto'})


main = \
dbc.Col([
        dbc.ListGroup([logo]),
        html.Div(id='none',children=[],style={'display': 'none'}),
        dbc.ListGroup([],id="links")
        ],
        width={'size':6, 'offset':3})


body = dbc.Card(
    [main],
    body=True,
    id="content")





###############################################################################
#### LAYOUT
###############################################################################



app.layout = html.Div([navbar, dcc.Location(id='url', refresh=False), body])



###############################################################################
#### CALLBACKS
###############################################################################



@app.callback(
    Output('links','children'),
    [Input('none', 'children')])
def generateLinks(children):
    linklist = []
    for k,v in dashboards.items():
        link = dbc.CardLink("{}".format(k),
                            href=relpath(v),
                            style={'text-align':'center'})
        try:
            desc = dbc.CardText(eval(v.replace("/","")).description,
                                style={'text-align':'center'})
            linklist.append(dbc.Card([link,desc],
                                     body=True,
                                     color='light',
                                    #  outline=False,
                                     inverse=False))
        except Exception as e:
            logger.exception('')
            linklist.append(dbc.Card([link],
                            body=True,
                            color='light',
                            # outline=False,
                            inverse=False))

    return linklist


@app.callback(
    Output('content', 'children'),
    [Input('url','pathname')])
def locationDisplay(pathname):
    if pathname:
        last_path = '/{}'.format(pathname.rsplit('/', 1).pop())
        if last_path in dashboards.values():
            for k,v in dashboards.items():
                if last_path == v:
                    logger.info('Serving report {}'.format(v))
                    return eval(v.replace("/","")).layout
    logger.info('Serving main page under path {}'.format(pathname))
    return main




if __name__ == '__main__':
   app.run_server(debug=False, dev_tools_hot_reload=False)
