import sys

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QSlider, QMessageBox, QAction, QWidget
from main_window import Ui_MainWindow
from PyQt5.QtMultimedia import *


class MainWindow(Ui_MainWindow):
    def __init__(self):
        super().__init__()

        # self.currentFile = '/'
        self.currentPlaylist = QMediaPlaylist()
        self.player = QMediaPlayer()
        self.userAction = -1  # 0- stopped, 1- playing 2-paused
        self.player.mediaStatusChanged.connect(self.qmp_mediaStatusChanged)
        self.player.stateChanged.connect(self.qmp_stateChanged)
        self.player.positionChanged.connect(self.qmp_positionChanged)
        self.player.volumeChanged.connect(self.qmp_volumeChanged)
        self.player.setVolume(60)
        self.setWindowTitle('Music Player')
        # Add Status bar
        self.statusBar().showMessage('No Media :: %d' % self.player.volume())
        self.homeScreen()

    def homeScreen(self):
        # Add Control Bar
        controlBar = self.addControls()

        # need to add both infoscreen and control bar to the central widget.
        centralWidget = QWidget()
        centralWidget.setLayout(controlBar)
        self.setCentralWidget(centralWidget)
        self.show()

    def addControls(self):
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTracking(False)
        self.slider.sliderMoved.connect(self.seekPosition)

        self.playBtn.clicked.connect(self.playHandler)
        self.pauseBtn.clicked.connect(self.pauseHandler)
        self.stopBtn.clicked.connect(self.stopHandler)
        self.volumeDescBtn.clicked.connect(self.decreaseVolume)
        self.volumeIncBtn.clicked.connect(self.increaseVolume)

        # playlist control button handlers
        self.prevBtn.clicked.connect(self.prevItemPlaylist)
        self.nextBtn.clicked.connect(self.nextItemPlaylist)

    def playHandler(self):
        self.userAction = 1
        self.statusBar().showMessage('Playing at Volume %d' % self.player.volume())
        if self.player.state() == QMediaPlayer.StoppedState:
            if self.player.mediaStatus() == QMediaPlayer.NoMedia:
                # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.currentFile)))
                print(self.currentPlaylist.mediaCount())
                if self.currentPlaylist.mediaCount() == 0:
                    self.openFile()
                if self.currentPlaylist.mediaCount() != 0:
                    self.player.setPlaylist(self.currentPlaylist)
            elif self.player.mediaStatus() == QMediaPlayer.LoadedMedia:
                self.player.play()
            elif self.player.mediaStatus() == QMediaPlayer.BufferedMedia:
                self.player.play()
        elif self.player.state() == QMediaPlayer.PlayingState:
            pass
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()

    def pauseHandler(self):
        self.userAction = 2
        self.statusBar().showMessage('Paused %s at position %s at Volume %d' % \
                                     (self.player.metaData(QMediaMetaData.Title), \
                                      self.centralWidget().layout().itemAt(0).layout().itemAt(0).widget().text(), \
                                      self.player.volume()))
        self.player.pause()

    def stopHandler(self):
        self.userAction = 0
        self.statusBar().showMessage('Stopped at Volume %d' % (self.player.volume()))
        if self.player.state() == QMediaPlayer.PlayingState:
            self.stopState = True
            self.player.stop()
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.stop()
        elif self.player.state() == QMediaPlayer.StoppedState:
            pass

    def qmp_mediaStatusChanged(self):
        if self.player.mediaStatus() == QMediaPlayer.LoadedMedia and self.userAction == 1:
            durationT = self.player.duration()
            self.centralWidget().layout().itemAt(0).layout().itemAt(1).widget().setRange(0, durationT)
            self.centralWidget().layout().itemAt(0).layout().itemAt(2).widget().setText(
                '%d:%02d' % (int(durationT / 60000), int((durationT / 1000) % 60)))
            self.player.play()

    def qmp_stateChanged(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            self.player.stop()

    def qmp_positionChanged(self, position, senderType=False):
        sliderLayout = self.centralWidget().layout().itemAt(0).layout()
        if senderType == False:
            sliderLayout.itemAt(1).widget().setValue(position)
        # update the text label
        sliderLayout.itemAt(0).widget().setText('%d:%02d' % (int(position / 60000), int((position / 1000) % 60)))

    def seekPosition(self, position):
        sender = self.sender()
        if isinstance(sender, QSlider):
            if self.player.isSeekable():
                self.player.setPosition(position)

    def qmp_volumeChanged(self):
        msg = self.statusBar().currentMessage()
        msg = msg[:-2] + str(self.player.volume())
        self.statusBar().showMessage(msg)

    def increaseVolume(self):
        vol = self.player.volume()
        vol = min(vol + 5, 100)
        self.player.setVolume(vol)

    def decreaseVolume(self):
        vol = self.player.volume()
        vol = max(vol - 5, 0)
        self.player.setVolume(vol)

    def prevItemPlaylist(self):
        self.player.playlist().previous()

    def nextItemPlaylist(self):
        self.player.playlist().next()

    def exitAction(self):
        exitAc = QAction('&Exit', self)
        exitAc.setShortcut('Ctrl+Q')
        exitAc.setStatusTip('Exit App')
        exitAc.triggered.connect(self.closeEvent)
        return exitAc

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'Pres Yes to Close.', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            QCoreApplication.quit()
        else:
            try:
                event.ignore()
            except AttributeError:
                pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())