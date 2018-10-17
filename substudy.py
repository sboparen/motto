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
from aqt.utils import getFile
from aqt.webview import AnkiWebView
from .highlight import *

def createMenu():
    a = QAction(mw)
    a.setText('Study Subtitle File...')
    mw.form.menuTools.addAction(a)
    a.triggered.connect(onStudy)

def onStudy():
    path = getFile(mw, 'Study Subtitle File',
        cb=None, key='study', filter='*.srt *.txt')
    if path is None:
        return
    with open(path) as f:
        subs = f.read().strip().split('\n\n')
    d = MainWindow(mw, path, subs)
    d.exec_()

def get_known_cards():
    ret = []
    ids = mw.col.findCards("-is:suspended")
    for cid in ids:
        note = mw.col.getCard(cid).note()
        if 'japanese' not in note.model()['name'].lower():
            continue
        expression = note.fields[0]
        ret.append(expression)
    return ret

class MainWindow(QDialog):
    def __init__(self, parent, path, subs):
        QDialog.__init__(self, parent)
        self.path = path
        self.subs = subs
        self.db = KnownDatabase()
        self.db.anki.lines = get_known_cards()
        self.db.anki.write()
        self.db.reload()
        self.db.process_subtitles(subs)
        area = QScrollArea()
        inner_widget = QWidget()
        inner_layout = QVBoxLayout()
        self.chunks = []
        for line in subs:
            chunk = TextChunk(self, line)
            self.chunks.append(chunk)
            inner_layout.addWidget(chunk)
        area.setWidget(inner_widget)
        area.setWidgetResizable(True)
        inner_widget.setLayout(inner_layout)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(area)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        layout.addWidget(bb)
        bb.rejected.connect(self.reject)
        self.setLayout(layout)
        self.resize(1000, 800) # TODO remember size
    def update_all_lines(self):
        for chunk in self.chunks:
            chunk.update_highlighting()

class TextChunk(QLabel):
    def __init__(self, main_window, line):
        QLabel.__init__(self)
        self.main_window = main_window
        self.line = line
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mark_action = QAction('Toggle Mark', self)
        self.mark_action.triggered.connect(self.toggle_mark)
        self.addAction(self.mark_action)
        self.queue_action = QAction('Toggle Queue', self)
        self.queue_action.triggered.connect(self.toggle_queue)
        self.addAction(self.queue_action)
        play_action = QAction('Play From Here', self)
        play_action.triggered.connect(self.play_from_here)
        self.addAction(play_action)
        self.update_highlighting()
    def update_highlighting(self):
        markup = self.main_window.db.highlight(
            self.line, '<font color="red">%s</font>')
        markup = markup.replace('\n', '<br>')
        markup = '<font size="24">%s</font>' % markup
        self.setText(markup)
        if self.line not in self.main_window.db.marked.lines:
            self.mark_action.setText('Mark as Known')
        else:
            self.mark_action.setText('Unmark as Known')
        in_queue = ' (%d in queue)' % self.main_window.db.num_in_queue()
        if self.line not in self.main_window.db.queue.lines:
            self.queue_action.setText('Add to Queue' + in_queue)
        else:
            self.queue_action.setText('Remove from Queue' + in_queue)
    def toggle_mark(self):
        if self.line not in self.main_window.db.marked.lines:
            self.main_window.db.marked.add(self.line)
        else:
            self.main_window.db.marked.remove(self.line)
        self.main_window.update_all_lines()
    def toggle_queue(self):
        if self.line not in self.main_window.db.queue.lines:
            self.main_window.db.queue.add(self.line)
        else:
            self.main_window.db.queue.remove(self.line)
        self.main_window.update_all_lines()
    def play_from_here(self):
        mkv_path = os.path.splitext(self.main_window.path)[0] + '.mkv'
        start = self.line.split('\n')[1].split(' --> ')[0].replace(',', '.')
        cmd = ['mpv', '--start=%s' % start, '--', mkv_path]
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '' # HACK
        subprocess.call(cmd, env=env)

createMenu()
