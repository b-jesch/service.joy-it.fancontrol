import gpiozero
from xbmc import Monitor, log, LOGINFO, LOGERROR, LOGDEBUG
from xbmcaddon import Addon
from xbmcgui import Dialog

import os
os.environ['LG_WD'] = '/storage/.kodi/temp'

from gpiozero import CPUTemperature, PWMOutputDevice
from gpiozero.pins import lgpio

addon =  Addon(id='service.joy-it.fancontrol')
LOC = addon.getLocalizedString
addonName = addon.getAddonInfo('name')
addonVersion = addon.getAddonInfo('version')

MIN_TEMP = int(addon.getSetting('start_cooling'))		# Temperature at which the fan goes on,
														# under this temp value fan is switched to the FAN_OFF speed
MAX_TEMP = 75											# over this temp value fan is switched to the FAN_MAX speed
FAN_LOW = 40											# lower side of the fan speed range during cooling
FAN_HIGH = 99											# higher side of the fan speed range during cooling
FAN_OFF = 20											# fan speed to set if the detected temp is below MIN_TEMP
FAN_MAX = 100											# fan speed to set if the detected temp is above MAX_TEMP
FAN_HYSTERESIS = 2										# fan hysteresis between start and stop (half value)

fanSpeed = 0
active_coolDown = False                                # Variable to cool down
fanStatus = False
count = 0

monitor = Monitor()
log('[%s %s] Joy-IT fan control service started' % (addonName, addonVersion), LOGINFO)

try:
	fan = PWMOutputDevice(int(addon.getSetting('gpio_pin')), initial_value=0, frequency=25) # PWM-Pin

	while not monitor.abortRequested():
		if monitor.waitForAbort(1): break

		CpuTemp = CPUTemperature().temperature

		if CpuTemp < MIN_TEMP - FAN_HYSTERESIS:
			fanSpeed = FAN_OFF
			active_coolDown = False

		# Set fan speed to MAXIMUM if the temperature is above MAX_TEMP
		elif CpuTemp > MAX_TEMP:
			fanSpeed = FAN_MAX
			active_coolDown = True

		# Caculate dynamic fan speed
		else:
			if CpuTemp > MIN_TEMP + FAN_HYSTERESIS:
				step = (FAN_HIGH - FAN_LOW) / (MAX_TEMP - MIN_TEMP)
				CpuDiff = CpuTemp -  MIN_TEMP
				fanSpeed = FAN_LOW + CpuDiff * step
				active_coolDown = True

		# PWM Output
		fan.value = fanSpeed / 100

		# Debug every x seconds, if enabled
		if addon.getSetting('debug').upper() == 'TRUE' and not (count % int(addon.getSetting('interval'))) and count > 0:
			log('[%s %s] CPU: %s °C, Fan speed %s' % (addonName, addonVersion, CpuTemp.__format__('3.1f'), int(fanSpeed)), LOGDEBUG)
		count += 1

		if fanStatus ^ active_coolDown:
			fanStatus = active_coolDown
			if active_coolDown: log('[%s %s] start active cooling, %s °C, speed %s' % (addonName, addonVersion, CpuTemp.__format__('3.1f'), int(fanSpeed)), LOGINFO)
			else: log('[%s %s] suspend active cooling, %s °C' % (addonName, addonVersion, CpuTemp.__format__('3.1f')), LOGINFO)

except gpiozero.GPIOZeroError as e:

	log('[%s %s] %s' % (addonName, addonVersion, str(e)), LOGERROR)
	Dialog().ok(addonName, LOC(32020))

fan.off()
fan.close()

log('[%s %s] Joy-IT fan control service finished' % (addonName, addonVersion), LOGINFO)
