
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