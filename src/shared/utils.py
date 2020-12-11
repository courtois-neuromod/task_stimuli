import psutil


def check_power_plugged():
    battery = psutil.sensors_battery()
    if battery:
        return battery.power_plugged
    else:
        return True
