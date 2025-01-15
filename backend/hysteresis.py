from controller import TemperatureController
from RPi import GPIO


class HysteresisController(TemperatureController):
    def __init__(self, hysteresis=0.25, **kwargs):
        super().__init__(**kwargs)
        self.hysteresis = hysteresis

    def control_step(self, temp, setpoint):
        if temp < setpoint - self.hysteresis and self.is_heater_off():
            print(f'Heater turned on. Temp: {temp}°C | Setpoint: {setpoint}°C')
            self.turn_on_heater()
        elif temp >= setpoint + self.hysteresis and self.is_heater_on():
            print(f'Heater turned off. Temp: {temp}°C | Setpoint: {setpoint}°C')
            self.turn_off_heater()
