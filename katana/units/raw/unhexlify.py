from katana.unit import BaseUnit
from collections import Counter
import sys
from io import StringIO
import argparse
from pwn import *
import subprocess
from katana.units import raw
from katana import utilities
import os
from katana.units import NotApplicable
import binascii
import traceback
import magic
from katana import units

HEX_PATTERN = rb'((0x)?[a-f0-9]{4,})'
HEX_REGEX = re.compile(HEX_PATTERN, re.MULTILINE | re.DOTALL | re.IGNORECASE)

class Unit(BaseUnit):

	PRIORITY = 25

	def __init__(self, katana, target):
		super(Unit, self).__init__(katana, target)

		# We don't need to operate on files
		if not self.target.is_printable or self.target.is_file or self.target.is_english:
			raise NotApplicable("is a file")

		# Check if there is hex in it, remove spaces and commas
		self.raw_target = self.target.raw.replace(b' ',b'').replace(b',',b'')
		self.matches = HEX_REGEX.findall(self.raw_target)

		if self.matches is None or self.matches == []:
			raise NotApplicable("no hex found")

	def evaluate(self, katana, case):
		results = []
		for match,_ in self.matches:
			if match.lower().startswith(b'0x'):
				match = match[2:]
			if len(match) < 4:
				continue
			try:
				result = binascii.unhexlify(match)
				results.append(binascii.unhexlify(match))
			except binascii.Error as e:
				# We may have an "odd-length string" in the way...
				# try to clean up the ends to see if we get anything
				results.append(binascii.unhexlify(match[0:-1]))

				results.append(binascii.unhexlify(match[1:]))

		katana.locate_flags(self, results)
				
		for result in results:
			if result:
				# We want to know about this if it is printable!
				if utilities.isprintable(result):
					katana.recurse(self, result)
					katana.add_results(self, result)

				# if it's not printable, we might only want it if it is a file...
				else:
					magic_info = magic.from_buffer(result)
					if utilities.is_good_magic(magic_info):
						
						katana.add_results(self, result)

						filename, handle = katana.create_artifact(self, "decoded", mode='wb', create=True)
						handle.write(result)
						handle.close()
						katana.recurse(self, filename)