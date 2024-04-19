import dash
import os
import sys

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from dash import Input, Output, State, callback_context
import plotly.express as px
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
current_time = "Current Time: "

app.layout = html.Div([
    html.Nav(className='navbar navbar-expand-lg navbar-light bg-light', children=[
        html.Div(className='container', children=[
            html.A(className='navbar-brand', href='#', children='Temperature Monitoring System - Slow Control'),
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
                            dbc.DropdownMenuItem("Valencia TGradient", href="/pages/tgrad.py"),
                        ]
                    )
                        ])
                    ])
                ])
            ])
        ]),
    dcc.Location(id='url', refresh=False),
    html.Div(id="page-content"),
    dcc.Interval(id='interval', interval=1000 * 5, n_intervals=0)
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        # Return the layout for the home page
        return html.Div([
            html.H1('Home Page'),
            html.P(f'{current_time}', id="time"),
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
                    }
                ],
                style_cell_conditional=[
                    {'if': {'column_id': 'Height (m)'}, 'width': '30%'},
                    {'if': {'column_id': 'Temperature (K)'}, 'width': '70%'}
                ]
            ),
        ], style={'width': '80%', 'margin': 'auto'})  # Adjust the width of the containing div)
    elif pathname == '/pages/tgrad.py':
        return html.Div([
            dcc.Graph(id='tgrad')
        ])
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
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
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
        if (df["temp"].mean() - cal - rcal - crcal) > 88:
            continue

        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal - rcal - crcal)
        etemp.append(df["temp"].std())
    table_data = [{"Height (m)": y[i], "Temperature (K)": temp[i]} for i in range(len(y))]  # Convert to list of dictionaries
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
                        startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
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

if __name__ == '__main__':
    app.run_server(debug=True)
