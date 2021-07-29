import sys
import requests
import yandex_api as ya

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QSlider, QMessageBox, QAction, QWidget, QMainWindow, QDialog, QListWidget, QListWidgetItem
from main_window import Ui_MainWindow
from PyQt5.QtMultimedia import *
from enter_yandex_music import Yam_Dialog


client = ya.YandexClient()
list_track = client.get_ru_chart().tracks


def get_url_by_track(track_id, client_ya):
    track = client_ya.track_by_id(track_id)
    return track.download_link()


class GetMusic(QtCore.QThread):
    finised_signal = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.finished_signal.emit(self.url)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
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
        self.statusBar().showMessage('No Media, Volume: %d' % self.player.volume())
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTracking(False)
        self.slider.sliderMoved.connect(self.seekPosition)
        self.playBtn.clicked.connect(self.playHandler)
        self.pauseBtn.clicked.connect(self.pauseHandler)
        self.stopBtn.clicked.connect(self.stopHandler)
        self.volumeDescBtn.clicked.connect(self.decreaseVolume)
        self.volumeIncBtn.clicked.connect(self.increaseVolume)
        # self.enterSptBtn.clicked.connect(self.enter_Spotify)
        self.enterYanBtn.clicked.connect(self.enter_Yandex)
        # playlist control button handlers
        self.prevBtn.clicked.connect(self.prevItemPlaylist)
        self.nextBtn.clicked.connect(self.nextItemPlaylist)
        # self.get_music_thread = GetMusic(url=)
        self.current_track_id = '52608947:7413860'

        for track in list_track:
            item = QListWidgetItem(str(track) + ' — ' + track.duration)
            item.setData(256, track.id)
            self.playlist_window.addItem(item)


    def enter_Yandex(self):
        a = Enter_Yandex()
        a.show()
        a.exec()

    def playHandler(self):
        self.userAction = 1
        self.statusBar().showMessage('Playing at Volume %d' % self.player.volume())
        if self.player.state() == QMediaPlayer.StoppedState:
            if self.player.mediaStatus() == QMediaPlayer.NoMedia:
                # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.currentFile)))
                print(self.currentPlaylist.mediaCount())
                if self.currentPlaylist.mediaCount() == 0:
                    print('1')
                    url = get_url_by_track(self.current_track_id, client)
                    print('2')
                    self.get_music_thread = GetMusic(url)
                    print('3')
                    self.get_music_thread.finised_signal.connect(self.init_player)
                    print('4')
                    self.get_music_thread.start()
                    print('5')
                if self.currentPlaylist.mediaCount() != 0:
                    self.player.setPlaylist(self.currentPlaylist)
            elif self.player.mediaStatus() == QMediaPlayer.LoadedMedia:
                url = get_url_by_track(self.current_track_id, client)
                self.get_music_thread = GetMusic(url)
                self.get_music_thread.finised_signal.connect(self.init_player)
                self.get_music_thread.start()
            elif self.player.mediaStatus() == QMediaPlayer.BufferedMedia:
                self.player.play()
        elif self.player.state() == QMediaPlayer.PlayingState:
            pass
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()

    def init_player(self):
        # print(args)
        url = get_url_by_track(self.current_track_id, client)
        content = QMediaContent(QtCore.QUrl(url))
        self.player.setMedia(content)
        self.player.setVolume(50)
        self.player.play()

    def current_track(self, item: QListWidgetItem):
        self.current_track_id = item.data(256)

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

    def download(self):
        pass

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


class Enter_Yandex(QDialog, Yam_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.log_pass()
        self.pushButton.clicked.connect(self.log_pass)

    def log_pass(self):
        login = self.login_yan.text()
        password = self.pass_yan.text()
        login_and_password = (login, password)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
