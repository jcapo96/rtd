import dash
import os
import sys

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from dash import Input, Output, State, callback_context
import dash_extendable_graph as deg
from dash.exceptions import PreventUpdate
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], prevent_initial_callbacks=True)
app.config["suppress_callback_exceptions"] = True

empty_data = {'Height (m)': [], 'Temperature (K)': []}
df_empty = pd.DataFrame(empty_data)
current_time = "... Initializing ..."

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
                        html.A(className='nav-link', href='/', children='Home')
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
    dcc.Interval(id='interval', interval=1000 * 10, n_intervals=0),
    dcc.Interval(id='interval-quick', interval=1000 * 5, n_intervals=0),
    dcc.Interval(id="interval-graph-update", interval = 1000*2, n_intervals=0),
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
                xaxis={'title': 'X Axis Label'},
                yaxis={'title': 'Y Axis Label'}
            )
        }

        return html.Div([
            html.H1('Pump Sensors', style={'text-align': 'center', 'color': 'black', 'font-size': '36px'}),
            dcc.Graph(id='pump-extendable', figure=extended_figure),
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
    else:
        # Return a default page or handle other paths
        return html.Div([
            html.H1('404 - Page Not Found'),
            html.P(f'The page "{pathname}" was not found.')
        ])

@app.callback(
    Output('tgrad', 'figure'),
    [Input('interval', 'n_intervals')]
)
def update_data(n_intervals):
    system = "tgrad"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    path = "/eos/user/j/jcapotor/PDHDdata/"
    ref = "40525"
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    integrationTime = 60  # seconds

    try:
        with open(f"{pathToCalib}/LARTGRAD_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/LARTGRAD_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]

        with open(f"{pathToCalib}/CERNRCalib.json") as f:
            crcaldata = json.load(f)
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
    path = "/eos/user/j/jcapotor/PDHDdata/"
    ref = "40525"

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

    sensors = mapping.head(72)["SC-ID"].values

    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    integrationTime = 60  # seconds

    try:
        with open(f"{pathToCalib}/LARTGRAD_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/LARTGRAD_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]

        with open(f"{pathToCalib}/CERNRCalib.json") as f:
            crcaldata = json.load(f)
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

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
    y = {"TGRAD":[], "HAWAI":[]}
    temp = {"TGRAD":[], "HAWAI":[]}
    etemp = {"TGRAD":[], "HAWAI":[]}
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
    path = "/eos/user/j/jcapotor/PDHDdata/"
    ref = "40525"
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    integrationTime = 60  # seconds

    try:
        with open(f"{pathToCalib}/LARTGRAD_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/LARTGRAD_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]

        with open(f"{pathToCalib}/CERNRCalib.json") as f:
            crcaldata = json.load(f)
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
    ref = "40525"
    FROM_CERN = True

    integrationTime = 60  # seconds
    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)
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
        split = mapping.loc[(mapping["SC-ID"]==name)]["NAME"].values[0].split("APA")
        apa = f"{split[0]}{split[1][0]}"
        id = int(split[1][0]) - 1
        name = split[1][1:]
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        y[id].append(name)
        temp[id].append(df["temp"].mean())
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
    ref = "40525"
    FROM_CERN = True


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
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() > 88.5:
            continue
        y.append(dict["Y"])
        temp.append(df["temp"].mean())
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
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    try:
        with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "pp"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    ref = "40525"
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    try:
        with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
        y.append(dict["X"])
        temp.append(df["temp"].mean() - cal - rcal)
        etemp.append(df["temp"].std())
    figure = px.scatter(x=y, y=temp, error_y=etemp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
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

def update_data(n_intervals, existing_figure):
    system = "pp"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    ref = "40525"
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    try:
        with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])
        temp[id] = []
        time[id] = []
        etemp[id] = []
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])
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
        time[id].append(df["epochTime"].mean())
        etemp[id].append(df["temp"].std())

    for id in temp.keys():
        scatter_trace = go.Scatter(
            x=time[id],
            y=temp[id],
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
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    try:
        with open(f"{pathToCalib}/PIPE_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/PIPE_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

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
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

        if caldata is not None:
            if id not in caldata.keys():
                cal = 0
            elif id in caldata.keys():
                cal = caldata[id][0]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            if id not in rcaldata.keys():
                rcal = 0
            elif id in rcaldata.keys():
                rcal = rcaldata[id][0]*1e-3
        elif rcaldata is None:
            rcal = 0

        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if df["temp"].mean() - cal - rcal < 86:
            continue
        if df["temp"].mean() - cal - rcal > 88:
            continue
        y.append(dict["Z"])
        temp.append(df["temp"].mean() - cal - rcal)
        etemp.append(df["temp"].std())
    figure = px.scatter(x=y, y=temp, error_y=etemp, title=f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    figure.update_layout(
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
    [Input('interval-quick', 'n_intervals')]
)
def update_data(n_intervals):
    system = "GA-2"
    allBool = False
    today = datetime.now().strftime('%y-%m-%d')
    ref = "40525"
    FROM_CERN = True

    pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

    try:
        with open(f"{pathToCalib}/GA-PM-PP_TREE.json") as f:
            caldata = json.load(f)[ref]

        with open(f"{pathToCalib}/GA-PM-PP_TREE_rcal.json") as f:
            rcaldata = json.load(f)[ref]
    except:
        print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
        print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
        print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
        print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
        print("\n")
        caldata, rcaldata, crcaldata = None, None, None

    mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                        sep=";", decimal=",", header=0)

    integrationTime = 60*2  # seconds

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
    cnt = 0
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

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
        y.append(cnt)
        cnt += 1
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
if __name__ == '__main__':
    app.run_server(debug=True)
