# Copyright (c) 2018 Simon Parent
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from reading import mecab_dict, add_furigana
import unittest

class TestUnicode(unittest.TestCase):

    def test_mecab(self):
        for n in range(0x12345):
            if n == 1:
                continue # TODO
            ch = chr(n)
            d = mecab_dict([ch])
            if '' in d:
                self.assertEqual(d[''], [])
                del d['']
            self.assertEqual(list(d.keys()), [ch])
            self.assertEqual([seg for seg, base, reading in d[ch]], [ch])

    def test_add_furigana(self):
        for n in range(0x12345):
            if n == 1:
                continue # TODO
            ch = chr(n)
            s = add_furigana(ch)
            if '[' in s and ']' in s:
                s = s[:s.index('[')] + s[s.index(']')+1:]
            self.assertEqual(s, ch)
