#!/usr/bin/env python
#https://www.raspberrypi.org/forums/viewtopic.php?p=314087
# 8 band Audio equaliser from wav file

import alsaaudio as aa
import smbus
from struct import unpack
import numpy as np
import wave

bus=smbus.SMBus(0)     #Use '1' for newer Pi boards;

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
matrix    = [0,0,0,0,0,0,0,0]
power     = []
weighting = [2,2,8,8,16,32,64,64] # Change these according to taste

# Set up audio
wavfile = wave.open('/home/pi/python_programs/NorwegianWood.wav','r')
sample_rate = wavfile.getframerate()
no_channels = wavfile.getnchannels()
chunk       = 4096 # Use a multiple of 8
output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
output.setchannels(no_channels)
output.setrate(sample_rate)
output.setformat(aa.PCM_FORMAT_S16_LE)
output.setperiodsize(chunk)

# Return power array index corresponding to a particular frequency
def piff(val):
   return int(2*chunk*val/sample_rate)

def calculate_levels(data, chunk,sample_rate):
   global matrix
   # Convert raw data (ASCII string) to numpy array
   data = unpack("%dh"%(len(data)/2),data)
   data = np.array(data, dtype='h')
   # Apply FFT - real data
   fourier=np.fft.rfft(data)
   # Remove last element in array to make it the same size as chunk
   fourier=np.delete(fourier,len(fourier)-1)
   # Find average 'amplitude' for specific frequency ranges in Hz
   power = np.abs(fourier)
   matrix[0]= int(np.mean(power[piff(0)    :piff(156):1]))
   matrix[1]= int(np.mean(power[piff(156)  :piff(313):1]))
   matrix[2]= int(np.mean(power[piff(313)  :piff(625):1]))
   matrix[3]= int(np.mean(power[piff(625)  :piff(1250):1]))
   matrix[4]= int(np.mean(power[piff(1250) :piff(2500):1]))
   matrix[5]= int(np.mean(power[piff(2500) :piff(5000):1]))
   matrix[6]= int(np.mean(power[piff(5000) :piff(10000):1]))
   matrix[7]= int(np.mean(power[piff(10000):piff(20000):1]))
   # Tidy up column values for the LED matrix
   matrix=np.divide(np.multiply(matrix,weighting),1000000)
   # Set floor at 0 and ceiling at 8 for LED matrix
   matrix=matrix.clip(0,8)
   return matrix

# Process audio file
print "Processing....."
data = wavfile.readframes(chunk)
while data!='':
   output.write(data)
   matrix=calculate_levels(data, chunk,sample_rate)
   for i in range (0,8):
      Set_Column((1<<matrix[i])-1,0xFF^(1<<i))
   data = wavfile.readframes(chunk)
   TurnOffLEDS()
