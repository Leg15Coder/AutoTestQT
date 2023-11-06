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
        :return: None
        """
        for elem in args:
            elem.manager = self
            self.tests.append(elem)
        for name in kwargs:
            kwargs[name].manager = self
            self.named_windows[name] = kwargs[name]

    def __getitem__(self, key):
        return self.named_windows[key]


class ResultWidget(QMainWindow):
    """
        Окно, которое показывает результаты тестирования
    """
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/result.ui', self)
        self.setGeometry(500, 500, 500, 500)
        self.setWindowTitle("Результаты тестирования")
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))

    def reload(self, res: list):
        """
            Загружает данные тестирования в виджет
        :param res: Массив битов, определяющий правильность выполнения заданий
        :return: None
        """
        count, total = len(res), sum(res)
        self.lcdNumber.display(total)
        self.lcdNumber_2.display(count)
        self.progressBar.setValue(round(total * 100 / count))


class Widget(QMainWindow, QScrollArea):
    """
        Окно с тестом
    """
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()

        # Параметры окна
        self.setGeometry(500, 500, 500, 500)
        self.setWindowTitle("Проверочная работа")

        # Инициализация элементов интерфейса
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        self.widget = QWidget()
        self.main_label = QLabel(self)
        self.pushButton = QPushButton(self)

        # Форматирование отображения
        self.widget.setLayout(self.layout)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)
        self.setCentralWidget(self.scroll)

        # Настройки загаловка
        self.layout.addWidget(self.main_label)
        self.main_label.setText("test")
        self.main_label.move(100, 0)

        # Настройки кнопки
        self.pushButton.move(350, 45)
        self.layout.addWidget(self.pushButton)
        self.pushButton.setText("Завершить")
        self.pushButton.clicked.connect(self.finish)

        # Переменная для сохранения остальных элементов UI, добавляемых позже
        self.block = list()

    def make_radio_block(self, texts: list, k: int):
        """
            Создаёт тестовый вопрос с одним правильным вариантом ответа
        :param texts: Данные для составления вопроса
        :param k: коэффициент отступа
        :return: None
        """
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

    def make_checkbox_block(self, texts: list, k: int):
        """
            Создаёт тестовый вопрос с несколькими правильными вариантами ответа
        :param texts: Данные для составления вопроса
        :param k: коэффициент отступа
        :return: None
        """
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

    def make_text_block(self, texts: list, k: int):
        """
            Создаёт вопрос с открытым вводом ответа
        :param texts: Данные для составления вопроса
        :param k: коэффициент отступа
        :return: None
        """
        label = QLabel(self)
        self.layout.addWidget(label)
        label.setText(str(texts[0]))
        label.move(100, 50 + 250 * k)
        text_input = QTextEdit(self)
        self.layout.addWidget(text_input)
        text_input.move(100, 80 + 250 * k)
        self.block.append({'label': label, 'text': text_input})

    def add(self, task: str, data: list, corr: list, k: int):
        """
            По сырым данным формирует базу правильных ответов и подготавливает UI вопроса
        :param task: Тип задания
        :param data: Данные для составления вопросов
        :param corr: Данные для проверки ответов
        :param k: коэффициент отступа
        :return: None
        """
        if task in ('numsenter', 'textenter'):
            self.make_text_block(data, k)
        elif task == 'radios':
            self.make_radio_block(data, k)
        else:
            self.make_checkbox_block(data, k)
        self.block[-1]['corr'] = list(map(str, corr))

    def finish(self):
        """
            Завершает задание и отправдяет его на проверку
        :return: None
        """
        res = list()
        for elem in self.block:
            if 'text' in elem:
                answ = elem['text'].toPlainText()
                res.append(answ.strip() in elem['corr'])
            elif 'checkboxes' in elem:
                flag = False
                for i in range(5):
                    if elem['checkboxes'][i].checkState() != elem['corr'][i]:
                        flag = True
                        break
                res.append(not flag)
            elif 'radios' in elem:
                flag = False
                for i in range(5):
                    if elem['radios'][i].isChecked() != elem['corr'][i]:
                        flag = True
                        break
                res.append(not flag)
        result = ResultWidget(self.manager)
        result.reload(res)
        manager.add_window(result)
        self.manager.main.toggle_window(result)
        self.hide()
        del self


class StartWidget(QMainWindow):
    """
        Окно для выбора темы и начала проверочной работы
    """
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/start.ui', self)
        self.lesson = 'СС'
        db = sql.connect("AutoTestQT/db.sqlite")
        self.cur = db.cursor()
        self.setupUi()

    def setupUi(self):
        """
            Связывает БД и UI
        :return: None
        """
        lessons = list(set(fetch("SELECT lesson FROM lessons", self.cur)))
        self.setWindowTitle("Создать вариант")
        self.comboBox.addItems(lessons)
        self.comboBox.currentTextChanged.connect(self.text_changed)
        self.pushButton.clicked.connect(self.create_test)
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager.main))

    def text_changed(self, s):
        self.lesson = s

    def create_test(self):
        """
            Создаёт проверочную работу
        :return: Bool (успешно ли создана работа)
        """
        num_of_tasks = self.spinBox.value()
        if self.lesson is not None:
            lesson = self.lesson
        else:
            return False
        tasks = fetch(f"SELECT task FROM lessons WHERE lesson='{lesson}'", self.cur)
        ids = fetch(f"SELECT id FROM lessons WHERE lesson='{lesson}'", self.cur)
        tasks = list(zip(ids, tasks))
        widget = Widget()
        self.manager.add_window(widget)
        for _ in range(num_of_tasks):
            task = choice(tasks)
            type_of_task = fetch(f"SELECT type FROM lessons WHERE id={task[0]}", self.cur)[0]
            answers = fetch(f"SELECT answer FROM answers WHERE task='{task[0]}'", self.cur)
            correctnesses = fetch(f"SELECT correctness FROM answers WHERE task='{task[0]}'", self.cur)
            answers = list(zip(answers, correctnesses))
            data, bools = [task[1]], list()
            if type_of_task in ('numsenter', 'textenter'):
                bools += fetch(f"SELECT answer FROM answers WHERE task='{task[0]}' and correctness!=0", self.cur)
            else:
                while len(data) < 6:
                    elem = choice(answers)
                    if elem[0] not in data:
                        data.append(elem[0])
                        bools.append(bool(elem[1]))
                while True:
                    if type_of_task == 'radios' and sum(bools) == 1 or any(bools) and type_of_task == 'checkboxes':
                        break
                    elem = choice(answers)
                    if elem[0] not in data:
                        data[-1] = elem[0]
                        bools[-1] = bool(elem[1])
            widget.add(type_of_task, data, bools, _)
        widget.show()
        return True


class SettingWidget(QMainWindow):
    """
        Окно общих настроек
    """
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
    """
        Окно для добавления заданий в БД
    """
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/add_task.ui', self)
        self.type = 'radios'
        self.setupUi()

    def setupUi(self):
        """
            Связывает БД и UI
        :return: None
        """
        elements = ['radios', 'checkboxes', 'numsenter', 'textenter']
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager['setting']))
        self.pushButton.clicked.connect(self.create_task)
        self.comboBox.addItems(elements)
        self.comboBox.currentTextChanged.connect(self.text_changed)

    def text_changed(self, s):
        self.type = s

    def create_task(self):
        """
            Добавляет задание в БД и выводит его ID а экран
        :return: None
        """
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
    """
        Окно для добавления возможных ответов к заданию по его ID в БД
    """
    def __init__(self, manage=None):
        self.manager = manage
        super().__init__()
        uic.loadUi('AutoTestQT/ui/add_answer.ui', self)
        self.db = sql.connect("AutoTestQT/db.sqlite")
        self.cur = self.db.cursor()
        self.id = 0
        self.setupUi()

    def setupUi(self):
        """
            Связывает БД и UI
        :return: None
        """
        self.back_button.clicked.connect(lambda: self.manager.main.toggle_window(self.manager['setting']))
        self.confirmButton.clicked.connect(self.create_answer)
        self.pushButton.clicked.connect(self.find_task)

    def find_task(self):
        """
            Ищет задание в БД по ID
        :return: str (текст задания)
        """
        ids = self.lineEdit.text()
        task = fetch(f"SELECT task FROM lessons WHERE id={ids}", self.cur)
        if not task:
            self.label.setText("Ничего не найдено")
        else:
            self.label.setText(task[0])
            self.id = ids
        return task[0] if not task else str()

    def create_answer(self):
        """
            Записывает возможный ответ к заданию в БД
        :return: None
        """
        text = self.textEdit.toPlainText()
        corr = self.checkBox.checkState()
        self.cur.execute("INSERT INTO answers(task, answer, correctness) VALUES (?, ?, ?)", (self.id, text, corr))
        self.db.commit()


class MainWidget(QMainWindow):
    """
        Окно с основным меню, стартовое окно и объект для хранения информации о текущем отображении на экране
    """
    def __init__(self, manage=None):
        self.manager = manage
        self.showing_window = self
        super().__init__()
        uic.loadUi('AutoTestQT/ui/menu.ui', self)
        self.setupUi()

    def setupUi(self):
        """
            Связывает БД и UI
        :return: None
        """
        self.exit_button.clicked.connect(QCoreApplication.quit)
        self.start_buttob.clicked.connect(lambda: self.toggle_window(self.manager['start']))
        self.settings_button.clicked.connect(lambda: self.toggle_window(self.manager['setting']))

    def toggle_window(self, window=None):
        """
            Переключает окна
        :param window: Окно, которое нужно отобразить
        :return: None
        """
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
