import dash
import dash_bootstrap_components as dbc
from app.lib import logger
import dash_html_components as html


# class CustomDash(dash.Dash):
#     def interpolate_index(self, **kwargs):
#         # Inspect the arguments by printing them
#         print(kwargs)
#         return '''
#         <!DOCTYPE html>
#         <html>
#             <head>
#                 <title>My App</title>
#             </head>
#             <body>

#                 <div id="custom-header">My custom header</div>
#                 {app_entry}
#                 {config}
#                 {scripts}
#                 {renderer}
#                 <div id="custom-footer">My custom footer</div>
#             </body>
#         </html>
#         '''.format(
#             app_entry=kwargs['app_entry'],
#             config=kwargs['config'],
#             scripts=kwargs['scripts'],
#             renderer=kwargs['renderer'])

# app = CustomDash()
# #%%
# app.interpolate_index.scripts

# external_stylesheets = ['https://fonts.googleapis.com/css?family=Open+Sans:300']
external_scripts = [
    {"src" : "https://unpkg.com/dash-html-components@0.13.4/dash_html_components/dash_html_components.min.js"},
    {"src" : "https://unpkg.com/dash-core-components@0.42.1/dash_core_components/dash_core_components.min.js"},
    {"src" : "https://cdn.plot.ly/plotly-1.43.1.min.js?v=0.42.1&m=1547571975"},
    {"src" : "https://unpkg.com/dash-renderer@0.20.0/dash_renderer/react-dom@15.4.2.min.js"},
    {"src" : "https://unpkg.com/dash-renderer@0.20.0/dash_renderer/react@15.4.2.min.js"}
]
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                external_scripts=external_scripts)

server = app.server
server.config.from_object('config')
logger.init_logger(server)

config = server.config['SECRETS']
logger = server.logger

app.config.update(config.get('dash_config'))

app.config.suppress_callback_exceptions = True
app.scripts.config.serve_locally = False
app.css.config.serve_locally = True

#%%
# dash.Dash.

# #%%
# app.scripts.get_all_scripts()

# #%%
# app.scripts.append_script()
