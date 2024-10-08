from xbmc import Monitor, log, sleep, LOGINFO, LOGERROR, LOGDEBUG
from xbmcaddon import Addon
from xbmcgui import Dialog

import os
os.environ['LG_WD'] = '/storage/.kodi/temp'

import sys
sys.path.append('/storage/.kodi/addons/virtual.rpi-tools/lib')

import lgpio

addon =  Addon(id='service.joy-it.fancontrol')
LOC = addon.getLocalizedString
addonName = addon.getAddonInfo('name')
addonVersion = addon.getAddonInfo('version')

MIN_TEMP = int(addon.getSetting('start_cooling'))		# Temperature at which the fan goes on,
														# under this temp value fan is switched to the FAN_OFF speed
MAX_TEMP = 70											# over this temp value fan is switched to the FAN_MAX speed
FAN_LOW = 35											# lower side of the fan speed range during cooling
FAN_OFF = 20											# fan speed to set if the detected temp is below MIN_TEMP
FAN_MAX = 100											# fan speed to set if the detected temp is above MAX_TEMP
FAN_HYSTERESIS = 2										# fan hysteresis between start and stop (half value)

fanSpeed = 0
active_coolDown = False                                # Variable to cool down
fanStatus = False
count = 0
step = (FAN_MAX - FAN_LOW) / (MAX_TEMP - MIN_TEMP)

# Get CPU's temperature
def getCpuTemperature():
	with open('/sys/class/thermal/thermal_zone0/temp') as f:
		return float(f.read()) / 1000

monitor = Monitor()
log('[%s %s] Joy-IT fan control service started' % (addonName, addonVersion), LOGINFO)

try:
	handle = lgpio.gpiochip_open(0)
	pin = int(addon.getSetting('gpio_pin'))
	lgpio.gpio_claim_output(handle, pin, FAN_MAX)

	sleep(1000)

	lgpio.tx_pwm(handle, pin, pwm_frequency=25, pwm_duty_cycle=FAN_OFF, pulse_cycles=0)

	while not monitor.abortRequested():
		if monitor.waitForAbort(1): break

		CpuTemp = getCpuTemperature()

		if CpuTemp < MIN_TEMP - FAN_HYSTERESIS:
			fanSpeed = FAN_OFF
			active_coolDown = False

		# Set fan speed to MAXIMUM if the temperature is above MAX_TEMP
		elif CpuTemp > MAX_TEMP:
			fanSpeed = FAN_MAX
			active_coolDown = True

		elif CpuTemp < MIN_TEMP + FAN_HYSTERESIS:
			fanSpeed = FAN_LOW
			active_coolDown = False

		# Caculate dynamic fan speed
		else:
			fanSpeed = int(FAN_LOW + ((CpuTemp - MIN_TEMP) * step))
			active_coolDown = True

		# PWM Output
		lgpio.tx_pwm(handle, pin, pwm_frequency=25, pwm_duty_cycle=fanSpeed, pulse_cycles=0)

		# Debug every x seconds, if enabled
		if addon.getSetting('debug').upper() == 'TRUE' and not (count % int(addon.getSetting('interval'))) and count > 0:
			log('[%s %s] CPU: %s °C, Fan speed %s' % (addonName, addonVersion, CpuTemp.__format__('3.1f'), fanSpeed), LOGDEBUG)
		count += 1

		if fanStatus ^ active_coolDown:
			fanStatus = active_coolDown
			if active_coolDown: log('[%s %s] start active cooling, %s °C, speed %s' % (addonName, addonVersion, CpuTemp.__format__('3.1f'), fanSpeed), LOGINFO)
			else: log('[%s %s] suspend active cooling, %s °C' % (addonName, addonVersion, CpuTemp.__format__('3.1f')), LOGINFO)

	# set fan speed to max when script terminates or aborts (avoids overheating)
	lgpio.tx_pwm(handle, pin, pwm_frequency=25, pwm_duty_cycle=FAN_MAX, pulse_cycles=0)
	sleep(2000)

	# free and close GPIO
	lgpio.gpio_free(handle, pin)
	lgpio.gpiochip_close(handle)

except Exception as e:

	log('[%s %s] %s' % (addonName, addonVersion, str(e)), LOGERROR)
	Dialog().ok(addonName, LOC(32020))


log('[%s %s] Joy-IT fan control service finished' % (addonName, addonVersion), LOGINFO)
