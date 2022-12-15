from collections import deque

import RPi.GPIO as GPIO
import numpy as np
import plotly
import plotly.graph_objs as go
from dash import Dash, dcc, html, dash
from dash.dependencies import Output, Input
import json
from flask import jsonify
from dash.exceptions import PreventUpdate

app = Dash(__name__)

MAX_TIME = 60  # n mins
UPDATE_TIME = 2  # update every n seconds
TICK_INTERVAL = 15  # in minutes

SETPOINT = 20.5
SLIDER_MIN = 16
SLIDER_MAX = 22
SLIDER_STEP = 0.5
SLIDER_TICK_STEP = 1

RELAY_PIN = 35

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT)

X = list(np.arange(0, int(MAX_TIME * 60) + 1, UPDATE_TIME))
X_TICK_VALS = X[::-1][::int(TICK_INTERVAL * 60 / UPDATE_TIME)][::-1]
# convert to string in hr:min format
X_TICK_TEXT = [f"{i // 60}:{i % 60:02}" for i in [(MAX_TIME - i // 60) for i in X_TICK_VALS]]
X_TICK_TEXT[-1] = "now"

app.layout = html.Div(
    [
        dcc.Graph(id='live-graph',
                  animate=False),
        dcc.Interval(
            id='graph-update',
            interval=UPDATE_TIME * 1000,
            n_intervals=0
        ),
        dcc.Slider(
            id='temp-slider',
            min=SLIDER_MIN,
            max=SLIDER_MAX,
            step=SLIDER_STEP,
            value=SETPOINT,
            marks={i: '{}°C'.format(i) for i in range(SLIDER_MIN, SLIDER_MAX + 1, SLIDER_TICK_STEP)},
            persistence=True
        ),
        # hidden div to store data
        html.Div(id='slider-output-container', style={'display': 'none'}),
    ]
)


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph_scatter(_):
    try:
        data = json.load(open('data.json', 'r'))
    except json.decoder.JSONDecodeError:
        raise PreventUpdate()

    setpoint_data = data['setpoint']
    temp_data = data['temp']
    assert len(setpoint_data) == len(temp_data) == len(
        X), f"Data length mismatch: {len(temp_data)}, {len(setpoint_data)}, {len(X)}"

    temp = temp_data[-1]
    setpoint = setpoint_data[-1]
    y_min, y_max = min(min(temp_data), min(setpoint_data)) - 1, max(max(temp_data), max(setpoint_data)) + 1

    data = plotly.graph_objs.Scatter(
        x=X,
        y=temp_data,
        name='Temperature',
        mode='lines',
        # set color of the line based on RELAY_HISTORY
        line=dict(color='blue')
    )

    setpoint_data = plotly.graph_objs.Scatter(
        x=X,
        y=setpoint_data,
        name='Setpoint',
        mode='lines',
        line=dict(color='green'),
        showlegend=True
    )

    xaxis_dict = dict(
        title='Time (hours:minutes)',
        tickvals=X_TICK_VALS,
        tickmode='array',
        ticktext=X_TICK_TEXT,
        range=[X[0], X[-1]]
    )
    is_on = GPIO.input(RELAY_PIN) == GPIO.HIGH
    layout = go.Layout(xaxis=xaxis_dict,
                       yaxis=dict(
                           range=[y_min, y_max],
                           title='Temperature (°C)\n'),
                       title=f'Set: {setpoint}°C - Current: {temp:.2f}°C'
                             f' - STATUS: {"ON" if is_on else "OFF"}',
                       legend=dict(
                           yanchor="top",
                           y=0.99,
                           xanchor="left",
                           x=0.01
                       )
                       )

    return {'data': [data, setpoint_data], 'layout': layout}


@app.callback(Output('slider-output-container', 'children'),
              [Input('temp-slider', 'value')])
def update_slider(value):
    global SETPOINT
    SETPOINT = value
    return value


@app.callback(Output('temp-slider', 'value'),
              [Input('graph-update', 'n_intervals')])
def update_slider(_):
    return SETPOINT


@app.server.route('/setpoint')
def setpoint():
    return jsonify(SETPOINT)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
