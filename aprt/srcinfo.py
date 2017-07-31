# Copyright 2017 Delft Robotics BV
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import os.path

from .package import Package

class SrcInfo:
	"""
	A SRCINFO data container.
	srcinfo.pkgbase is a dict holding the pkgbase data.
	srcinfo.pkgnames is a list of dicts holding data per pkgname.
	"""

	def __init__(self, directory):
		self.pkgbase   = None;
		self.pkgnames  = [];
		self.directory = directory

	def packages(self):
		"""
		Get a list of packages described by this SRCINFO.
		The returned  packages are generated by merging pkgbase data with each pkgname.
		"""
		for pkgname in self.pkgnames:
			package = Package(pkgname.name)
			for key, values in self.pkgbase.data.items():
				package.add_values(key, values)
			for key, values in pkgname.data.items():
				package.add_values(key, values)
			yield package

	@classmethod
	def parse(cls, blob, directory):
		"""
		Parse a blob of text as SRCINFO file.
		The results are returned as a SrcInfo object,
		"""
		result  = cls(directory)
		current = None

		for line in blob.splitlines():
			if len(line) == 0 or line[0] == '#': continue

			key, value = line.split('=', 1)
			key        = key.strip();
			value      = value.strip();

			if key == 'pkgbase':
				current = Package(value);
				result.pkgbase = current

			elif key == 'pkgname':
				current = Package(value);
				result.pkgnames.append(current)

			elif current == None:
				raise ValueError("SRCINFO value encountered but no pkgbase or pkgname has been started.")

			else:
				current.add_value(key, value)

		return result

	@classmethod
	def parse_file(cls, filename):
		with open(filename, 'r') as file:
			return cls.parse(file.read(), os.path.dirname(filename))

	@classmethod
	def parse_packages(cls, blob, directory):
		return cls.parse(blob, directory).packages()

	@classmethod
	def parse_packages_file(cls, filename):
		return cls.parse_file(filename).packages()

	@classmethod
	def __find_srcinfo_dirs(cls, root):
		children = os.listdir(root)

		for child in children:
			path = os.path.join(root, child)
			if child == '.SRCINFO':
				yield root
			if os.path.isdir(path):
				yield from cls.__find_srcinfo_dirs(path)

	@classmethod
	def load_db(cls, root):
		directories = cls.__find_srcinfo_dirs(root)
		result      = {}
		for directory in directories:
			srcinfo           = cls.parse_file(os.path.join(directory, '.SRCINFO'))
			srcinfo.directory = directory
			result[directory] = srcinfo
		return result

	@classmethod
	def index_by_pkgname(cls, srcinfo_db):
		result = {}
		for srcinfo in srcinfo_db.values():
			for package in srcinfo.packages():
				if package.name in result:
					raise RuntimeError('Multiple .SRCINFO files build the same package: {} is built by {} and {}.'.format(package, srcinfo.directory, result[package.name].directory))
				result[package.name] = srcinfo
		return result

	@classmethod
	def load_db_indexed_by_pkgname(cls, root):
		return cls.index_by_pkgname(cls.load_db(root))
