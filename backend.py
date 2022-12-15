from hysteresis import HysteresisController
from controller import TemperatureController
import argparse

args = argparse.ArgumentParser()
args.add_argument('--default_setpoint', type=float, default=19.5)
args.add_argument('--timespan', type=int, default=60)
args.add_argument('--update_time', type=int, default=2)
args.add_argument('--hysteresis', type=float, default=0.25)
args.add_argument('--relay_pin', type=int, default=35)
args.add_argument('--data_file', type=str, default='data.json')
args.add_argument('--config_file', type=str, default='config.json')
args.add_argument('--setpoint_api', type=str, default='http://localhost:8050/setpoint')
args.add_argument('--supress_gpio_warnings', type=bool, default=True)
args.add_argument('--reinit_output', default=False, action='store_true')

args = args.parse_args()

if __name__ == '__main__':
    controller = HysteresisController(**vars(args))
    controller.control_loop()
