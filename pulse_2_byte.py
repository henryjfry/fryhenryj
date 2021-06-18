#!/usr/bin/python3
import sys
import smbus
import RPi.GPIO as GPIO

from datetime import datetime
import os
import time

print(sys.stdin)


rev = GPIO.RPI_REVISION
if rev == 2 or rev == 3:
	bus = smbus.SMBus(1)
else:
	bus = smbus.SMBus(0)
	

#########################
# Common
irconffile = "/etc/lirc/lircd.conf.d/argon.lircd.conf"

# I2C
address = 0x1a	  # I2C Address
command = 0xaa	  # I2C Command

# Constants
PULSETIMEOUTMS = 1000
VERIFYTARGET = 3
PULSEDATA_MAXCOUNT = 200	# Fail safe

# NEC Protocol Constants
PULSEBIT_MAXMICROS_NEC = 2500
PULSEBIT_ZEROMICROS_NEC = 1000

PULSELEADER_MINMICROS_NEC = 8000
PULSELEADER_MAXMICROS_NEC = 10000
PULSETAIL_MAXMICROS_NEC = 12000


def getbytestring(pulsedata):
	outstring = ""
	for curbyte in pulsedata:
		tmpstr = hex(curbyte)[2:]
		while len(tmpstr) < 2:
			tmpstr = "0" + tmpstr
		outstring = outstring+tmpstr
	return outstring

def displaybyte(pulsedata):
	print (getbytestring(pulsedata))


def pulse2byteNEC(pulsedata):
	outdata = []
	bitdata = 1
	curbyte = 0
	bitcount = 0
	for (mode, duration) in pulsedata:
		if mode == 1:
			continue
		elif duration > PULSEBIT_MAXMICROS_NEC:
			continue
		elif duration > PULSEBIT_ZEROMICROS_NEC:
			curbyte = curbyte*2 + 1
		else:
			curbyte = curbyte*2

		bitcount = bitcount + 1
		if bitcount == 8:
			outdata.append(curbyte)
			curbyte = 0
			bitcount = 0
	# Shouldn't happen, but just in case
	if bitcount > 0:
		outdata.append(curbyte)

	return outdata


def bytecompare(a, b):
	idx = 0
	maxidx = len(a)
	if maxidx != len(b):
		return 1
	while idx < maxidx:
		if a[idx] != b[idx]:
			return 1
		idx = idx + 1
	return 0
	

#mode2 --driver default --device /dev/lirc0

pulse1 = '''
space 16777215
pulse 9008
space 4451
pulse 610
space 518
pulse 609
space 519
pulse 612
space 514
pulse 583
space 520
pulse 608
space 517
pulse 610
space 519
pulse 585
space 515
pulse 609
space 1622
pulse 608
space 519
pulse 609
space 518
pulse 583
space 519
pulse 609
space 1624
pulse 607
space 1622
pulse 608
space 522
pulse 605
space 1620
pulse 609
space 1626
pulse 606
space 517
pulse 607
space 1622
pulse 582
space 545
pulse 582
space 1649
pulse 581
space 522
pulse 606
space 1621
pulse 609
space 519
pulse 609
space 519
pulse 582
space 1648
pulse 582
space 520
pulse 607
space 1622
pulse 614
space 513
pulse 611
space 1624
pulse 603
space 519
pulse 582
space 1649
pulse 580
space 1648
pulse 583
space 43549
pulse 9006
space 2195
pulse 609
pulse 132661
'''

pulsedata = []

for i in pulse1.splitlines():
	if i != '':
		new_var = []
		new_var.append(int(i.replace('space','0,').replace('pulse','1,').split(',')[0]))
		new_var.append(int(i.replace('space','0,').replace('pulse','1,').split(',')[1]))
		pulsedata.append(new_var)

print(pulsedata)

powerdata = pulse2byteNEC(pulsedata)

if powerdata[len(powerdata)-1] == 1:
	powerdata2 = (powerdata[:-1])
try:
	print(powerdata2)
	powerdata = powerdata2
except:
	print(powerdata)

address = 26
command = 170
print('bus.write_i2c_block_data(' + str(address) +  ', ' + str(command) + ', ' + str(powerdata) + ')')
#bus.write_i2c_block_data(address, command, powerdata)

#mode2 --driver default --device /dev/lirc0