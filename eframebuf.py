import framebuf

font = open('font.bin', 'rb').read()

if len(font) == 0:
	raise Exception("Couldn't load font")

class EnhancedFrameBuffer:
	def __init__(self, buffer, width, height, format=framebuf.MONO_HLSB):
		self.buffer = buffer
		self.width = width
		self.height = height
		fb = framebuf.FrameBuffer(buffer, width, height, framebuf.MONO_HLSB)
		self.framebuf = fb
		self.fill = fb.fill
		self.pixel = fb.pixel
		self.hline = fb.hline
		self.vline = fb.vline
		self.line = fb.line
		self.rect = fb.rect
		self.fill_rect = fb.fill_rect
		self.text = fb.text
		self.scroll = fb.scroll
		self.blit = fb.blit

	def narrowtext(self, string, x=0, y=0):
		UNKNOWN_CHAR = 0x3F - 0x20 # Question mark
		for c in string:
			font_index = ord(c)
			if font_index < 0x20:
				# raise Exception("Non-printable Character")
				font_index = UNKNOWN_CHAR
			elif font_index < 0x80:
				font_index = font_index - 0x20
			elif font_index < 0xA0:
				# raise Exception("Unmapped Character")
				font_index = UNKNOWN_CHAR
			elif font_index < 0xC0:
				font_index = font_index - 0xA0 + 0x5F
			else:
				# raise Exception("Unmapped Character")
				font_index = UNKNOWN_CHAR

			font_char = font_index * 8
			font_width = font[font_char + 0]

			if not self._bitmap_byte(font[font_char + 1:font_char + 8], x, 1, font_width, 7):
				break

			x = x + font_width

	def bitmap(self, buffer, x, y, w, h, overwrite=False):
		ret = False
		for i in range(w / 8):
			o = i*8
			ret = self._bitmap_byte(buffer[o:o+8],x+o,y,min(w,8),h,overwrite)
		return ret

	def _bitmap_byte(self, buffer, x, y, w, h, overwrite=False):
		num_modules = int(self.width / 8)

		split = x % 8

		# first module
		m = int(x / 8)

		if x < 0:
			split = split - 1
			m = m - 1

		# print("Modules: %d x: %d split: %d first module: %d" % (num, x, split, m))

		if m >= num_modules:
			return False

		if m >= 0:
			for cy in range(h):
				if cy + y < self.height:
					buffer_offset = ((cy + y) * num_modules) + m
					newByte = buffer[cy] >> split
					if not overwrite:
						newByte = newByte | self.buffer[buffer_offset]
					self.buffer[buffer_offset] = newByte

		# possible second byte
		if m >= -1 and split + w > 8:
			if m + 1 >= num_modules:
				return False

			hang = 8 - split
			for cy in range(h):
				if cy + y < self.height:
					buffer_offset = ((cy + y) * num_modules) + m + 1
					newByte = (buffer[cy] << hang)
					if not overwrite:
						newByte = newByte | self.buffer[buffer_offset]
					self.buffer[buffer_offset] = newByte

		return True
