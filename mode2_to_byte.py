#!/usr/bin/env python 
#Copyright 2013, Peter Cock. All rights reserved.
#Released under the MIT License.
#!/usr/bin/python3
import sys
import smbus
import RPi.GPIO as GPIO

from datetime import datetime
import os
import time


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
	
	
global powerdata

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


def expand(code):
    return tuple(min(1, code & (2**(7-i))) for i in range(8))
mapping = dict((expand(code), code) for code in range(256))
assert len(mapping) == 256

powerdata = []
code = []
try:
    line = next(sys.stdin)
    #while line.startswith("space "):
    #    line = next(sys.stdin)
    while line:
        try:
            assert line.startswith("pulse ") or line.startswith("space ")
            code.append(str(line).rstrip() + '\n')
        except:
            try:
                assert line.startswith("pulse ")
                code.append(str(line).rstrip() + '\n')
            except:
                code.append(str(line).rstrip() + '\n')
                pass
        try:
            on = int(line.split(None, 1)[1])
        except:
            pass
        line = next(sys.stdin)
        try:
            assert line.startswith("space ") or line.startswith("pulse ")
            code.append(str(line).rstrip() + '\n')
        except:
            code.append(str(line).rstrip() + '\n')
            pass
        try:
            off = int(line.split(None, 1)[1])
            #if 700 < on < 1300 and 2700 < off:
            #    code.append(line) # 1ms on, 3ms off
            #elif 2700 < on < 3300 and 700 < off:
            #    code.append(line) # 3ms on, 1 ms off
            #else:
                #print("? (%i, %i)" % (on, off))
            #    code.append(line)
            if 1 == 1 :
                #Long pause at end of signal
                try:
                    value = mapping[tuple(code)]
                    print("%s - %i - 0x%X" % ("".join(str(x) for x in code), value, value))
                    print(1)
                except KeyError:
                    #print("".join(str(x) for x in code))
                    for x in code:
                        if 'driver' not in str(x):
                            if "".join(str(x).split('\n')[0]) != '':
                                powerdata.append("".join(str(x).split('\n')[0]))
                                print("".join(str(x).split('\n')[0]))

                            if "".join(str(x).split('\n')[1]) != '':
                                powerdata.append("".join(str(x).split('\n')[1]))
                                print("".join(str(x).split('\n')[1]))
                            #if 'pulse' in powerdata[len(powerdata)-1] and 'pulse' in powerdata[len(powerdata)-2]:
                            #    print('DONE = CTRL+C')
                code = []
            line = next(sys.stdin)

        except:
            pass
except StopIteration:
    #Finished
    print("The end")
    #print(powerdata)
    pass
except KeyboardInterrupt:
    #Told to quit
    print("Stopped")
    #print(powerdata)
    pass

pulse1 = ''
for i in powerdata:
	if i != '':
		pulse1 = pulse1 +'\n' + i

#print(pulse1)


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

##mode2 --driver default --device /dev/lirc0

##mode2 --driver default --device /dev/lirc0 | sudo python3 /home/osmc/scripts/mode2_to_byte.py