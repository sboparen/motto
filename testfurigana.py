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
from reading import add_furigana
import unittest

class TestFurigana(unittest.TestCase):

    def add_furigana(self, text):
        ret = add_furigana(text)
        # TODO self.assertEqual(add_furigana(ret), ret)
        return ret

    def test_scripts(self):
        self.assertEqual(self.add_furigana('ひらがな'), 'ひらがな')
        self.assertEqual(self.add_furigana('カタカナ'), 'カタカナ')
        self.assertEqual(self.add_furigana('漢字'), '漢字[かんじ]')
        self.assertEqual(self.add_furigana('Romaji'), 'Romaji')
        self.assertEqual(self.add_furigana('①②③'), '①②③')
        self.assertEqual(self.add_furigana('<div>&nbsp;'), '<div>&nbsp;')
