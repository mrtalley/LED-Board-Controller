#!/usr/bin/env python
#
# Audio 2 channel volume analyser using MCP2307
#
# Audio from wav file on SD card
#
import alsaaudio as aa
import audioop
from time import sleep
import smbus
import struct
import numpy as np
import wave

bus=smbus.SMBus(0)     #Use '1' for newer Pi boards
ADDR   = 0x20         #The I2C address of MCP23017
DIRA   = 0x00         #PortA I/O direction, by pin. 0=output, 1=input
DIRB   = 0x01         #PortB I/O direction, by pin. 0=output, 1=input
BANKA  = 0x12         #Register address for Bank A
BANKB  = 0x13         #Register address for Bank B

#Set up the 23017 for 16 output pins
bus.write_byte_data(ADDR, DIRA, 0);  #all zeros = all outputs on Bank A
bus.write_byte_data(ADDR, DIRB, 0);  #all zeros = all outputs on Bank B

def TurnOffLEDS ():
   bus.write_byte_data(ADDR, BANKA, 0xFF)  #set all columns high
   bus.write_byte_data(ADDR, BANKB, 0x00)  #set all rows low

def Set_Column(row, col):
   bus.write_byte_data(ADDR, BANKA, col)
   bus.write_byte_data(ADDR, BANKB, row)

# Initialise matrix
TurnOffLEDS()
matrix=[0,0,0,0,0,0,0,0]

# Set up audio
wavfile = wave.open('/home/pi/python_programs/NorwegianWood.wav','r')
sample_rate = wavfile.getframerate()
no_channels = wavfile.getnchannels()
chunk = 1024
output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
output.setchannels(no_channels)
output.setrate(sample_rate)
output.setformat(aa.PCM_FORMAT_S16_LE)
output.setperiodsize(chunk)

print "Processing....."

data = wavfile.readframes(chunk)
while data!='':
   output.write(data)
   # Split channel data and find maximum volume
   channel_l=audioop.tomono(data, 2, 1.0, 0.0)
   channel_r=audioop.tomono(data, 2, 0.0, 1.0)
   max_vol_factor =5000
   max_l = audioop.max(channel_l,2)/max_vol_factor
   max_r = audioop.max(channel_r,2)/max_vol_factor
   # Write to 8x8 LED
   for i in range (0,4):
      Set_Column((1<<max_l)-1,0xFF^(1<<i))
   TurnOffLEDS()
   for i in range (4,8):
      Set_Column((1<<max_r)-1,0xFF^(1<<i))
   data = wavfile.readframes(chunk)
   TurnOffLEDS()
