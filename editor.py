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
from anki.hooks import addHook
from aqt import mw
from aqt.qt import *
from .highlight import *
from .reading import add_furigana

def onContextMenu(ewv, m):
    def onAddFurigana():
        note = ewv.editor.note
        text = note.fields[ewv.editor.currentField]
        text = add_furigana(text)
        note.fields[ewv.editor.currentField] = text
        mw.progress.timer(100, ewv.editor.loadNoteKeepingFocus, False)
    def onTakeFromQueue():
        text = queue.lines[i]
        ewv.editor.doPaste(text, internal=False)
        j = queue.lines.index('***') if '***' in queue.lines else 0
        if '***' in queue.lines:
            queue.lines.remove('***')
        queue.lines.insert(j+1, '***')
        queue.write()
    a = m.addAction(_("Add Furigana"))
    a.triggered.connect(onAddFurigana)
    queue = TextCollection('queue.txt', None)
    i = queue.lines.index('***') + 1 if '***' in queue.lines else 0
    remaining = len(queue.lines) - i
    note = ewv.editor.note
    currentField = ewv.editor.currentField
    if currentField is not None:
        text = note.fields[currentField]
        if remaining > 0 and currentField == 0 and text == '':
            a = m.addAction(_("Take from Queue (%d remaining)") % remaining)
            a.triggered.connect(onTakeFromQueue)

addHook('EditorWebView.contextMenuEvent', onContextMenu)
