import argparse

from hysteresis import HysteresisController

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
from datetime import time

app = Flask(__name__)
CORS(app)

args = argparse.ArgumentParser()
args.add_argument('--default_setpoint', type=float, default=19.5)
args.add_argument('--timespan', type=int, default=60 * 24)
args.add_argument('--update_time', type=int, default=2)
args.add_argument('--hysteresis', type=float, default=0.25)
args.add_argument('--relay_pin', type=int, default=35)
args.add_argument('--data_file', type=str, default='data.json')
args.add_argument('--config_file', type=str, default='config.json')
args.add_argument('--supress_gpio_warnings', type=bool, default=True)

args = args.parse_args()

# Global instance
controller = HysteresisController(**vars(args))


@app.route('/get_history', methods=['GET'])
def get_history():
    return jsonify({
        'temperature': controller.get_temperature_history(),
        'setpoint': controller.get_setpoint_history(),
    })


@app.route('/get_full_history', methods=['GET'])
def get_full_history():
    return jsonify({
        'temperature': controller.get_temperature_history(),
        'setpoint': controller.get_setpoint_history(),
        'time': controller.get_time_history()
    })


@app.route('/get_setpoint', methods=['GET'])
def get_setpoint():
    return jsonify({'setpoint': controller.setpoint})


@app.route('/get_heater_state', methods=['GET'])
def get_heater_state():
    return jsonify({'heater_state': controller.heater_state()})


@app.route('/set_setpoint', methods=['POST'])
def set_setpoint():
    setpoint = request.json.get('setpoint')
    controller.update_setpoint(setpoint=setpoint)
    return jsonify({'status': 'success'})


@app.route('/get_temperature', methods=['GET'])
def get_temperature():
    return jsonify({'temperature': controller.read_temp()})


@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    return jsonify(controller.schedule.to_dict())


@app.route('/get_logs', methods=['GET'])
def get_logs():
    with open('backend.log', 'r') as f:
        return jsonify(f.read())


@app.route('/set_schedule', methods=['POST'])
def set_schedule():
    """
    Spec for how the schedule will get generated and sent to the backend
    weekday_wakeup_time=time.fromisoformat(data['weekday_wakeup_time']),
    leave_for_work_time=time.fromisoformat(data['leave_for_work_time']),
    home_from_work_time=time.fromisoformat(data['home_from_work_time']),
    weekday_bedtime=time.fromisoformat(data['weekday_bedtime']),
    weekend_wakeup_time=time.fromisoformat(data['weekend_wakeup_time']),
    weekend_bedtime=time.fromisoformat(data['weekend_bedtime']),
    bedtime_temperature=data['bedtime_temperature'],
    wakeup_temperature=data['wakeup_temperature'],
    at_work_temperature=data['at_work_temperature']
    """
    schedule = request.json.get('schedule')
    controller.set_schedule(schedule)
    return jsonify({'status': 'success'})


# toggle schedule
@app.route('/toggle_schedule', methods=['POST'])
def toggle_schedule():
    state = request.json.get('state')
    controller.toggle_schedule(state)
    return jsonify({'status': 'success'})


# get schedule state
@app.route('/get_schedule_state', methods=['GET'])
def get_schedule_state():
    return jsonify({'state': controller.get_schedule_state()})


def run_controller():
    controller.control_loop()


if __name__ == '__main__':
    thread = threading.Thread(target=run_controller)
    thread.daemon = True
    thread.start()

    app.run(host='0.0.0.0', port=1111)
