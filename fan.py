from xbmc import Monitor, log, LOGINFO, LOGERROR
from xbmcaddon import Addon
from xbmcgui import Dialog

import os
os.environ['LG_WD'] = '/storage/.kodi/temp'
from gpiozero import CPUTemperature, PWMOutputDevice

addon =  Addon(id='service.joy-it.fancontrol')
LOC = addon.getLocalizedString
addonName = addon.getAddonInfo('name')
addonVersion = addon.getAddonInfo('version')

startTemp = float(addon.getSetting('start_cooling'))   # Temperature at which the fan goes on
coolDown = float(addon.getSetting('stop_cooling'))     # Temperature to which it is cooled down
active_coolDown = False                                # Variable to cool down
fanStatus = False

pTemp = 8 # Proportional part
iTemp = 0.2 # Integral part

fanSpeed = 0 # Fan speed
sum = 0 # Memory variable for ishare

monitor = Monitor()

try:
	led = PWMOutputDevice(int(addon.getSetting('gpio_pin')), initial_value=0, frequency=25) # PWM-Pin

	log('[%s %s] Joy-IT fan control service started' % (addonName, addonVersion), LOGINFO)
	while not monitor.abortRequested():
		if monitor.waitForAbort(1): break

		cpu = CPUTemperature() # Reading the current temperature
		actTemp = cpu.temperature # Current temperature as float variable

		if actTemp < coolDown: active_coolDown = False # do not cool
		else: active_coolDown = True # cool

		diff = actTemp - startTemp
		sum += diff
		pDiff = diff * pTemp
		iDiff = sum * iTemp

		# Adjust fan speed
		if active_coolDown:
			fanSpeed = pDiff + iDiff + 35

		# set fan to zero
		else: fanSpeed = 0

		# Set boundary values
		if fanSpeed > 100: fanSpeed = 100

		if sum > 100: sum = 100
		elif sum < -100: sum = -100

		if fanStatus ^ active_coolDown:
			fanStatus = active_coolDown
			if active_coolDown: log('[%s %s] active cooling started, %s °C, speed %s' % (addonName, addonVersion, actTemp, fanSpeed), LOGINFO)
			else: log('[%s %s] active cooling stopped, %s °C' % (addonName, addonVersion, actTemp), LOGINFO)

		# PWM output
		led.value = fanSpeed / 100

except Exception as e:

	log(str(e), LOGERROR)
	Dialog().ok(addonName, LOC(32020))

log('[%s %s] Joy-IT fan control service finished' % (addonName, addonVersion), LOGINFO)
