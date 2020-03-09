import max7219
from machine import Pin, SPI, I2C
import time, network

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

import BME280

# ESP8266 - Pin assignment
i2c = I2C(scl=Pin(14), sda=Pin(12), freq=10000)

temp=0
hum=0
pres=0

def read_temp ():
    global temp, hum, pres
    bme = BME280.BME280(i2c=i2c)
    temp = bme.temperature
    hum = bme.humidity
    pres = bme.pressure

display.brightness(0)

def led_print(msg):
    display.fill(0)
    display.text(msg,0,0,1)
    display.show()

led_print("Hello")

wlan = network.WLAN(network.STA_IF)

while not wlan.isconnected():
    time.sleep_ms(100)

from machine import RTC

rtc = RTC()

import ntptime
ntptime.settime() # set the rtc datetime from the remote server

led_print("T OK");

from machine import Timer

# set up ntp refresh
# tmr_t = Timer(-1)
# tmr_t.init(period=30*60*1000, mode=Timer.PERIODIC, callback=lambda t: ntptime.settime())

def print_time():
    utc = rtc.datetime()    # get the date and time in UTC

    tz = 8

    utc_hours = utc[4]

    hours = (utc_hours + tz) % 24
    minutes = utc[5]
    seconds = utc[6]
        
    led_print('%02d%s%02d' % (hours,(":" if seconds%2 else " "),minutes))
    
def print_temp():
    read_temp()
    led_print(temp)
    
def print_hum():
    read_temp()
    led_print(hum)
    
def print_pres():
    read_temp()
    led_print(pres)

msg = None
# count = 0

def update_display (t):
    if msg == None:
        print_time()
    elif msg == "temp":
        print_temp()
    elif msg == "humidity":
        print_hum()
    elif msg == "pressure":
        print_pres()
    else:
        led_print(msg)
    
    # count = count + 1
    
    # if count > 30 * 60:
        # ntptime.settime()

tmr = Timer(-1)
tmr.init(period=1000, mode=Timer.PERIODIC, callback=update_display)

import socket
addr = socket.getaddrinfo('0.0.0.0', 8000)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
# s.settimeout(0.1)

def check_conn(t):
    global msg
    try:
        cl, addr = s.accept()
        bytes = cl.readline()
        msg = bytes.decode('utf-8')[:-1]
        
        if msg == "time":
            msg = None
        
        cl.send("thanks\n")
        # led_print("conn")
        cl.close()
    except OSError as e:
        # if e.args[0] == EAGAIN:
            # pass
        pass

while True:
    check_conn(0)

# tmr2 = Timer(-1)
# tmr2.init(period=100, mode=Timer.PERIODIC, callback=check_conn)