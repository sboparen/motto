# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Modified by Simon Parent
#
# Automatic reading generation with kakasi and mecab.
#

import sys, os, platform, re, subprocess
try:
    from anki.utils import isWin, isMac
except ImportError:
    isWin = False
    isMac = False

kakasiArgs = ["-isjis", "-osjis", "-u", "-JH", "-KH"]
mecabArgs = ['--node-format=%m[%f[7]][%f[6]] ', '--eos-format=\n',
            '--unk-format=%m[][%m] ']

supportDir = os.path.dirname(__file__)

if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    try:
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
    si = None

# Mecab
##########################################################################

def mungeForPlatform(popen):
    if isWin:
        popen = [os.path.normpath(x) for x in popen]
        popen[0] += ".exe"
    elif not isMac:
        popen[0] += ".lin"
    return popen

class MecabController(object):

    def __init__(self):
        self.mecab = None

    def setup(self):
        self.mecabCmd = mungeForPlatform(
            [os.path.join(supportDir, "mecab")] + mecabArgs + [
                '-d', supportDir, '-r', os.path.join(supportDir,"mecabrc")])
        os.environ['DYLD_LIBRARY_PATH'] = supportDir
        os.environ['LD_LIBRARY_PATH'] = supportDir
        if not isWin:
            os.chmod(self.mecabCmd[0], 0o755)

    def ensureOpen(self):
        if not self.mecab:
            self.setup()
            try:
                self.mecab = subprocess.Popen(
                    self.mecabCmd, bufsize=-1, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    startupinfo=si)
            except OSError:
                raise Exception("Please ensure your Linux system has 64 bit binary support.")

    def run_mecab(self, expr):
        self.ensureOpen()
        self.mecab.stdin.write(expr.encode('euc-jp') + b'\n')
        self.mecab.stdin.flush()
        expr = self.mecab.stdout.readline().rstrip(b'\r\n').decode('euc-jp')
        ret = []
        for node in expr.split(" "):
            if not node:
                break
            (kanji, reading, root) = re.match("(.+)\[(.*)\]\[(.*)\]", node).groups()
            ret.append((kanji, reading, root))
        return ret

    def reading(self, expr):
        out = []
        for kanji, reading, root in self.run_mecab(expr):
            # hiragana, punctuation, not japanese, or lacking a reading
            if kanji == reading or not reading:
                out.append(kanji)
                continue
            # katakana
            if kanji == kakasi.reading(reading):
                out.append(kanji)
                continue
            # convert to hiragana
            reading = kakasi.reading(reading)
            # ended up the same
            if reading == kanji:
                out.append(kanji)
                continue
            # don't add readings of numbers
            if kanji in u"一二三四五六七八九十０１２３４５６７８９":
                out.append(kanji)
                continue
            # strip matching characters and beginning and end of reading and kanji
            # reading should always be at least as long as the kanji
            placeL = 0
            placeR = 0
            for i in range(1,len(kanji)):
                if kanji[-i] != reading[-i]:
                    break
                placeR = i
            for i in range(0,len(kanji)-1):
                if kanji[i] != reading[i]:
                    break
                placeL = i+1
            if placeL == 0:
                if placeR == 0:
                    out.append(" %s[%s]" % (kanji, reading))
                else:
                    out.append(" %s[%s]%s" % (
                        kanji[:-placeR], reading[:-placeR], reading[-placeR:]))
            else:
                if placeR == 0:
                    out.append("%s %s[%s]" % (
                        reading[:placeL], kanji[placeL:], reading[placeL:]))
                else:
                    out.append("%s %s[%s]%s" % (
                        reading[:placeL], kanji[placeL:-placeR],
                        reading[placeL:-placeR], reading[-placeR:]))
        fin = u""
        for c, s in enumerate(out):
            if c < len(out) - 1 and re.match("^[A-Za-z0-9]+$", out[c+1]):
                s += " "
            fin += s
        return fin.strip().replace("< br>", "<br>")

# Kakasi
##########################################################################

class KakasiController(object):

    def __init__(self):
        self.kakasi = None

    def setup(self):
        self.kakasiCmd = mungeForPlatform(
            [os.path.join(supportDir, "kakasi")] + kakasiArgs)
        os.environ['ITAIJIDICT'] = os.path.join(supportDir, "itaijidict")
        os.environ['KANWADICT'] = os.path.join(supportDir, "kanwadict")
        if not isWin:
            os.chmod(self.kakasiCmd[0], 0o755)

    def ensureOpen(self):
        if not self.kakasi:
            self.setup()
            try:
                self.kakasi = subprocess.Popen(
                    self.kakasiCmd, bufsize=-1, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    startupinfo=si)
            except OSError:
                raise Exception("Please install kakasi")

    def reading(self, expr):
        self.ensureOpen()
        self.kakasi.stdin.write(expr.encode("sjis", "ignore") + b'\n')
        self.kakasi.stdin.flush()
        res = self.kakasi.stdout.readline().rstrip(b'\r\n').decode("sjis")
        return res

# Init
##########################################################################

kakasi = KakasiController()
mecab = MecabController()

def fixup(line):
    ret, extra = '', ''
    for ch in line:
        n = ord(ch)
        replace = False
        if ord(ch) <= 0xff or ord(ch) == 0x3000:
            replace = True
        elif ch.encode('euc_jp', 'ignore').decode('euc_jp') != ch:
            replace = True
        if replace:
            ret += '\x01'
            extra += ch
        else:
            ret += ch
    return ret, extra

def add_furigana(text):
    text, extra = fixup(text)
    ret = mecab.reading(text)
    while '\x01' in ret:
        ret = ret.replace('\x01', extra[0], 1)
        extra = extra[1:]
    return ret

def mecab2(lines):
    lines = [fixup(line) for line in lines]
    chunks = [mecab.run_mecab(line) for line, extra in lines]
    assert len(chunks) == len(lines), (len(chunks), len(lines))
    ret = []
    for chunk, (original, extra) in zip(chunks, lines):
        cur = []
        check = ''
        for seg, reading, base in chunk:
            check += seg
            while '\x01' in seg:
                seg = seg.replace('\x01', extra[0], 1)
                base = base.replace('\x01', extra[0], 1)
                reading = reading.replace('\x01', extra[0], 1)
                extra = extra[1:]
            cur.append((seg, base, reading))
        if check != original:
            print
            print(repr(check))
            print(repr(original))
            assert False
        ret.append(cur)
        assert extra == '', repr(extra)
    return ret

def mecab_dict(lines):
    lines = [line for line in lines if line != '']
    results = mecab2(lines)
    assert len(lines) == len(results), (len(lines), len(results))
    ret = {}
    for k, v in zip(lines, results):
        if k in ret:
            assert ret[k] == v
        ret[k] = v
    ret[''] = []
    return ret
