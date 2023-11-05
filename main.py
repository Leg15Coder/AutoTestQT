from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from AutoTestQT.load.funcs import *
import sqlite3 as sql
from random import *
import sys


class WindowsManager(object):
    """
        Менеджер окон - объект для быстрого переключения и взаимодействия между окнами в приложении
    """
    def __init__(self, main: QMainWindow):
        self.main = main
        self.main.manager = self
        self.tests = list()
        self.named_windows = dict()

    def add_window(self, *args, **kwargs):
        """
            Добавляет окна в иенеджер
        :param args:
        :param kwargs:
        :return:
        """
        for elem in args:
            elem.manager = self
            self.tests.append(elem)
        for name in kwargs:
            kwargs[name].manager = self
            self.named_windows[name] = kwargs[name]

    def __getitem__(self, key):
        return self.named_windows[key]


class Widget(QMainWindow, QScrollArea):
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        self.setupUi()

    def setupUi(self):
        try:
            self.setGeometry(500, 500, 500, 500)
            self.setWindowTitle("test")

            self.layout = QVBoxLayout(self)
            self.scroll = QScrollArea(self)
            self.widget = QWidget()

            self.widget.setLayout(self.layout)

            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll.setWidgetResizable(True)
            self.scroll.setWidget(self.widget)
            self.setCentralWidget(self.scroll)

            self.main_label = QLabel(self)
            self.layout.addWidget(self.main_label)
            self.main_label.setText("test")
            self.main_label.move(100, 0)
            self.block = list()
        except Exception as ex:
            print(ex)

    def make_radio_block(self, texts: list, k: int):
        group = QButtonGroup(self)
        label = QLabel(self)
        self.layout.addWidget(label)
        label.setText(str(texts[0]))
        label.move(100, 50 + 250 * k)
        radios = list()
        for n in range(5):
            radios.append(QRadioButton(self))
            self.layout.addWidget(radios[n])
            group.addButton(radios[n])
            radios[n].setText(str(texts[n + 1]))
            radios[n].move(100, 50 + 250 * k + 25 * (n + 1))
        self.block.append({'group': group, 'label': label, 'radios': radios})

    def make_checkbox_block(self):
        group = QButtonGroup(self)
        label = QLabel(self)
        self.layout.addWidget(label)
        label.setText(str(texts[0]))
        label.move(100, 50 + 250 * k)
        checkboxes = list()
        for n in range(5):
            checkboxes.append(QCheckBox(self))
            self.layout.addWidget(checkboxes[n])
            group.addButton(checkboxes[n])
            checkboxes[n].setText(str(texts[n + 1]))
            checkboxes[n].move(100, 50 + 250 * k + 25 * (n + 1))
        self.block.append({'group': group, 'label': label, 'checkboxes': checkboxes})


class StartWidget(QMainWindow):
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/start.ui', self)
        self.lesson = 'turtle'
        db = sql.connect("AutoTestQT/db.sqlite")
        self.cur = db.cursor()
        self.setupUi()

    def setupUi(self):
        lessons = list(set(fetch("SELECT lesson FROM lessons", self.cur)))
        self.comboBox.addItems(lessons)
        self.comboBox.currentTextChanged.connect(self.text_changed)
        self.pushButton.clicked.connect(self.create_test)
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))

    def text_changed(self, s):
        self.lesson = s

    def create_test(self):
        num_of_tasks = self.spinBox.value()
        if self.lesson is not None:
            lesson = self.lesson
        else:
            return False
        tasks = fetch(f"SELECT task FROM lessons WHERE lesson='{lesson}'", self.cur)
        ids = fetch(f"SELECT id FROM lessons WHERE lesson='{lesson}'", self.cur)
        data = list(zip(ids, tasks))
        widget = Widget()
        self.manager.add_window(widget)
        for _ in range(num_of_tasks):
            task = choice(data)
            answers = fetch(f"SELECT answer, correctness FROM answers WHERE task='{task[0]}'", self.cur)
            radios = [task[1]]
            for __ in range(5):
                radios.append(choice(answers))
            widget.make_radio_block(radios, _)
        widget.show()


class SettingWidget(QMainWindow):
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/setting.ui', self)
        self.setupUi()

    def setupUi(self):
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))
        self.addTask.clicked.connect(lambda: self.manager.main.toggle_window(self.manager["add_task"]))
        self.addAnswer.clicked.connect(lambda: self.manager.main.toggle_window(self.manager["add_answer"]))


class AddTaskWidget(QMainWindow):
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/add_task.ui', self)
        self.type = 'textenter'
        self.setupUi()

    def setupUi(self):
        elements = ['radios', 'checkboxes', 'numsenter', 'textenter']
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))
        self.pushButton.clicked.connect(self.create_task)
        self.comboBox.addItems(elements)
        self.comboBox.currentTextChanged.connect(self.text_changed)

    def text_changed(self, s):
        self.type = s

    def create_task(self):
        db = sql.connect("AutoTestQT/db.sqlite")
        cur = db.cursor()
        lesson = str(self.lineEdit.text())
        task = str(self.textEdit.toPlainText())
        ids = max(fetch("SELECT id FROM lessons", cur)) + 1
        cur.execute(f'INSERT INTO lessons (lesson, task, type, id) VALUES (?, ?, ?, ?)', (lesson, task, self.type, ids))
        self.lcd.display(ids)
        db.commit()
        db.close()


class AddAnswerWidget(QMainWindow):
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/add_answer.ui', self)
        self.db = sql.connect("AutoTestQT/db.sqlite")
        self.cur = self.db.cursor()
        self.id = 0
        self.setupUi()

    def setupUi(self):
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))
        self.confirmButton.clicked.connect(self.create_answer)
        self.pushButton.clicked.connect(self.find_task)

    def find_task(self):
        ids = self.lineEdit.text()
        task = fetch(f"SELECT task FROM lessons WHERE id={ids}", self.cur)
        if not task:
            self.label.setText("Ничего не найдено")
        else:
            self.label.setText(task[0])
            self.id = ids

    def create_answer(self):
        text = self.textEdit.toPlainText()
        corr = self.checkBox.checkState()
        self.cur.execute("INSERT INTO answers(task, answer, correctness) VALUES (?, ?, ?)", (self.id, text, corr))
        self.db.commit()


class MainWidget(QMainWindow):
    def __init__(self, manage=None):
        self.manager = manage
        self.showing_window = self
        super().__init__()
        uic.loadUi('AutoTestQT/ui/menu.ui', self)
        self.setupUi()

    def setupUi(self):
        self.exit_button.clicked.connect(QCoreApplication.quit)
        self.start_buttob.clicked.connect(lambda: self.toggle_window(self.manager['start']))
        self.settings_button.clicked.connect(lambda: self.toggle_window(self.manager['setting']))

    def toggle_window(self, window=None):
        if window is None:
            self.show()
        else:
            if self.showing_window.isVisible():
                self.showing_window.hide()
                self.showing_window = window
                self.showing_window.show()
            else:
                self.show()


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        manager = WindowsManager(MainWidget())
        manager.add_window(
            start=StartWidget(manager), setting=SettingWidget(manager), add_task=AddTaskWidget(manager),
            add_answer=AddAnswerWidget(manager)
        )
        ex = manager.main
        ex.show()
        sys.exit(app.exec_())
    except Exception as ex:
        print(ex)
