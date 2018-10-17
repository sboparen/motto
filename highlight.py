#!/usr/bin/env python3
"""
Highlight presumed unknown words in Japanese text.
"""
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
if __name__ == '__main__': # HACK
    from reading import mecab_dict
else:
    from .reading import mecab_dict
import argparse
import os
import subprocess
import unicodedata

def cleanup_card(s):
    s = s.replace('<br>', '')
    s = s.replace(' ', '')
    while '[' in s and ']' in s:
        s = s[:s.index('[')] + s[s.index(']')+1:]
    return s

def has_japanese_text(s):
    for ch in s:
        name = unicodedata.name(ch, 'nope')
        if 'KATAKANA' in name:
            return True
        if 'HIRAGANA' in name:
            return True
        if 'CJK' in name:
            return True
    return False

class TextCollection():
    def __init__(self, name, update_callback,
                 split_on='\n\n', postprocess=None):
        self.update_callback = update_callback
        self.split_on = split_on
        self.postprocess = postprocess
        root = os.path.join(os.path.dirname(__file__), 'user_files')
        if not os.path.isdir(root):
            os.mkdir(root)
        self.path = os.path.join(root, name)
        self.read()
    def read(self):
        if not os.path.exists(self.path):
            self.lines = []
            return
        with open(self.path) as f:
            self.lines = f.read().strip().split(self.split_on)
            self.lines = [line.rstrip() for line in self.lines]
            if self.postprocess is not None:
                self.lines = [self.postprocess(line) for line in self.lines]
    def write(self):
        with open(self.path + '.tmp', 'w') as f:
            data = self.split_on.join(self.lines) + '\n'
            f.write(data)
        os.rename(self.path + '.tmp', self.path)
    def add(self, line):
        if line in self.lines:
            return
        self.lines.append(line)
        self.write()
        self.update_callback()
    def remove(self, line):
        if line not in self.lines:
            return
        self.lines.remove(line)
        self.write()
        self.update_callback()

class KnownDatabase():
    def __init__(self):
        self.subs = []
        self.reload()
    def reload(self):
        self.anki = TextCollection('anki.txt', self.update_known,
            split_on='\n', postprocess=cleanup_card)
        self.marked = TextCollection('marked.txt', self.update_known)
        self.queue = TextCollection('queue.txt', self.update_known)
        self.process_subtitles(self.subs)
    def process_subtitles(self, subs):
        self.subs = subs
        lines = list(self.subs)
        lines += self.anki.lines
        lines += self.marked.lines
        lines += self.queue.lines
        self.jd = mecab_dict(lines)
        self.update_known()
    def update_known(self):
        self.known = set()
        for line in self.anki.lines + self.queue.lines:
            for seg, base, reading in self.jd[line]:
                if not has_japanese_text(base):
                    continue
                self.known.add(base)
        trimmed = TextCollection('marked.trimmed.txt', None)
        trimmed.lines = []
        for line in self.marked.lines:
            segments = self.jd[line]
            added = False
            for seg, base, reading in segments:
                if not has_japanese_text(base):
                    continue
                if base not in self.known:
                    self.known.add(base)
                    added = True
            if added:
                trimmed.lines.append(line)
        trimmed.write()
    def highlight(self, text, fmt, stats=False):
        markup = u''
        r, t = 0, 0
        for seg, base, reading in self.jd[text]:
            if has_japanese_text(seg) and base not in self.known:
                markup += fmt % seg
                r += len(seg)
            else:
                markup += seg
            t += len(seg)
        if stats:
            return r, t
        return markup
    def num_in_queue(self):
        i = self.queue.lines.index('***') + 1 \
            if '***' in self.queue.lines else 0
        return len(self.queue.lines) - i

def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', nargs='+')
    args = parser.parse_args()
    for path in args.file:
        db = KnownDatabase()
        with open(path) as f:
            subs = f.read().strip().split('\n\n')
        db.process_subtitles(subs)
        pre = subprocess.check_output(['tput', 'setaf', '1']).decode('utf8')
        post = subprocess.check_output(['tput', 'sgr0']).decode('utf8')
        if len(args.file) == 1:
            for line in subs:
                print(db.highlight(line, pre + '%s' + post))
        else:
            red, total = 0, 0
            for line in subs:
                r, t = db.highlight(line, '%s', stats=True)
                red += r
                total += t
            print('%3.0f%% %s' % (100 - (100.0 * red / max(total, 1)), path))

if __name__ == '__main__':
    main()
