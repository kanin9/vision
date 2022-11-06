import sys
import threading
import requests
import pyqtgraph as pg
import pyqtgraph.functions as fn
import pyqtgraph.parametertree as ptree
#from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtChart import QChart, QStackedBarSeries, QChartView, QBarSet, QBarCategoryAxis
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QGridLayout, QHBoxLayout, QToolBar, \
    QMainWindow, QAction, QInputDialog, QMessageBox
from mss import mss, tools

sct = mss()


def capture(bar: QBarSet, surprise, happiness, neutral, angry, sad, disgust, ctrl):
    bounding_box = {'top': 0, 'left': 0, 'width': 1920, 'height': 1080}
    data = {
        'surprise': [],
        'happy': [],
        'neutral': [],
        'angry': [],
        'sad': [],
        'disgust': []
    }
    while True:
        sct_img = sct.grab(bounding_box)

        files = {'media': tools.to_png(sct_img.rgb, sct_img.size)}
        # headers = {'Bypass-Tunnel-Reminder': 'True'}
        r = requests.post(url=ctrl['tunnelURL'] + "/process", files=files)

        print(r.content)
        response = r.json()
        emotions = ['surprise', 'happy', 'neutral', 'angry', 'sad', 'disgust']

        sample = response['sample']

        idx = 0
        for emotion in emotions:
            value = 0.0
            if emotion in response['emotions']:
                value = round(response['emotions'][emotion]['score'] / sample, 2)
                # print(emotion, response['emotions'][emotion]['score'])
            bar.replace(idx, value)
            data[emotion].append(value)
            idx += 1

        happiness.setData(data['happy'])
        surprise.setData(data['surprise'])
        neutral.setData(data['neutral'])
        angry.setData(data['angry'])
        sad.setData(data['sad'])
        disgust.setData(data['disgust'])

        if ctrl['break']:
            return


class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.width = 480
        self.height = 270
        # self.show()


class MainWindow(QMainWindow):
    def setupUI(self):

        self.button.move(70, 300)
        self.button.setFixedSize(140, 50)
        self.button.clicked.connect(self.beginCapture)
        self.bar.append([0.0, 0.1, 0.2, 0.4, 0.6, 1.0])

        self.series.append(self.bar)
        self.series.setLabelsVisible(True)

        categories = ['Удивление', 'Счастье', 'Нейтрал', 'Злость', 'Грусть', 'Отвращение']
        self.axis.append(categories)

        self.chart.addSeries(self.series)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.createDefaultAxes()
        self.chart.setAxisX(self.axis)

        # self.layout.setContentsMargins(300, 0, 0, 0)
        self.chartview.setFixedSize(500, 500)

        # self.layout.addWidget(self.chartview)

        # self.chartview.move(200, 200)

        self.chartview.setChart(self.chart)
        self.show()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vision")
        self.setWindowIcon(QIcon("icon.ico"))
        self.width = 1280
        self.height = 720
        # self.main_widget = QWidget(self)
        # self.main_widget.setFocus()
        # self.layout = QHBoxLayout()
        # self.setLayout(self.layout)
        self.ctrl = {'break': True, 'tunnelURL': 'http://localhost:4444'}

        self.resize(1280, 720)
        #self.setFixedSize(self.width, self.height)
        self.button = QPushButton('Начать запись', self)

        self.central = QWidget()

        self.setCentralWidget(self.central)

        self.chart = QChart()
        self.bar = QBarSet('Аудитория')
        self.axis = QBarCategoryAxis()
        self.series = QStackedBarSeries(self.chart)
        self.chartview = QChartView(self.chart)

        self.centralLayout = QHBoxLayout()
        # self.central.setFixedSize(300, 300)
        self.central.setLayout(self.centralLayout)
        #self.centralLayout.addWidget(self.button)
        self.button.setParent(self.central)
        self.centralLayout.addWidget(self.button)
        self.centralLayout.addWidget(self.chartview)

        self.centralLayout.setContentsMargins(20, 0, 0, 0)

        self.internal = QWidget()
        self.internal.setFixedSize(480, 480)
        self.internalLayout = QHBoxLayout()
        self.internal.setLayout(self.internalLayout)
        self.centralLayout.addWidget(self.internal)
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.addLegend()

        self.happiness = self.graphWidget.plot(pen='y', name='Счастье')

        self.neutral = self.graphWidget.plot(pen=(255, 192, 203), name='Нейтрал')
        self.disgust = self.graphWidget.plot(pen='g', name='Отвращение')
        self.sad = self.graphWidget.plot(pen='b', name='Грусть')
        self.surprise = self.graphWidget.plot(pen=(255, 165, 0), name='Удивление')
        self.angry = self.graphWidget.plot(pen='r', name='Злость')

        # self.graphWidget.plot(pen=(0,255,0))
        self.internalLayout.addWidget(self.graphWidget)

        self.toolbar = QToolBar("My main toolbar")
        self.toolbar.setMovable(False)

        font = QFont('Cascadia Code')
        font.setPixelSize(18)

        self.addToolBar(self.toolbar)
        self.about = QAction("О программе", self)
        self.about.setFont(font)
        self.fileAction = QAction("Файл", self)
        self.fileAction.triggered.connect(self.configOpen)
        self.configWindow = ConfigWindow()

        self.fileAction.setFont(font)
        # .triggered.connect(self.onMyToolBarButtonClick)
        self.toolbar.addAction(self.fileAction)
        self.toolbar.addAction(self.about)

        # self.layout.addWidget(toolbar)
        # self.addToolBar(toolbar)

        self.setupUI()

    def configOpen(self):
        dialog = QInputDialog()
        dialog.setWindowFlags(dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        text, ok = dialog.getText(self, 'Конфиг', 'Адрес тунеля')
        if ok:
            self.ctrl['tunnelURL'] = str(text)

    def closeEvent(self, event):
        self.ctrl['break'] = True

    def beginCapture(self):
        self.ctrl['break'] = not self.ctrl['break']
        thread = threading.Thread(target=capture, args=(
            self.bar, self.surprise, self.happiness, self.neutral, self.angry, self.sad, self.disgust, self.ctrl))
        if not self.ctrl['break']:
            thread.start()
            self.button.setText("Закончить запись")
        else:
            self.ctrl['break'] = True
            self.button.setText("Начать запись")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
