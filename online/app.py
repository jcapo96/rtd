import dash
import os
import sys

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc, dash_table
from src.data.make_data import MakeData
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

FROM_CERN = True

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], prevent_initial_callbacks=True)
load_figure_template("bootstrap")
app.config["suppress_callback_exceptions"] = True

empty_data = {'Height (m)': [], 'Temperature (K)': []}
df_empty = pd.DataFrame(empty_data)
current_time = "... Initializing ..."

pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"
mapping = pd.read_csv(f"{current_directory}/src/data/mapping/baseline_pdhd_mapping.csv",
                        sep=",", decimal=".", header=0)
ref = "40533"
treePath = 0

calibFileNameTGrad = "LARTGRAD_TREE"

calibFileName = "POFF_2024-04-30T19:00:00_2024-04-30T20:00:00" #here use the name of the pumps-off calibration you want to use

with open(f"{pathToCalib}/{calibFileName}.json") as f:
    calpoff = json.load(f)[ref]

app.layout = html.Div([
    html.Nav(className='navbar navbar-expand-lg navbar-light bg-light', children=[
        html.Div(className='container', children=[
            html.A(className='navbar-brand', href='#', children=[
                html.Img(src=app.get_asset_url('logo.png'), height="30"),
                '\t \t Temperature Monitoring System - Slow Control'
            ]),
            html.Button(className='navbar-toggler', type='button', **{'data-toggle': 'collapse', 'data-target': '#navbarSupportedContent',
                               'aria-controls': 'navbarSupportedContent', 'aria-expanded': 'false', 'aria-label': 'Toggle navigation'}, children=[
                html.Span(className='navbar-toggler-icon')
            ]),
            html.Div(className='collapse navbar-collapse', id='navbarSupportedContent', children=[
                html.Ul(className='navbar-nav ms-auto', children=[
                    html.Li(className='nav-item', style={"margin-right": "40px"}, children=[
                        html.A(className='nav-link', href='/', children='Home'),
                    ]),
                    html.Li(className='nav-item', style={"margin-right": "40px"}, children=[
                        html.A(className='nav-link', href='/3d', children='3D'),
                    ]),
                    html.Li(className='nav-item', style={"margin-right": "40px"}, children=[
                        html.A(className='nav-link', href='/poff', children='Pumps-Off'),
                    ]),
                    html.Li(className='nav-item dropdown pages-menu', children=[
                        dbc.DropdownMenu(
                            label="Systems",
                            className="dropdown-menu-pages",
                            children=[
                                dbc.DropdownMenuItem("Table", href="/table"),
                                dbc.DropdownMenuItem("Valencia TGradient", href="/tgrad"),
                                dbc.DropdownMenuItem("APA", href="/apa"),
                                dbc.DropdownMenuItem("HAWAII", href="/hawaii"),
                                dbc.DropdownMenuItem("PrM", href="/prm"),
                                dbc.DropdownMenuItem("Pump", href="/pump"),
                                dbc.DropdownMenuItem("Pipe", href="/pipe"),
                                dbc.DropdownMenuItem("Gas Arrays", href="/ga"),
                            ]
                        )
                    ])
                ])
            ])
        ])
    ]),
    dcc.Location(id='url', refresh=False),
    html.Div(id="page-content"),
    dcc.Interval(id='interval', interval=1000 * 20, n_intervals=0),
    dcc.Interval(id='interval-medium', interval=1000 * 8, n_intervals=0),
    dcc.Interval(id='interval-quick', interval=1000 * 5, n_intervals=0),
    dcc.Interval(id="interval-graph-update", interval = 1000*3, n_intervals=0),
    dcc.Interval(id="interval-graph-update-stab", interval = 1000*10, n_intervals=0),

    # Bottom bar
    html.Footer([
        html.Div([
            html.Div('Developer: Jordi Capó', style={'flex': '1'}),
            html.Div('Institution: IFIC (Valencia, Spain)', style={'flex': '1'}),
            html.Div(html.A('jcapo@ific.uv.es', href='mailto:jcapo@ific.uv.es'), style={'flex': '1'})
        ], style={'display': 'flex', 'justify-content': 'space-between', 'padding': '10px', 'background-color': '#f0f0f0'})
    ])
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        # Return the layout for the home page
        return html.Div(style={'background-color': '#f2f2f2'}, children=[
                html.Div(style={'margin-top': '20px', "background-color":'#f3f3f3'}),  # Add separation between H1 and top navbar
                html.H1('Temperature Status: Overview', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),

                html.Div([
                    html.H1('Stabilization Plot', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),
                    dcc.Graph(
                        id='diff',
                        config={'displayModeBar': False},
                        figure={
                            'layout': {
                                'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                                'title': '... Loading temperature graph ...'
                            }
                        }
                    ),
                ], style={'width': '96%', 'display': 'inline-block', 'padding': '20px', 'vertical-align': 'top'}),

                # Left div with the first graph
                html.Div([
                    html.Div([
                        html.H1('T-Profiles', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),
                        dcc.Graph(
                            id='home',
                            config={'displayModeBar': False},
                            figure={
                                'layout': {
                                    'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                                    'title': '... Loading temperature graph ...'
                                }
                            }
                        ),
                    ], style={'border': '1px solid #000', 'padding': '10px'}),  # Box enclosing the graph
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'vertical-align': 'top'}),

                # Right div with the second graph
                html.Div([
                    html.Div([
                        html.H1('APA temperatures', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),
                        dcc.Graph(
                            id='apa',
                            config={'displayModeBar': False},
                            figure={
                                'layout': {
                                    'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                                    'title': '... Loading temperature graph ...'
                                }
                            }
                        ),
                    ], style={'border': '1px solid #000', 'padding': '10px'}),  # Box enclosing the graph
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'vertical-align': 'top'}),

                html.Div([
                    html.Div([
                        html.H1('Gas Arrays', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),
                        dcc.Graph(
                            id='ga',
                            config={'displayModeBar': False},
                            figure={
                                'layout': {
                                    'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                                    'title': '... Loading temperature graph ...'
                                }
                            }
                        ),
                    ], style={'border': '1px solid #000', 'padding': '10px'}),  # Box enclosing the graph
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'vertical-align': 'top'}),

                html.Div([
                    html.Div([
                        html.H1('Pipe Temperatures', style={'text-align': 'center', 'color': 'black', 'font-size': '24px'}),
                        dcc.Graph(
                            id='pipe',
                            config={'displayModeBar': False},
                            figure={
                                'layout': {
                                    'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                                    'title': '... Loading temperature graph ...'
                                }
                            }
                        ),
                    ], style={'border': '1px solid #000', 'padding': '10px'}),  # Box enclosing the graph
                ], style={'width': '48%', 'display': 'inline-block', 'padding': '20px', 'vertical-align': 'top'}),
            ])



    elif pathname == '/table':
        # Return the layout for the home page
        return html.Div([
            html.H1('Temperatures', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            html.P(f'Current time: {current_time}', id="time"),
            dash_table.DataTable(
                id='table',
                columns=[{'name': i, 'id': i} for i in df_empty.columns],
                data=[],
                style_table={'overflowX': 'auto', 'border': '1px solid black'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                style_data={'whiteSpace': 'normal', 'height': 'auto'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'column_id': 'Temperature (K)'},
                        'textAlign': 'center'
                    },
                    {
                        'if': {'column_id': 'Height (m)'},
                        'textAlign': 'center'
                    }
                ],
                style_cell_conditional=[
                    {'if': {'column_id': 'Height (m)'}, 'width': '30%', "textAlign": "center"},
                    {'if': {'column_id': 'Temperature (K)'}, 'width': '70%', "textAlign": "center"}
                ]
            ),
        ], style={'width': '60%', 'margin': 'auto'})  # Adjust the width of the containing div)
    elif pathname == '/tgrad':
        return html.Div([
            html.H1('Valencia TGradient Monitor', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='tgrad',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/apa':
        return html.Div([
            html.H1('Sensors on the APAs', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='apa',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/hawaii':
        return html.Div([
            html.H1('Hawaii TGradient Monitor', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='hawaii',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/prm':
        return html.Div([
            html.H1('Purity Monitor Sensors', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='prm',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/pump':
        extended_figure = {
            'data': [go.Scatter(x=[], y=[], mode='markers', name='Scatter Plot')],
            'layout': go.Layout(
                title='Pump Sensors',
                xaxis={'title': 'Epoch Time (s)'},
                yaxis={'title': 'Temperature (K)'}
            )
        }

        return html.Div([
            html.H1('Pump Sensors', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(id='pump-extendable', figure=extended_figure),
            dcc.Graph(
                id='pump',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),

    elif pathname == '/pipe':
        return html.Div([
            html.H1('Sensors on the Pipes & Inlets', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='pipe',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/ga':
        return html.Div([
            html.H1('Gas Arrays', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(
                id='ga',
                config={'displayModeBar': False},
                figure = {
                    'layout': {
                        'annotations': [{'text': 'Loading...', 'x': 0.5, 'y': 0.5, 'showarrow': False}],
                        'title': '... Loading temperature graph ...'
                    }
                }
            ),
        ]),
    elif pathname == '/3d':
        return html.Div([
            html.H4('Temperature Map in the cryostat', style={'text-align': 'center'}),
            html.Button('Update', id='button', style={'display': 'block', 'margin': 'auto'}),
            dcc.Graph(id="3dgraph",
                    figure={
                        'layout': {
                            'title': 'Click Update button'
                        }
                    }),
            html.P("Height:"),
            dcc.RangeSlider(
                id='range-slider',
                min=0, max=8, step=0.1,
                marks={0: '0', 2.5: '2.5'},
                value=[0.0, 8.0]
            ),
        ])
    elif pathname == '/poff':
        extended_figure = {
            'data': [go.Scatter(x=[], y=[], mode='markers', name='Scatter Plot')],
            'layout': go.Layout(
                title='Stabilization evolution',
                xaxis={'title': 'Epoch Time (s)'},
                yaxis={'title': 'STD of stabilization plot (K)'}
            )
        }
        return html.Div([
            html.H4('Stabilization Plot', style={'text-align': 'center'}),
            dcc.Graph(id="diff",
                    figure={'layout': {'title': 'Loading stabilization plot...'}}),
            dcc.Graph(id="stab-extendable", figure=extended_figure),
        ])
    else:
        # Return a default page or handle other paths
        return html.Div([
            html.H1('404 - Page Not Found'),
            html.P(f'The page "{pathname}" was not found.')
        ])

@app.callback(
    Output('3dgraph', 'figure'),
    [Input('button', 'n_clicks'),
     Input("range-slider", "value")]
)
def update_data(n_clicks, slider_range):
    if n_clicks:
        system = "tgrad"
        allBool = False
        today = datetime.now().strftime('%y-%m-%d')
        path = "/eos/user/j/jcapotor/PDHDdata/"

        integrationTime = 60  # seconds

        try:
            with open(f"{pathToCalib}/{calibFileName}.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/{calibFileName}_rcal.json") as f:
                rcaldata = json.load(f)[ref]

            with open(f"{pathToCalib}/CERNRCalib.json") as f:
                crcaldata = json.load(f)
        except:
            caldata, rcaldata, crcaldata = calpoff, None, None

        sensors = mapping.head(100)["SC-ID"].values

        today = datetime.now()
        startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
        endTimeStamp = today.timestamp()
        if FROM_CERN is True:
            m = MakeData(detector="np04", all=allBool, sensors = sensors,
                            startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                            startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                            clockTick=60,
                            ref=ref, FROM_CERN=FROM_CERN)
        elif FROM_CERN is False:
            m = MakeData(detector="np04", all=allBool, sensors = sensors,
                            startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                            clockTick=60,
                            ref=ref, FROM_CERN=FROM_CERN)
        m.getData()
        x, y, z, temp, etemp = [], [], [], [], []
        for name, dict in m.container.items():
            id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
            if caldata is not None:
                if id not in caldata.keys():
                    cal = 0
                elif id in caldata.keys():
                    cal = caldata [id][treePath]*1e-3
            elif caldata is None:
                cal = 0
            if rcaldata is not None:
                if id not in rcaldata.keys():
                    rcal = 0
                elif id in rcaldata.keys():
                    rcal = rcaldata [id][treePath]*1e-3
            elif rcaldata is None:
                rcal = 0
            if crcaldata is not None:
                if f"s{int(name.split('TE')[1])}" not in crcaldata.keys():
                    crcal = 0
                elif f"s{int(name.split('TE')[1])}" in crcaldata.keys():
                    crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
            elif crcaldata is None:
                crcal = 0
            df = dict["access"].data
            df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
            if (df["temp"].mean() - cal - rcal - crcal) < 0:
                continue
            x.append(dict["X"])
            y.append(dict["Y"])
            z.append(dict["Z"])
            temp.append(df["temp"].mean() - cal - rcal - crcal)
            etemp.append(df["temp"].std())

        data = pd.DataFrame({"x":x, "y":y, "z":z, "temp":temp})
        low, high = slider_range
        mask = (data.y > low) & (data.y  < high)
        figure = px.scatter_3d(data[mask],
            x='x', y='z', z='y',
            color="temp", hover_data=['temp'])
        figure.update_layout(
            xaxis_title="Height (m)",
            yaxis_title="Temperature (K)",
            title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}",
            font = {
                "family": "Arial, sans-serif",
                "size": 14,
                "color": "black"
            },
            title_font = {
                "family": "Arial, sans-serif",
                "size": 20,
                "color": "black"
            },
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_x=0.5,
        )
        return figure

@app.callback(
    Output('diff', 'figure'),  # Corrected output specification
    [Input('interval', 'n_intervals')]
)
def update_data(n_intervals):
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')


    sensors = mapping.head(96)["SC-ID"].values

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        df = dict["access"].data
        dataFrame = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if (dataFrame["temp"].mean()) > 88:
            continue
        if (dataFrame["temp"].mean()) < 0:
            continue
        dataFrame2 = df.loc[(df["epochTime"]>(today - timedelta(seconds=60*15)).timestamp())&(df["epochTime"]<endTimeStamp)]
        if abs(dataFrame["temp"].mean() - dataFrame2["temp"].mean()) > 0.02:
            continue
        y.append(name)
        temp.append(dataFrame["temp"].mean() - dataFrame2["temp"].mean())
        # etemp.append(np.sqrt(dataFrame["temp"].std()**2 + dataFrame2["temp"].std()**2))
        etemp.append(np.sqrt(dataFrame["temp"].std()**2 + dataFrame2["temp"].std()))
    figure = px.scatter(x=y, y=temp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    figure.update_yaxes(range=[-0.005, 0.005])
    return figure

@app.callback(Output('stab-extendable', 'figure'),
              [Input('interval-graph-update-stab', 'n_intervals')],
              [State('stab-extendable', 'figure')])

def update_data_real_time(n_intervals, existing_figure):
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')


    sensors = mapping.head(96)["SC-ID"].values

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()

    temp_means = []

    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        df = dict["access"].data
        dataFrame2 = df.loc[(df["epochTime"]>(today - timedelta(seconds=60*15)).timestamp())&(df["epochTime"]<endTimeStamp)]
        df = df.loc[(df["epochTime"] > startTimeStamp) & (df["epochTime"] < endTimeStamp)]
        if df["temp"].mean() < 0:
            continue
        if df["temp"].mean() > 88:
            continue
        if abs(df["temp"].mean() - dataFrame2["temp"].mean()) > 0.02:
            continue
        temp_means.append(df["temp"].mean() - dataFrame2["temp"].mean())
    temp_means = [temp for temp in temp_means if not np.isnan(temp)]
    mean_temp_all_sensors = n_intervals
    std_temp_all_sensors = np.std(temp_means)
    scatter_trace = go.Scatter(
        x=[mean_temp_all_sensors],
        y=[std_temp_all_sensors],
        mode='markers',
        marker={"size": 10},
        name="Standard Deviation"
    )

    if existing_figure is not None and 'data' in existing_figure:
        existing_traces = existing_figure['data']
        if existing_traces:
            existing_trace = existing_traces[0]
            existing_trace['x'] += [mean_temp_all_sensors]
            existing_trace['y'] += [std_temp_all_sensors]
            scatter_trace = existing_trace

    extended_data = [scatter_trace]

    extended_figure = {
        'data': extended_data,
        'layout': existing_figure['layout'] if existing_figure else {}
    }

    return extended_figure

@app.callback(
    Output('tgrad', 'figure'),
    [Input('interval-medium', 'n_intervals')]
)
def update_data(n_intervals):
    system = "tgrad"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    integrationTime = 60  # seconds

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/{calibFileNameTGrad}.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/{calibFileNameTGrad}_rcal.json") as f:
                rcaldata = json.load(f)[ref]

            with open(f"{pathToCalib}/CERNRCalib.json") as f:
                crcaldata = json.load(f)
        elif calpoff is not None:
            caldta, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][treePath]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][treePath]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        elif crcaldata is None:
            crcal = 0
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if (df["temp"].mean() - cal - rcal - crcal) > 88:
            continue
        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal - rcal - crcal)
        etemp.append(df["temp"].std())
    figure = px.scatter(x=y, y=temp, error_y=etemp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(
    Output('home', 'figure'),
    [Input('interval', 'n_intervals')]
)
def update_data(n_intervals):
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    sensorIds = [
        39666, 39665, 39664, 39667, 39661, 39660, 39655, 39654, 39653, 39652, 99999, 39651, 39650,
        40526, 40525, 40524, 39659, 39658, 39657, 39649, 39648, 39647, 39646, 39644, 39630, 39629,
        39628, 39627, 39626, 39625, 39624, 39623, 39622, 39621, 39620, 39619, 40533, 40530, 40531,
        40529, 39614, 39613, 39612, 39611, 39610, 39609, 39608, 39607, 40000, 40001, 40002, 40003,
        40004, 40005, 40006, 40007, 40008, 40009, 40010, 40011, 40012, 40013, 40014, 40015, 40016,
        40017, 40018, 40019, 40020, 40021, 40022, 40023
    ]


    integrationTime = 60  # seconds

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/{calibFileNameTGrad}.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/{calibFileNameTGrad}_rcal.json") as f:
                rcaldata = json.load(f)[ref]

            with open(f"{pathToCalib}/CERNRCalib.json") as f:
                crcaldata = json.load(f)
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, sensorIds=sensorIds,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, sensorIds=sensorIds,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y = {"TGRAD":[], "HAWAI":[]}
    temp = {"TGRAD":[], "HAWAI":[]}
    etemp = {"TGRAD":[], "HAWAI":[]}
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))

        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][treePath]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][treePath]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            try:
                crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
            except:
                crcal = 0
        elif crcaldata is None:
            crcal = 0
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        # if (df["temp"].mean() - cal - rcal - crcal) > 88:
        #     continue

        y[dict["SYSTEM"]].append(dict["Y"])
        temp[dict["SYSTEM"]].append(df["temp"].mean() - cal - rcal - crcal)
        etemp[dict["SYSTEM"]].append(df["temp"].std())

    trace1 = go.Scatter(
        x=y["TGRAD"],
        y=temp["TGRAD"],
        error_y={"type":"data", "array":etemp["TGRAD"], "visible":True},
        name="VALENCIA",
        mode="markers",
        marker={
            "color":'rgb(34,163,192)'
        }
    )
    trace2 = go.Scatter(
        x=y["HAWAI"],
        y=temp["HAWAI"],
        error_y={"type":"data", "array":etemp["HAWAI"], "visible":True},
        name="HAWAII",
        mode="markers",
        yaxis='y2'

    )

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(trace1)
    figure.add_trace(trace2,secondary_y=False)
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        title = f"{today.strftime('%Y-%m-%d %H:%M:%S')}",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(
    [Output("table", "data"),
     Output("time", "children")],
    [Input('interval', 'n_intervals')]
)
def update_data(n_intervals):
    system = "tgrad"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    integrationTime = 60  # seconds

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/{calibFileNameTGrad}.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/{calibFileNameTGrad}_rcal.json") as f:
                rcaldata = json.load(f)[ref]

            with open(f"{pathToCalib}/CERNRCalib.json") as f:
                crcaldata = json.load(f)
        elif calpoff is not None:
            caldta, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))

        if caldata is not None:
            if id not in caldata.keys():
                continue
            cal = caldata[id][2]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        elif crcaldata is None:
            crcal = 0
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal - rcal - crcal)
        etemp.append(df["temp"].std())
    table_data = [{"Height (m)": y[i], "Temperature (K)": temp[i]} for i in range(len(y))]  # Convert to list of dictionaries
    current_time = today.strftime('%Y-%m-%d %H:%M:%S')
    return table_data, current_time

@app.callback(
    Output('apa', 'figure'),
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "apa"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    integrationTime = 60  # seconds

    try:
        with open(f"{pathToCalib}/{calibFileName}.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/{calibFileName}_rcal.json") as f:
            rcaldata = json.load(f)[ref]

        with open(f"{pathToCalib}/CERNRCalib.json") as f:
            crcaldata = json.load(f)
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [[] for i in range(4)], [[] for i in range(4)], [[] for i in range(4)]
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][treePath]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][treePath]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        elif crcaldata is None:
            crcal = 0
        split = mapping.loc[(mapping["SC-ID"]==name)]["NAME"].values[0].split("APA")
        apa = f"{split[0]}{split[1][0]}"
        id = int(split[1][0]) - 1
        name = split[1][1:]
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        y[id].append(name)
        temp[id].append(df["temp"].mean() - cal)
        etemp[id].append(df["temp"].std())
    fig = make_subplots(rows=2, cols=2)

    # Add traces to subplots
    fig.add_trace(go.Scatter(x=y[0], y=temp[0], mode='markers', name=f"APA1"), row=1, col=1)
    fig.add_trace(go.Scatter(x=y[1], y=temp[1], mode='markers', name=f"APA2"), row=1, col=2)
    fig.add_trace(go.Scatter(x=y[2], y=temp[2], mode='markers', name=f"APA3"), row=2, col=1)
    fig.add_trace(go.Scatter(x=y[3], y=temp[3], mode='markers', name=f"APA4"), row=2, col=2)

    # Update layout
    fig.update_layout(
        title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}",
        title_font={
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )

    # Convert subplot to a Plotly figure
    figure = fig.to_dict()
    return figure

@app.callback(
    Output('hawaii', 'figure'),
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "hawai"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    try:
        with open(f"{pathToCalib}/{calibFileName}.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/{calibFileName}_rcal.json") as f:
            rcaldata = json.load(f)[ref]

        with open(f"{pathToCalib}/CERNRCalib.json") as f:
            crcaldata = json.load(f)
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][treePath]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][treePath]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        elif crcaldata is None:
            crcal = 0
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() > 88.5:
            continue
        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal)
        etemp.append(df["temp"].std())
    figure = px.scatter(x=y, y=temp, error_y=etemp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(
    Output('prm', 'figure'),
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "prm"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    ref = "48733"

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
                rcaldata = json.load(f)[ref]
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))

        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][2]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() < 0:
            continue
        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal - rcal)
        etemp.append(df["temp"].std())
    figure = px.scatter(x=y, y=temp, error_y=etemp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(
    Output('pump', 'figure'),
    [Input('interval', 'n_intervals')]
)
def update_data(n_intervals):
    system = "pp"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
                rcaldata = json.load(f)[ref]
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))

        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][2]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        y.append(dict["X"])
        temp.append(df["temp"].mean() - cal - rcal)
        etemp.append(df["temp"].std())
    figure = go.Figure(
        data=[
            go.Scatter(x=y, y=temp, error_y={"type":"data", "array":etemp}, mode="markers", name="Pump"),
        ]
    )
    figure.update_layout(
        title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}",
        xaxis_title="Distance from pump center (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(Output('pump-extendable', 'figure'),
              [Input('interval-graph-update', 'n_intervals')],
              [State('pump-extendable', 'figure')])

def update_data_real_time(n_intervals, existing_figure):
    system = "pp"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
                rcaldata = json.load(f)[ref]
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()

    temp, time, etemp, scatter_traces = {}, {}, {}, {}
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        temp[id] = []
        time[id] = []
        etemp[id] = []
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][2]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() < 0:
            continue
        temp[id].append(df["temp"].mean() - cal - rcal)
        time[id].append(n_intervals)
        etemp[id].append(df["temp"].std())

    for id in temp.keys():
        scatter_trace = go.Scatter(
            x=time[id],
            y=temp[id],
            error_y = {"type":"data", "array":etemp[id]},
            mode='markers',
            marker={"size": 10},
            name=id  # Set trace name to the ID
        )
        if existing_figure is not None and 'data' in existing_figure:
            existing_traces = [trace for trace in existing_figure['data'] if trace['name'] == id]
            if existing_traces:
                existing_trace = existing_traces[0]
                existing_trace['x'] += time[id]
                existing_trace['y'] += temp[id]
                existing_trace['error_y']['array'] += etemp[id]
                scatter_trace = existing_trace
        scatter_traces[id] = scatter_trace

    extended_data = list(scatter_traces.values())

    extended_figure = {
        'data': extended_data,
        'layout': existing_figure['layout'] if existing_figure else {}
    }

    return extended_figure

@app.callback(
    Output('pipe', 'figure'),
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "pipe"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    ref = "37131"

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/PIPE_TREE.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/PIPE_TREE_rcal.json") as f:
                rcaldata = json.load(f)[ref]
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, system=system,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y = {"I":[], "U":[], "M":[]}
    z = {"I":[], "U":[], "M":[]}
    temp = {"I":[], "U":[], "M":[]}
    etemp = {"I":[], "U":[], "M":[]}
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        stype = str(dict["type"].split("-")[1])
        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata [id][treePath]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata [id][treePath]*1e-3
        elif rcaldata is None:
            rcal = 0

        if id == "37136":
            cal, rcal = -17*1e-3, 0 #THIS NUMBER IS NOT REAL -> SENSOR FAILED DURING CALIBRATION

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() - cal - rcal < 0:
            continue
        y[stype].append(dict["Y"])
        z[stype].append(dict["Z"])
        temp[stype].append(df["temp"].mean() - cal - rcal)
        etemp[stype].append(df["temp"].std())
    figure = go.Figure(
        data=[
            go.Scatter(x=z["I"], y=temp["I"], error_y={"type":"data", "array":etemp["I"]}, mode="markers", name="Inlet"),
            go.Scatter(x=z["U"], y=temp["U"], error_y={"type":"data", "array":etemp["U"]}, mode="markers", name="Up-Inlet"),
            go.Scatter(x=z["M"], y=temp["M"], error_y={"type":"data", "array":etemp["M"]}, mode="markers", name="Pipe"),
        ]
    )
    figure.update_layout(
        title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}",
        xaxis_title="Distance from Jura side (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

@app.callback(
    Output('ga', 'figure'),
    [Input('interval-medium', 'n_intervals')]
)
def update_data(n_intervals):
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')

    sensors = [f"TE0{number}" for number in range(265, 302)]

    try:
        if calpoff is None:
            with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
                caldata = json.load(f)[ref]

            with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
                rcaldata = json.load(f)[ref]
        elif calpoff is not None:
            caldata, rcaldata, crcaldata = calpoff, None, None
    except:
        caldata, rcaldata, crcaldata = calpoff, None, None

    integrationTime = 60*2  # seconds

    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = today.timestamp()
    if FROM_CERN is True:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        startTime=f"{(today - timedelta(seconds=60*60*2 + 60*5)).strftime('%H:%M:%S')}", endTime=f"{today.strftime('%H:%M:%S')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    elif FROM_CERN is False:
        m = MakeData(detector="np04", all=allBool, sensors=sensors,
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                        clockTick=60,
                        ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    y = {"GA-1":[], "GA-2":[]}
    temp = {"GA-1":[], "GA-2":[]}
    etemp = {"GA-1":[], "GA-2":[]}
    for name, dict in m.container.items():
        id = str(int(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0]))
        stype = str(dict["SYSTEM"])

        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                if calpoff is None:
                    cal = caldata[id][2]*1e-3
                elif calpoff is not None:
                    cal = caldata[id][0]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() < 0:
            continue
        y[stype].append(dict["Y"])
        temp[stype].append(df["temp"].mean() - cal - rcal)
        etemp[stype].append(df["temp"].std())

    figure = go.Figure(
        data=[
            go.Scatter(x=y["GA-1"], y=temp["GA-1"], error_y={"type":"data", "array":etemp["GA-1"]}, mode="markers", name="GasArray-1"),
            go.Scatter(x=y["GA-2"], y=temp["GA-2"], error_y={"type":"data", "array":etemp["GA-2"]}, mode="markers", name="GasArray-2"),
        ]
    )
    figure.update_layout(
        xaxis_title="Height (m)",
        yaxis_title="Temperature (K)",
        font = {
            "family": "Arial, sans-serif",
            "size": 14,
            "color": "black"
        },
        title_font = {
            "family": "Arial, sans-serif",
            "size": 20,
            "color": "black"
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
    )
    return figure

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
