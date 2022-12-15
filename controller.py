from collections import deque
from time import sleep

from tmp75 import TMP75
import RPi.GPIO as GPIO
from abc import ABC, abstractmethod
import json
import requests


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
            timespan=60,  # in minutes
            data_file='data.json',
            config_file='config.json',
            setpoint_api='http://localhost:8050/setpoint',
            supress_gpio_warnings=True,
            reinit_output=False,

    ):
        self.tmp75 = TMP75()
        print(f'Initialized TMP75 sensor: {self.tmp75.read_temp()}°C')
        self.relay_pin = relay_pin
        GPIO.setwarnings(~supress_gpio_warnings)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        self.setpoint = default_setpoint
        self.update_time = update_time
        self.max_length = int(timespan * 60 / update_time) + 1
        self.setpoint_api = setpoint_api
        self.data_file = data_file

        json.dump({
            'update_time': self.update_time,
            'timespan': timespan
        }, open(config_file, 'w'))

        # json.dump({
        #     'setpoint': self.setpoint}
        #     , open(self.setpoint_file, 'w'))

        temp = self.read_temp()

        if reinit_output:
            self.temp_history = deque([temp for _ in range(self.max_length)], maxlen=self.max_length)
            self.setpoint_history = deque([self.setpoint for _ in range(self.max_length)], maxlen=self.max_length)
        else:
            data = json.load(open(self.data_file, 'r'))
            assert len(data['temp']) == len(data['setpoint']) == self.max_length, \
                'Data file is not compatible with current settings. Use --reinit_output to reinitialize output.'
            self.temp_history = deque(data['temp'], maxlen=self.max_length)
            self.setpoint_history = deque(data['setpoint'], maxlen=self.max_length)
            self.setpoint = self.setpoint_history[-1]

    def read_temp(self):
        return self.tmp75.read_temp()

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

    def read_setpoint(self):
        return requests.get(self.setpoint_api).json()

    def control_loop(self):
        while True:
            temp = self.read_temp()
            try:
                setpoint = self.read_setpoint()
                assert 10 <= setpoint <= 25, f'{setpoint=} out of range.'
            except:
                setpoint = self.setpoint_history[-1]
                print(f'Error reading setpoint. Using previous setpoint. {setpoint=}')

            if setpoint != self.setpoint:
                self.setpoint = setpoint
                print(f'Setpoint changed to {self.setpoint}°C')

            self.control_step(temp=temp, setpoint=self.setpoint)
            self.temp_history.append(temp)
            self.setpoint_history.append(setpoint)

            json.dump({
                'temp': list(self.temp_history),
                'setpoint': list(self.setpoint_history),
            }, open(self.data_file, 'w'))

            sleep(self.update_time)

    @abstractmethod
    def control_step(self, temp, setpoint):
        raise NotImplementedError
