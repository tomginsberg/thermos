from collections import deque

import RPi.GPIO as GPIO
import numpy as np
import plotly
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Output, Input

from tmp75 import TMP75

app = Dash(__name__)

tmp75 = TMP75()
MAX_TIME = 3  # n hr
UPDATE_TIME = 3  # update every n seconds
TICK_INTERVAL = 20  # in minutes
RELAY_PIN = 35
DEFAULT_TEMP = 20.5

GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT)

X = list(np.arange(0, int(MAX_TIME * 3600) + 1, UPDATE_TIME))
X_TICK_VALS = X[::-1][::int(TICK_INTERVAL * 60 / UPDATE_TIME)][::-1]
# convert to string in hr:min format
X_TICK_TEXT = [f"{i // 60}:{i % 60:02}" for i in [(MAX_TIME * 60 - i // 60) for i in X_TICK_VALS]]
X_TICK_TEXT[-1] = "now"

Y = deque(maxlen=len(X))
curr_temp = tmp75.read_temp()
Y.extend([curr_temp for _ in X])

setpoint = DEFAULT_TEMP

SETPOINT_HISTORY = deque(maxlen=len(X))
SETPOINT_HISTORY.extend([DEFAULT_TEMP for _ in X])

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
            min=18,
            max=25,
            step=0.5,
            value=DEFAULT_TEMP,
            marks={i: '{}°C'.format(i) for i in range(18, 26)},
            persistence=True
        ),
    ]
)


def find_change_points(bin_array):
    """Find the indices where the array changes from 0 to 1 or 1 to 0"""
    return np.where(np.diff(bin_array) != 0)[0] + 1


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph_scatter(n):
    global setpoint, X, Y, SETPOINT_HISTORY
    temp = tmp75.read_temp()

    if temp < setpoint:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
    else:
        GPIO.output(RELAY_PIN, GPIO.LOW)

    print(f'Curr temp: {temp}°C | Setpoint: {setpoint}°C | Status: {"ON" if temp < setpoint else "OFF"}')

    Y.append(temp)
    SETPOINT_HISTORY.append(setpoint)

    # data = []
    # change_points = [0] + find_change_points(RELAY_HISTORY) + [len(RELAY_HISTORY)]
    # for idx, change_point in enumerate(change_points[:-1]):
    #     next_change_point = change_points[idx + 1]
    #     data.append(
    #         plotly.graph_objs.Scatter(
    #             x=X[change_point:next_change_point],
    #             y=Y[change_point:next_change_point],
    #             mode='lines',
    #             line=dict(color='red' if RELAY_HISTORY[next_change_point - 1] == 1 else 'blue'),
    #             showlegend=False
    #         )
    #     )
    data = plotly.graph_objs.Scatter(
        x=X,
        y=list(Y),
        name='Temperature',
        mode='lines',
        # set color of the line based on RELAY_HISTORY
        line=dict(color='blue')
    )

    setpoint_data = plotly.graph_objs.Scatter(
        x=X,
        y=list(SETPOINT_HISTORY),
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

    layout = go.Layout(xaxis=xaxis_dict,
                       yaxis=dict(
                           range=[min(min(Y), min(SETPOINT_HISTORY)) - 1, max(max(Y), max(SETPOINT_HISTORY)) + 1],
                           title='Temperature (°C)\n'),
                       title=f'Set: {setpoint}°C - Current: {temp:.2f}°C'
                             f' - STATUS: {"ON" if temp < setpoint else "OFF"}',
                       legend=dict(
                           yanchor="top",
                           y=0.99,
                           xanchor="left",
                           x=0.01
                       )
                       )

    return {'data': [data, setpoint_data], 'layout': layout}


@app.callback(Output('temp-slider', 'value'),
              [Input('temp-slider', 'value')])
def update_slider(value):
    global setpoint
    setpoint = value
    return value


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
