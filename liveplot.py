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
MAX_TIME = 1  # 1 hr
UPDATE_TIME = 5  # update every 5 seconds
MAX_ELEMENTS = int(MAX_TIME * 3600 / UPDATE_TIME)
MAX_TICKS = 10
RELAY_PIN = 35
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT)
DEFAULT_TEMP = 20.5

X = deque(maxlen=MAX_ELEMENTS)
X.append(0)

Y = deque(maxlen=MAX_ELEMENTS)
Y.append(tmp75.read_temp())

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
        html.Div(id='slider-output-container')
    ]
)


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals'), Input('temp-slider', 'value')]
)
def update_graph_scatter(n, setpoint):
    # make the x-axis have a tick every UPDATE_TIME seconds
    X.append(X[-1] + UPDATE_TIME)

    temp = tmp75.read_temp()
    if temp < setpoint:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
    else:
        GPIO.output(RELAY_PIN, GPIO.LOW)

    Y.append(temp)

    data = plotly.graph_objs.Scatter(
        x=list(X),
        y=list(Y),
        name='temperature',
        mode='lines+markers',
        marker=dict(opacity=0)
    )

    step = max(1, len(X) // MAX_TICKS)
    xticks = list((np.array(X) // 60)[::-1])[::step]
    tickvals = list(X)[::-1][::step][::-1]
    ticktext = [str(i) for i in xticks]
    ticktext[-1] = 'now'

    xaxis_dict = dict(
        title='Time (minutes)',
        tickvals=tickvals,
        tickmode='array',
        ticktext=ticktext,
        range=[X[0], X[-1]]
    )

    return {'data': [data],
            'layout': go.Layout(
                xaxis=xaxis_dict,
                yaxis=dict(range=[min(Y) - .5, max(Y) + .5], title='Temperature (°C)\n'),
                title=f'Set: {setpoint}°C - Current: {temp:.2f}°C'
                      f' - STATUS: {"ON" if temp < setpoint else "OFF"}'
            )}


# print slider value
# @app.callback(Output('slider-output-container', 'children'),
#               [Input('temp-slider', 'value')])
# def update_slider(value):
#     sp.temp = value
#     return 'Setpoint: {}°C'.format(value)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=False)
