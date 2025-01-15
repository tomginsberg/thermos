import json
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, asdict
from datetime import time, datetime
from time import sleep
from typing import Union

import RPi.GPIO as GPIO

from tmp75 import TMP75
import warnings


@dataclass
class TemperatureSchedule:
    # Weekday schedule
    weekday_wakeup_time: time = time(8, 0)  # Default wakeup time at 7:00 AM
    leave_for_work_time: time = time(9, 0)  # Default leave for work at 8:00 AM
    home_from_work_time: time = time(17, 0)  # Default home from work at 6:00 PM
    weekday_bedtime: time = time(23, 0)  # Default bedtime at 10:30 PM

    # Weekend schedule
    weekend_wakeup_time: time = time(9, 0)  # Default wakeup time at 8:00 AM
    weekend_bedtime: time = time(23, 59)  # Default bedtime at 11:00 PM

    # Temperatures (in degrees Celsius)
    bedtime_temperature: float = 17.0  # Default bedtime temperature
    wakeup_temperature: float = 20.0  # Default wakeup temperature
    at_work_temperature: float = 16.0  # Default at work temperature

    def to_dict(self):
        d = asdict(self)
        for key in d:
            if isinstance(d[key], time):
                d[key] = d[key].isoformat()
        return d

    def from_dict(self, data: dict[str, Union[float, str]]):
        for k, v in data.items():
            if not hasattr(self, k):
                warnings.warn(f'Invalid key: {k}, skipping.')
                continue

            if isinstance(v, str) and 'temperature' not in k:
                setattr(self, k, time.fromisoformat(v))
            elif isinstance(v, (float, int)) and 'temperature' in k:
                setattr(self, k, v)
            elif isinstance(v, str) and 'temperature' in k:
                setattr(self, k, float(v))


class TemperatureController(ABC):
    """
    Base class for a temperature controller that reads the temperature from a TMP75 sensor and controls a relay
    connected to a heating element in an attempt to maintain a setpoint temperature.
    """

    def __init__(
            self,
            relay_pin=35,
            default_setpoint=19.5,
            update_time=2,  # in seconds
            timespan=60 * 24,  # in minutes
            log_interval=20,
            config_file='config.json',
            data_file='data.json',
            supress_gpio_warnings=True,
            schedule: TemperatureSchedule = TemperatureSchedule()

    ):
        self.tmp75 = TMP75()
        print(f'Initialized TMP75 sensor: {self.tmp75.read_temp()}°C')
        self.relay_pin = relay_pin
        GPIO.setwarnings(~supress_gpio_warnings)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        self.setpoint = default_setpoint
        self.update_time = update_time
        self.max_length = int(timespan * 60 / update_time / log_interval) + 1
        self.data_file = data_file
        self.schedule = schedule
        self.schedule_enabled = True
        self.log_interval = log_interval

        with open(config_file, 'w') as f:
            json.dump({
                'update_time': self.update_time,
                'timespan': timespan
            }, f)

        temp = self.read_temp()
        self.temp_history = deque([temp], maxlen=self.max_length)
        self.setpoint_history = deque([self.setpoint], maxlen=self.max_length)
        self.time_history = deque([datetime.now()], maxlen=self.max_length)

    def toggle_schedule(self, state=True):
        self.schedule_enabled = state

    def get_schedule_state(self):
        return self.schedule_enabled

    def set_schedule(self, schedule: dict[str, Union[float, str]]):
        self.schedule = TemperatureSchedule()
        self.schedule.from_dict(schedule)

    def read_temp(self):
        return self.tmp75.read_temp()

    def update_setpoint(self, setpoint):
        self.setpoint = setpoint

    def get_temperature_history(self):
        return list(self.temp_history)

    def get_setpoint_history(self):
        return list(self.setpoint_history)

    def get_time_history(self):
        return list(self.time_history)

    def _set_relay(self, state):
        GPIO.output(self.relay_pin, state)

    def turn_on_heater(self):
        self._set_relay(1)

    def turn_off_heater(self):
        self._set_relay(0)

    def heater_state(self):
        return GPIO.input(self.relay_pin)

    def is_heater_on(self):
        return self.heater_state() == GPIO.HIGH

    def is_heater_off(self):
        return self.heater_state() == GPIO.LOW

    def control_loop(self):
        step = 0
        last_update_day = None
        event_triggered = {
            'weekday_wakeup': False,
            'leave_for_work': False,
            'home_from_work': False,
            'weekday_bedtime': False,
            'weekend_wakeup': False,
            'weekend_bedtime': False,
        }

        while True:
            if self.schedule_enabled:
                now = datetime.now()
                current_time = now.time()
                day_of_week = now.weekday()  # Monday is 0, Sunday is 6

                # Check if it's a new day to reset event indicators
                if last_update_day != now.date():
                    for event in event_triggered:
                        event_triggered[event] = False
                    last_update_day = now.date()

                # Update setpoint based on the schedule for weekdays
                if day_of_week < 5:  # Weekday
                    if not event_triggered['weekday_wakeup'] and current_time >= self.schedule.weekday_wakeup_time:
                        print(f'Waking up, setting temperature to {self.schedule.wakeup_temperature}°C')
                        self.setpoint = self.schedule.wakeup_temperature
                        event_triggered['weekday_wakeup'] = True
                    if not event_triggered['leave_for_work'] and current_time >= self.schedule.leave_for_work_time:
                        print(f'Leaving for work, setting temperature to {self.schedule.at_work_temperature}°C')
                        self.setpoint = self.schedule.at_work_temperature
                        event_triggered['leave_for_work'] = True
                    if not event_triggered['home_from_work'] and current_time >= self.schedule.home_from_work_time:
                        print(f'Home from work, setting temperature to {self.schedule.wakeup_temperature}°C')
                        self.setpoint = self.schedule.wakeup_temperature  # Assuming you want to return to the wakeup temperature
                        event_triggered['home_from_work'] = True
                    if not event_triggered['weekday_bedtime'] and current_time >= self.schedule.weekday_bedtime:
                        print(f'Bedtime, setting temperature to {self.schedule.bedtime_temperature}°C')
                        self.setpoint = self.schedule.bedtime_temperature
                        event_triggered['weekday_bedtime'] = True
                else:  # Weekend
                    if not event_triggered['weekend_wakeup'] and current_time >= self.schedule.weekend_wakeup_time:
                        print(f'Waking up, setting temperature to {self.schedule.wakeup_temperature}°C')
                        self.setpoint = self.schedule.wakeup_temperature
                        event_triggered['weekend_wakeup'] = True
                    if not event_triggered['weekend_bedtime'] and current_time >= self.schedule.weekend_bedtime:
                        print(f'Bedtime, setting temperature to {self.schedule.bedtime_temperature}°C')
                        self.setpoint = self.schedule.bedtime_temperature
                        event_triggered['weekend_bedtime'] = True

            temp = self.read_temp()

            setpoint = self.setpoint
            assert 10 <= setpoint <= 25, f'{setpoint=} out of range.'

            self.control_step(temp=temp, setpoint=self.setpoint)
            if (step % self.log_interval) == 0:
                self.temp_history.append(temp)
                self.setpoint_history.append(setpoint)
                self.time_history.append(datetime.now())
                print(f'Temp: {temp}°C | Setpoint: {setpoint}°C | Heater: {"ON" if self.is_heater_on() else "OFF"}')

            sleep(self.update_time)
            step += 1

    @abstractmethod
    def control_step(self, temp, setpoint):
        raise NotImplementedError
