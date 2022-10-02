"""
Biomod Raman Spectra Analysis GUI
Dahlia Dry, 2022 | dahlia23@mit.edu
Physical Optics and Electronics Group
"""
#package imports
from dash import dcc,html,dash_table
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
fileparams = ['Name','Nspec','Time(s)','Label','Concentration']
working = go.Figure()
current=go.Figure()
colorlist = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
datalog = ""
buffer='      \n'
tab= html.Div(children=[
            html.Div(dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
                multiple=True
            )),
            html.Div(
                children= [
                dcc.Store(id='diff-store'),
                dash_table.DataTable(
                    id='file-list',
                    columns=([{'id':p,'name':p} for p in fileparams]),
                    data=[{'Name':'',
                        'Nspec':0,
                        'Time(s)':0,
                        'Label':'',
                        'Concentration':''}],
                    style_data_conditional=[],
                    row_selectable='multi',
                    row_deletable=True,
                    editable=True
                )]
            ),
            html.Div(id='spectra',style={'display': 'none'}),
            html.Div(id='graphnum',children='0',style={'display':'none'}),
            dbc.Row([
                dbc.Col(html.Div([
                    dcc.Graph(
                        id='working',
                        figure=working,
                    ),
                    dcc.Markdown(id='dialogue',children=''),
                    html.Div([dbc.Button("Do Lieber Fit",id='lieber',n_clicks=0,color='success'),
                              dbc.Tooltip("Method for background removal",target='lieber',placement='bottom'),
                              dbc.Button("Do Batch Subtraction",id='subtract',n_clicks=0,color='success'),
                              dbc.Tooltip("Toggle to spectrum you wish to subtract, then press this button",target='subtract',placement='bottom'),
                              dbc.Button("Do Max Peak Normalizaton",id='norm',n_clicks=0,color='success'),
                              dbc.Tooltip("Click max peak on bottom right plot, then press this button",target='norm',placement='bottom'),],
                              className ="d-grid gap-2 d-md-flex",
                              style={'padding':10}),
                    html.Div([dbc.Button("Show Limit of Detection",id='lod',n_clicks=0,color='info'),
                              dbc.Tooltip("Toggle LOD:Fill in concentrations in table, select analyte peak in top left plot, then press this button ",target='lod',placement='bottom'),
                              dbc.Button("Show All Spectra",id='all-spec',n_clicks=0,color='info'),
                              dbc.Tooltip("Toggle show all spectra",target='all-spec',placement='bottom'),],
                              className ="d-grid gap-2 d-md-flex",
                              style={'padding':10}),
                ],
                ),),
                dbc.Col(html.Div([
                    dcc.Markdown(children='## Log'),
                    dcc.Markdown(id='log',children='',style={"maxHeight": "400px", "overflow": "scroll"}),
                    html.Div([
                                dbc.Button("<-",id="back",n_clicks=0,color='primary'),
                                dbc.Button("->",id="forward",n_clicks=0,color='primary'),
                                dbc.Button("undo",id="undo",n_clicks=0,color='primary')], #undo/toggle back-forth buttons
                                className ="d-grid gap-2 d-md-flex",
                                style={'padding':10}),
                    dcc.Graph(
                        id='current',
                        figure=current,
                    ),
                    ]
                    ),)
                ],)],style={'height':'50vh'},)