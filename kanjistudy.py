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
from aqt import mw
from aqt.qt import *
from aqt.utils import getFile, restoreGeom, saveGeom
from aqt.webview import AnkiWebView
from .highlight import *
import sqlite3

def createMenu():
    a = QAction(mw)
    a.setText('Compare To Kanji Study Backup File...')
    mw.form.menuTools.addAction(a)
    a.triggered.connect(onCompare)

def onCompare():
    path = getFile(mw, 'Compare To Kanji Study Backup File', cb=None,
        key='kanjistudy', filter='*.ksdata')
    if path is None:
        return
    mw.progress.start(immediate=True)
    rep = compare(path)
    d = QDialog(mw)
    v = QVBoxLayout()
    v.setContentsMargins(0, 0, 0, 0)
    w = AnkiWebView()
    v.addWidget(w)
    w.stdHtml(rep)
    bb = QDialogButtonBox(QDialogButtonBox.Close)
    v.addWidget(bb)
    bb.rejected.connect(d.reject)
    d.setLayout(v)
    d.resize(500, 400)
    restoreGeom(d, "kanjistudy")
    mw.progress.finish()
    d.exec_()
    saveGeom(d, "kanjistudy")

def ksdata(path):
    ret = {}
    with sqlite3.connect(path) as conn:
        c = conn.cursor()
        c.execute('''
select kanji_code, study_rating from user_kanji_info where is_radical = 0;
''')
        for row in c.fetchall():
            kanji, study_rating = row
            kanji = chr(kanji)
            assert kanji not in ret
            ret[kanji] = study_rating
        return ret

def compare(path):
    ret = ''
    known = set(''.join(get_known_cards()))
    known_plus_suspended = set(''.join(get_known_cards(query='')))
    kanji = ksdata(path)
    for r, name in [(0, 'New'), (1, 'Seen')]:
        ret += '<h1>%s kanji on a reading flashcard</h1><p>' % name
        for ch in known:
            if 'CJK' not in unicodedata.name(ch, 'nope'):
                continue
            rating = 0
            if ch in kanji:
                rating = kanji[ch]
            if rating == r:
                ret += ch
        ret += '</p>'
    ret += '<h1>Familiar/Known kanji not on an active reading flashcard</h1><p>'
    for ch, rating in kanji.items():
        if rating >= 2 and ch not in known:
            if ch in known_plus_suspended:
                ret += '<font color="red">%s</font>' % ch
            else:
                ret += ch
    ret += '</p>'
    return ret

def get_known_cards(query='-is:suspended'):
    ret = []
    ids = mw.col.findCards(query)
    for cid in sorted(ids):
        note = mw.col.getCard(cid).note()
        if 'japanese' not in note.model()['name'].lower():
            continue
        expression = note.fields[0]
        ret.append(expression)
    return ret

createMenu()
