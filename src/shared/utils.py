import psutil

def check_power_plugged():
    battery = psutil.sensors_battery()
    return battery.power_plugged
