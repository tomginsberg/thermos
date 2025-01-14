from controller import TemperatureController


class OnOffController(TemperatureController):
    def control_step(self, temp, setpoint):
        if temp < setpoint:
            if not self.heater_state():
                print(f'Heater turned on. Temp: {temp}°C | Setpoint: {setpoint}°C')
            self.turn_on_heater()
        elif temp >= setpoint:
            if self.heater_state():
                print(f'Heater turned off. Temp: {temp}°C | Setpoint: {setpoint}°C')
            self.turn_off_heater()
