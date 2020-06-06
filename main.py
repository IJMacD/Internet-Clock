from machine import Pin, SPI, I2C
import time, network, micropython, gc
import max7219

gc.collect()

# Available pins
# 0, 2, 4, 5, 12, 13, 14, 15, and 16

# Pin(2) == GPIO2 == D4
# Pin(4) == GPIO4 == D2
# Pin(5) == GPIO5 == D1
# Pin(12) == GPIO12 == D6
# Pin(14) == GPIO14 == D5
# Pin(16) == GPIO16 == D0  (unused)
spi = SPI(-1, baudrate=100000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(4), miso=Pin(16))
display = max7219.Matrix8x8(spi, Pin(5), 5)

gc.collect()

from BME280_min import BME280

CLOCK_ICON = bytearray([0x3c,0x52,0x91,0x91,0x8d,0x81,0x42,0x3c])
WIFI_ICON = bytearray([0xf0,0x08,0xe4,0x12,0xc9,0x25,0x15,0x95])
TRAIN_ICON = bytearray([0x08,0x04,0xE0,0xA4,0xBE,0x82,0xFE,0x24])
SOLAR_ICON = bytearray([0x00,0xFC,0xAA,0xAA,0x7E,0x55,0x55,0x3F])
BATT_ICON = bytearray([0x18,0x7E,0x42,0x4A,0x5A,0x52,0x42,0x7E])
PLUG_ICON = bytearray([0x00,0x00,0x06,0x0B,0x72,0xCB,0x06,0x00])
BOLT_ICON = bytearray([0x00,0x04,0x08,0x10,0x3C,0x08,0x10,0x20])

gc.collect()

# ESP8266 - Pin assignment
i2c = I2C(scl=Pin(14), sda=Pin(12), freq=10000)

temp=0
hum=0
pres=0

def read_temp ():
	global temp, hum, pres
	bme = BME280(i2c=i2c)
	temp = bme.temperature
	hum = bme.humidity
	pres = bme.pressure

display.brightness(0)

def led_print(msg, narrow=False):
	display.fill(0)
	if msg is not None:
		if len(msg) > 5 or narrow:
			display.narrowtext(msg, 0, 1)
		else:
			display.text(msg,0,0,1)
	display.show()

def led_iconprint(icon, msg, narrow=False):
	display.fill(0)
	display.bitmap(icon, 0, 0, 8, 8)
	if len(msg) > 4 or narrow:
		display.narrowtext(msg, 9, 1)
	else:
		display.text(msg,9,0,1)
	display.show()

led_print("Hello")

wlan = network.WLAN(network.STA_IF)

while not wlan.isconnected():
	time.sleep_ms(100)

led_iconprint(WIFI_ICON, wlan.ifconfig()[0][8:])
time.sleep(2)

from machine import RTC
rtc = RTC()

import ntptime
ntpfail = 1

while ntpfail:
	try:
		ntptime.settime() # set the rtc datetime from the remote server
		ntpfail = 0
	except:
		led_print("T F{}".format(ntpfail))
		ntpfail = ntpfail + 1

# led_print("T OK");
display.fill(0)
display.bitmap(CLOCK_ICON, 0, 0, 8, 8)
display.text("OK", 16, 0, 1)
display.show()
time.sleep(1)

from machine import Timer

def print_time(show_seconds=False):
	utc = rtc.datetime()	# get the date and time in UTC

	tz = 8

	utc_hours = utc[4]

	hours = (utc_hours + tz) % 24
	minutes = utc[5]
	seconds = utc[6]
	
	if show_seconds:
		display.fill(0)
		display.narrowtext('%02d:%02d:%02d' % (hours,minutes,seconds), 3, 1)
		display.show()
	else:
		led_print('%02d%s%02d' % (hours,(":" if seconds%2 else " "),minutes))

def print_date():
	utc = rtc.datetime()	# get the date and time in UTC

	year = utc[0]
	month = utc[1]
	day = utc[2]
	
	led_print('%04d%02d%02d' % (year,month,day))
	
def print_temp():
	read_temp()
	led_print(temp)
	
def print_hum():
	read_temp()
	led_print(hum)
	
def print_pres():
	read_temp()
	led_print(pres)

from solar import read_solar 
from stock import read_stock

msg = "cycle"
train_pos = -8

def update_display ():
	global msg, train_pos
	if msg == None or msg == "time":
		print_time()
	elif msg == "times":
		print_time(True)
	elif msg == "date":
		print_date()
	elif msg == "temp":
		print_temp()
	elif msg == "humidity":
		print_hum()
	elif msg == "pressure":
		print_pres()
	elif msg == "cycle":
		s = int(rtc.datetime()[6] / 10)
		if s in [0,1,3,4]:
			print_time()
		elif s == 2:
			print_temp()
		else:
			print_pres()
	elif msg == "train":
		display.fill(0)
		display.bitmap(TRAIN_ICON,train_pos, 0, 8, 8)
		display.show()
		train_pos = train_pos + 1
		if train_pos > 40:
			msg = "cycle"
			train_pos = -8
	elif msg == "solar panel":
		data = read_solar()
		led_iconprint(SOLAR_ICON, str(data[1]))
		# pass
	elif msg == "solar current":
		data = read_solar()
		led_iconprint(BOLT_ICON, str(data[2]))
		# pass
	elif msg == "solar battery":
		data = read_solar()
		led_iconprint(BATT_ICON, str(data[3]))
		# pass
	elif msg == "solar power":
		data = read_solar()
		led_iconprint(PLUG_ICON, str(float(data[1]) * float(data[2])))
		# pass
	elif msg[0:5] == "stock":
		value = read_stock(msg[6:])
		led_print(value)
	elif isinstance(msg, bytearray):
		w = len(msg)
		display.fill(0)
		display.bitmap(msg,0,0,len(msg),8)
		display.show()
	else:
		led_print(msg)

tmr = Timer(-1)
tmr.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: update_display())

tmr2 = Timer(-1)
tmr2.init(period=3 * 60 * 60 * 1000, mode=Timer.PERIODIC, callback=lambda t: ntptime.settime())

import socket
addr = socket.getaddrinfo('0.0.0.0', 8000)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
# s.settimeout(0.1)

def check_conn():
	global msg
	try:
		cl, addr = s.accept()
		bytes = cl.readline()
		msg = bytes.decode('utf-8')[:-1]
		
		if msg[:7] == "bitmap ":
			tail = msg[7:]
			l = int(len(tail)/2)
			msg = bytearray(l)
			for i in range(l):
				msg[i] = int(tail[i*2:i*2+2], 16)
		
		cl.send("thanks\n")
		# led_print("conn")
		cl.close()
		
		update_display()
	except OSError as e:
		# if e.args[0] == EAGAIN:
			# pass
		pass
		
	# mem0 = gc.mem_alloc()
	# gc.collect()
	# mem1 = gc.mem_alloc()
	# mem_free = gc.mem_free()
	
	# print("Used: %d, Free: %d, Freed: %d" % (mem1, mem_free, mem0 - mem1))
		

while True:
	check_conn()

# tmr2 = Timer(-1)
# tmr2.init(period=100, mode=Timer.PERIODIC, callback=check_conn)
