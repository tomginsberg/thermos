import numpy as np
import streamlit as st
import json
from plotly import graph_objects as go
from time import sleep
from datetime import time
import RPi.GPIO as GPIO
from scipy.signal import savgol_filter
import requests

BACKEND_URL = "http://localhost:1111"

MAX_TIME = 60  # n mins
UPDATE_TIME = 1  # update every n seconds
TICK_INTERVAL = 15  # in minutes

SETPOINT = 19.5
SLIDER_MIN = 15.0
SLIDER_MAX = 23.0
SLIDER_STEP = 0.5
SLIDER_TICK_STEP = 1

RELAY_PIN = 35

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT)

X = list(np.arange(0, int(MAX_TIME * 60) + 1, UPDATE_TIME))
X_TICK_VALS = X[::-1][::int(TICK_INTERVAL * 60 / UPDATE_TIME)][::-1]
X_TICK_TEXT = [f"{i // 60}:{i % 60:02}" for i in [(MAX_TIME - i // 60) for i in X_TICK_VALS]]
X_TICK_TEXT[-1] = "now"


def load_data():
    # Load your data here, potentially from a changing source
    data = json.load(open('data.json', 'r'))
    temp_data = data['temp']
    setpoint_data = data['setpoint']
    return temp_data, setpoint_data


def get_setpoint():
    # use get request to get the setpoint from the backend
    response = requests.get(f"{BACKEND_URL}/get_setpoint")
    return response.json().get('setpoint', SETPOINT)


def create_figure(temp_data, setpoint_data):
    fig = go.Figure()
    temp = temp_data[-1]
    if len(temp_data) > 20:
        temp_data = savgol_filter(temp_data, 15, 3)
    n_points = len(temp_data)
    _X = X[-n_points:]
    fig.add_trace(
        go.Scatter(x=_X, y=temp_data, name='Temperature',
                   mode='lines',
                   line=dict(color='blue'))
    )
    fig.add_trace(
        go.Scatter(x=_X, y=setpoint_data, name='Setpoint',
                   line=dict(color='green'),
                   mode='lines')
    )
    fig.update_xaxes(
        tickvals=X_TICK_VALS,
        ticktext=X_TICK_TEXT,
        title_text='Time'
    )

    is_on = GPIO.input(RELAY_PIN) == GPIO.HIGH
    status = "ON" if is_on else "OFF"

    fig.update_layout(
        title=f"Set: {get_setpoint()}°C - Current: {temp:.2f}°C - STATUS: {status}",
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    return fig


def get_history():
    req = requests.get(f"{BACKEND_URL}/get_history").json()
    return req.get('temperature', [0]), req.get('setpoint', [0])


# Initial load of the data
temp_data, setpoint_data = get_history()
fig = create_figure(temp_data, setpoint_data)
chart = st.plotly_chart(fig, use_container_width=True)

if 'setpoint' not in st.session_state:
    st.session_state.setpoint = SETPOINT

setpoint = st.slider("Setpoint", min_value=SLIDER_MIN, max_value=SLIDER_MAX, step=SLIDER_STEP,
                     value=st.session_state.setpoint)
update_button = st.button("Update Setpoint")


def update_setpoint(setpoint):
    try:
        response = requests.post(f"{BACKEND_URL}/set_setpoint", json={'setpoint': setpoint})
        if response.status_code != 200:
            st.error("Failed to set setpoint")
    except requests.RequestException as e:
        st.error(f"Failed to set setpoint: {e}")


if update_button:
    update_setpoint(setpoint)
    st.session_state.setpoint = setpoint

st.sidebar.title("Temperature Schedule Settings")

# Weekday schedule
st.sidebar.header("Weekdays")
bedtime_weekday = st.sidebar.time_input("Bedtime", time(22, 0))
wakeup_time_weekday = st.sidebar.time_input("Wake Up Time", time(7, 0))
leave_time_weekday = st.sidebar.time_input("Time Leaving for Work", time(8, 0))

temp_bedtime_weekday = st.sidebar.slider("Bedtime Temperature", SLIDER_MIN, SLIDER_MAX, step=SLIDER_STEP,
                                         key="bedtime_weekday")
temp_wakeup_weekday = st.sidebar.slider("Wake Up Temperature", SLIDER_MIN, SLIDER_MAX, step=SLIDER_STEP,
                                        key="wakeup_weekday")
temp_leave_weekday = st.sidebar.slider("Work Leaving Temperature", SLIDER_MIN, SLIDER_MAX, step=SLIDER_STEP,
                                       key="leave_weekday")

# Weekend schedule
st.sidebar.header("Weekends")
bedtime_weekend = st.sidebar.time_input("Bedtime", time(23, 0), key="weekend_1")
wakeup_time_weekend = st.sidebar.time_input("Wake Up Time", time(9, 0), key="weekend_2")
temp_bedtime_weekend = st.sidebar.slider("Bedtime Temperature", SLIDER_MIN, SLIDER_MAX, step=SLIDER_STEP,
                                         key="bedtime_weekend")
temp_wakeup_weekend = st.sidebar.slider("Wake Up Temperature", SLIDER_MIN, SLIDER_MAX, step=SLIDER_STEP,
                                        key="wakeup_weekend")

# Save schedule
if st.sidebar.button("Save Schedule"):
    # Logic to save the schedule settings
    # You can use a JSON file or any other method to save the schedule
    schedule = {
        "weekday": {
            "bedtime": str(bedtime_weekday),
            "wake_up": str(wakeup_time_weekday),
            "leave_for_work": str(leave_time_weekday),
            "temp_bedtime": temp_bedtime_weekday,
            "temp_wakeup": temp_wakeup_weekday,
            "temp_leave": temp_leave_weekday
        },
        "weekend": {
            "bedtime": str(bedtime_weekend),
            "wake_up": str(wakeup_time_weekend),
            "temp_bedtime": temp_bedtime_weekend,
            "temp_wakeup": temp_wakeup_weekend
        }
    }
    with open('schedule.json', 'w') as f:
        json.dump(schedule, f)
    st.sidebar.success("Schedule saved!")

# Load schedule
if st.sidebar.button("Load Schedule"):
    # Logic to load the schedule settings
    # Ensure to handle file not found scenarios
    try:
        with open('schedule.json', 'r') as f:
            loaded_schedule = json.load(f)
            st.sidebar.json(loaded_schedule)  # Display the loaded schedule
    except FileNotFoundError:
        st.sidebar.error("No saved schedule found.")

while True:
    # Update the data
    try:
        temp_data, setpoint_data = get_history()
    except json.decoder.JSONDecodeError:
        sleep(1)
        continue

    # Update the figure
    fig = create_figure(temp_data, setpoint_data)

    # Update the chart in the app
    chart.plotly_chart(fig, use_container_width=True)

    # Wait for 5 seconds before the next update
    sleep(UPDATE_TIME)
