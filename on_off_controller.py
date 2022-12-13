from controller import TemperatureController
from time import sleep


class OnOffController(TemperatureController):
    def control_step(self):
        temp = self.read_temp()
        if temp < self.setpoint:
            self.turn_on_heater()
        else:
            self.turn_off_heater()
