from time import sleep

from tmp75 import TMP75
import RPi.GPIO as GPIO
from abc import ABC, abstractmethod


class TemperatureController(ABC):
    """
    Base class for a temperature controller that reads the temperature from a TMP75 sensor and controls a relay
    connected to a heating element in an attempt to maintain a setpoint temperature.
    """

    def __int__(
            self,
            relay_pin=35,
            setpoint=20.5,
            update_time=3,
            supress_gpio_warnings=True,

    ):
        self.tmp75 = TMP75()
        self.relay_pin = relay_pin
        GPIO.setwarnings(~supress_gpio_warnings)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        self.setpoint = setpoint
        self.update_time = update_time

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

    def run(self):
        while True:
            self.control_step()
            sleep(self.update_time)

    @abstractmethod
    def control_step(self):
        raise NotImplementedError
