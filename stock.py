import gc

def http_get(url):
	import socket
	_, _, host, path = url.split('/', 3)
	addr = socket.getaddrinfo(host, 80)[0][-1]
	s = socket.socket()
	s.connect(addr)
	s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
	header_done = False
	# while True:
	data = s.recv(1024)
	if data:
		head, body = str(data, 'utf8').split('\r\n\r\n', 2)
		return body
	else:
		# break
		pass
	s.close()

from machine import Timer
tmr = None

symbol = None
data = None
watch_mode = False

def fetch_stock ():
	global data, symbol, watch_mode
	if symbol is None:	
		return
	if watch_mode:
		resp = http_get('http://solar.ijmacd.com/stock.php?symbol='+symbol)
		try:
			row = resp.split('\r\n')[1].split(',')
			data = row[1]
			watch_mode = False
			print("Fetched Stock Data %s" % row[0])
		except:
			print("Error with stock data: " + resp)

def read_stock (s):
	global watch_mode, symbol, tmr
	
	symbol = s

	watch_mode = True

	if data is None:
		fetch_stock()
		gc.collect()

	if tmr is None:
		tmr = Timer(-1)
		tmr.init(period=60 * 1000, mode=Timer.PERIODIC, callback=lambda t: fetch_stock())

	return data