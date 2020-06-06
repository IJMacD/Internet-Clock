
def http_get(url):
	import socket
	_, _, host, path = url.split('/', 3)
	addr = socket.getaddrinfo(host, 80)[0][-1]
	s = socket.socket()
	s.connect(addr)
	s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
	header_done = False
	while True:
		data = s.recv(1024)
		if data:
			head, body = str(data, 'utf8').split('\r\n\r\n', 2)
			return body
		else:
			break
	s.close()

from machine import Timer
tmr2 = None

solar = None
watch_mode = False

def fetch_solar ():
	global solar, watch_mode
	if watch_mode:
		data = http_get('http://solar.ijmacd.com/update.php?method=data&device=1714520,3422737&delta=86400&limit=2').split('\r\n')[0].split('\t')
		try:
			date = data[0]
			panel = (float(data[1]) + float(data[4])) / 2	# AVG
			current = (float(data[2]) + float(data[5]))		# SUM
			batt = (float(data[3]) + float(data[6])) / 2	# AVG
			solar = (date, panel, current, batt)
		except IndexError:
			solar = ("",0, 0, 0)
		watch_mode = False
		print("Fetched Solar Data %s" % date)

def read_solar():
	global watch_mode, solar, tmr2

	watch_mode = True

	if solar is None:
		fetch_solar()

	if tmr2 is None:
		tmr2 = Timer(-1)
		tmr2.init(period=60 * 1000, mode=Timer.PERIODIC, callback=lambda t: fetch_solar())

	return solar