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
MAX_TIME = 3  # 1 hr
UPDATE_TIME = 1  # update every 20 seconds
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
Y.extend([tmp75.read_temp()] * len(X))

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

setpoint = DEFAULT_TEMP


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph_scatter(n):
    global setpoint
    temp = tmp75.read_temp()

    if temp < setpoint:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
    else:
        GPIO.output(RELAY_PIN, GPIO.LOW)

    print(f'Curr temp: {temp}°C | Setpoint: {setpoint}°C | Status: {"ON" if GPIO.input(RELAY_PIN) else "OFF"}')

    Y.append(temp)

    data = plotly.graph_objs.Scatter(
        x=list(X),
        y=list(Y),
        name='temperature',
        mode='lines+markers',
        marker=dict(opacity=0)
    )

    xaxis_dict = dict(
        title='Time (hours:minutes)',
        tickvals=X_TICK_VALS,
        tickmode='array',
        ticktext=X_TICK_TEXT,
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
@app.callback(Output('temp-slider', 'value'),
              [Input('temp-slider', 'value')])
def update_slider(value):
    global setpoint
    setpoint = value
    return value


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
