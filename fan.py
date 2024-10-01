from xbmc import Monitor, log, LOGINFO
import os
os.environ['LG_WD'] = '/storage/.kodi/temp'
from gpiozero import CPUTemperature, PWMOutputDevice

led = PWMOutputDevice(17, initial_value=0, frequency=25) # PWM-Pin

startTemp = 60.0 # Temperature at which the fan goes on
coolDown = 50.0  # Temperature to which it is cooled down
active_coolDown = False # Variable to cool down
fanStatus = False

pTemp = 8 # Proportional part
iTemp = 0.2 # Integral part

fanSpeed = 0 # Fan speed
sum = 0 # Memory variable for ishare

monitor = Monitor()

log('Joy-IT fan control service started', LOGINFO)
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
		if active_coolDown: log('active cooling started, %s °C, speed %s' % (actTemp, fanSpeed), LOGINFO)
		else: log('active cooling stopped, %s °C' % actTemp, LOGINFO)

	# PWM output
	led.value = fanSpeed / 100

log('Joy-IT fan control service finished', LOGINFO)
