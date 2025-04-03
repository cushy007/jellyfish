#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
"""
https://pillow.readthedocs.io/en/stable/reference/
https://github.com/lincolnloop/python-qrcode

"""
import logging
from copy import copy
from os.path import join

import qrcode
from PIL import Image, ImageDraw, ImageFont

_LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG = {
	'dpi': 300,
	'page': {
		'width': 210,
		'height': 297,
		'margin_top': 10,
		'margin_bottom': 10,
		'margin_left': 10,
		'margin_right': 10,
	},
	'qrcode': {
		'version': 5,
		'size': 28,
		'padding': 3.5,
		'border_width': 0.3,
		'margin': 5,
	}
}


class ConverterException(Exception):
	pass


class PageFullException(Exception):
	pass


class Point:

	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __eq__(self, other):
		return self.x == other.x and self.y == other.y


class ConverterMixin:
	INCH = 25.4
	ALLOWED_DPI = (300, 600, 1200)

	def __init__(self, dpi):
		if dpi not in self.ALLOWED_DPI:
			raise ConverterException("'%s' is not a valid value for DPI setting", dpi)
		self._dpi = dpi

	def size_to_pixels(self, size):
		return round(size * self._dpi / self.INCH)

	@property
	def size_of_a_pixel(self):
		return self.INCH / self._dpi

	def qrcode_nb_of_dots(self, version):
		return (4 * version + 17)

	def qrcode_dot_size_in_pixel(self, size, version):
		return round(size * self._dpi / ((4 * version + 17) *self.INCH))


class Page(ConverterMixin):

	def __init__(self, image_factory=Image, **config):
		self._config = copy(DEFAULT_CONFIG)
		self._config.update(config)
		self._width = self._config['page']['width']
		self._height = self._config['page']['height']
		self._margin_top = self._config['page']['margin_top']
		self._margin_bottom = self._config['page']['margin_bottom']
		self._margin_left = self._config['page']['margin_left']
		self._margin_right = self._config['page']['margin_right']
		ConverterMixin.__init__(self, self._config['dpi'])

		self._page = image_factory.new("RGB", (self.size_to_pixels(self._width), self.size_to_pixels(self._height)), (255, 255, 255))
		self._coord_min = Point(self.size_to_pixels(self._margin_left), self.size_to_pixels(self._margin_top))
		self._coord_max = Point(self.size_to_pixels(self._width - self._margin_right), self.size_to_pixels(self._height - self._margin_bottom))
		self._current_coord = copy(self._coord_min)
		self._next_row_start = self._coord_min.y

	def add_image(self, img):
		if img.width > self._coord_max.x - self._coord_min.x:
			raise ConverterException("Image '%s' is too wide for this page")
		if img.height > self._coord_max.y - self._coord_min.y:
			raise ConverterException("Image '%s' is too high for this page")
		if self._current_coord.x + img.width > self._coord_max.x:
			# go to the next line
			_LOGGER.info("Row is full -> go to the next one")
			self._current_coord.x = self._coord_min.x
			self._current_coord.y = self._next_row_start
			if self._current_coord.y + img.height > self._coord_max.y:
				raise PageFullException()
		self._page.paste(img, (self._current_coord.x, self._current_coord.y))
		self._current_coord.x += img.width
		self._next_row_start = max(self._next_row_start, self._current_coord.y + img.height)

	def save(self, filepath):
		self._page.save(filepath)


class QRCode(ConverterMixin):

	FONT_NAME = "DejaVuSansMono-Bold"

	def __init__(self, **config):
		self._config = copy(DEFAULT_CONFIG)
		self._config.update(config)
		self._version = self._config['qrcode']['version']
		self._size = self._config['qrcode']['size']
		self._padding = self._config['qrcode']['padding']
		self._border_width = self._config['qrcode']['border_width']
		self._margin = self._config['qrcode']['margin']
		ConverterMixin.__init__(self, self._config['dpi'])
		self._box_size = self.qrcode_dot_size_in_pixel(self._size, self._version)

		try:
			self._font = ImageFont.truetype("%s.ttf" % self.FONT_NAME, round(self._size * 2.33))
		except IOError:
			raise Exception("No font found")
		_LOGGER.debug("Creating a QRcode of %smm with dots of %s pixels ", self._size, self._box_size)

	def _generate_text_image(self, text):
		box_sizes = (
			round(self.size_to_pixels(self._size) / 2) + 13,
			round(self.size_to_pixels(self._size) / 3.5) - 11
		)
		img = Image.new("RGB", box_sizes, (255, 255, 255))
		draw = ImageDraw.Draw(img)
		draw.text((round(box_sizes[0] / 2), round(box_sizes[1] / 2)), text, fill='black', font=self._font, anchor="mm")
		return img

	def _generate_frame_image(self, qr_img):
		# surounding rectangle
		start_x = self.size_to_pixels(self._margin + self._border_width / 2)
		start_y = self.size_to_pixels(self._margin + self._border_width / 2)
		width = start_x + self.size_to_pixels(self._size + 2 * self._padding + self._border_width / 2)
		height = start_y + self.size_to_pixels(self._size + 2 * self._padding + self._border_width / 2)
		draw = ImageDraw.Draw(qr_img)
		for coord in (
			(start_x, start_y, width, start_y),
			(width, start_y, width, height),
			(width, height, start_x, height),
			(start_x, height, start_x, start_y),
		):
			draw.line(coord, fill=0, width=self.size_to_pixels(self._border_width))

	def create_qr_code_image(self, data, text):
		qr = qrcode.QRCode(
			error_correction=qrcode.constants.ERROR_CORRECT_H,
			version=self._version,  # determine the number of dots (4 × version number + 17) so version 1 = 21x21 dots
			box_size=self._box_size, # size of each dot in pixels
			border=(self._padding + self._border_width + self._margin) / (self._box_size * self.size_of_a_pixel),  # size of the padding in (n)th of dots (n x box_size)
		)
		qr.add_data(data)
		qr.make()
		qr_img = qr.make_image().convert('RGB')

		self._generate_frame_image(qr_img)
		text_img = self._generate_text_image(text)

		pos = ((qr_img.width - text_img.width) // 2, (qr_img.height - text_img.height) // 2)
		_LOGGER.info("QRcode size in pixels is %sx%s", qr_img.width, qr_img.height)
		qr_img.paste(text_img, pos)

		return qr_img


def generate_qrcodes(dest_dir, filename, data_pairs, page_sizes=(500, 500), qrcode_size=28):
	"""
	dest_dir is the directory in which the file(s) will be generated
	filename is the basename of the generated file(s). It will be appended with -1, -2 and so on if not all QR codes can be put in one file
	data_pairs is a list of (data embedded, text printed at the center of the image)

	"""
	qr_codes = [QRCode(size=qrcode_size, padding=3).create_qr_code_image(data, text) for data, text in data_pairs]
	qr_idx = 0
	page_nb = 1
	while "QR code to generate":
		filepath = join(dest_dir, "%s%d.png" % (filename, page_nb))
		_LOGGER.info("Generating QR codes for in '%s'", filepath)
		page = Page(sizes=page_sizes, margins=(0, 0))
		try:
			while qr_idx < len(qr_codes):
				page.add_image(qr_codes[qr_idx])
				qr_idx += 1
		except PageFullException:
			_LOGGER.info("Page is full -> continue in a new one")
			page.save(filepath)
			page_nb += 1
			continue
		else:
			_LOGGER.info("No more QR code to generate")
			page.save(filepath)
			break


#pylint: disable=C0103
if __name__ == "__main__":
	logging.basicConfig()
	_LOGGER.setLevel(logging.DEBUG)

	items = ("D1", "OC99")
	qr_codes = [QRCode(size=28, padding=4).create_qr_code_image("https://gear.jellyfish.org/%s" % i, text="%s" % i) for i in items]
	page = Page() #sizes=(500, 500)
	for qr_code in qr_codes:
		page.add_image(qr_code)
	page.save('qrcode.png')
