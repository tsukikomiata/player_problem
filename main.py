import sys
import requests
import os
import yandex_api as ya

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidget
from PyQt5.QtCore import QCoreApplication, QUrl
from PyQt5.QtWidgets import QApplication, QSlider, QMessageBox, QAction, QMenu, QMainWindow, \
                            QDialog, QAction, QListWidgetItem, QFileDialog, QListWidget
from main_window import Ui_MainWindow
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist, QMediaMetaData, QMediaResource
from enter_yandex_music import Yam_Dialog


LOGIN = os.getenv('username')
PASSWORD = os.getenv('password')

client = ya.YandexClient((LOGIN, PASSWORD))
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
        r = requests.get(self.url)
        self.finished_signal.emit(r)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.currentFile = '/'
        self.player = QMediaPlayer()
        self.current_playlist = QMediaPlaylist(self.player)
        self.userAction = -1  # 0- stopped, 1- playing 2-paused
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.stateChanged.connect(self.state_changed)
        self.player.positionChanged.connect(self.position_changed)
        self.player.volumeChanged.connect(self.volume_changed)
        self.player.setVolume(60)
        self.setWindowTitle('Music Player')
        # Add Status bar
        self.statusBar().showMessage('No Media, Volume: %d' % self.player.volume())
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTracking(False)
        self.slider.sliderMoved.connect(self.seek_position)
        self.play_button.clicked.connect(self.play_handler)
        self.pause_button.clicked.connect(self.pause_handler)
        self.stop_button.clicked.connect(self.stop_handler)
        self.volume_decrease_button.clicked.connect(self.decrease_volume)
        self.volume_increase_button.clicked.connect(self.increase_volume)
        self.downloaded_tracks.itemDoubleClicked.connect(self.open_file)
        self.enter_yandex_button.clicked.connect(self.enter_yandex)
        # playlist control button handlers
        self.prev_button.clicked.connect(self.prevItemPlaylist)
        self.next_button.clicked.connect(self.nextItemPlaylist)
        # self.get_music_thread = GetMusic(url=)
        self.current_track_id = '52608947:7413860'
        self.track_path = 'tracks/'
        self.fill_downloaded_tracks()

        for track in list_track:
            item = QListWidgetItem(str(track) + ' — ' + track.duration)
            item.setData(256, track.id)
            self.playlist_window.addItem(item)

        self.playlist_window.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.playlist_window.customContextMenuRequested.connect(self.context_menu)

    @staticmethod
    def enter_yandex():
        a = Enter_Yandex()
        a.show()
        a.exec()

    def context_menu(self):
        menu = QMenu()
        download_action = QAction('Скачать')
        download_action.triggered.connect(self.download)
        menu.addAction(download_action)
        menu.exec(QtGui.QCursor.pos())

    def open_file(self, item):
        try:
            track_name = item.text()
            full_file_path = os.path.join(os.getcwd(), f'/tracks/{track_name}')
            url = QUrl.fromLocalFile(full_file_path)
            content = QMediaContent(url)
            self.current_playlist.addMedia(content)
        except Exception as e:
            print(e)

    def play_handler(self):
        self.userAction = 1
        self.statusBar().showMessage('Playing at Volume %d' % self.player.volume())
        if self.player.state() == QMediaPlayer.StoppedState:
            if self.player.mediaStatus() == QMediaPlayer.NoMedia:
                print(self.current_playlist.mediaCount())
                if self.player.mediaStatus() == QMediaPlayer.NoMedia:
                    # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.currentFile)))
                    print(self.current_playlist.mediaCount())
                    if self.current_playlist.mediaCount() == 0:
                        print('222')
                    if self.current_playlist.mediaCount() != 0:
                        try:
                            self.player.setPlaylist(self.current_playlist)
                        except Exception as e:
                            print(e)
            elif self.player.mediaStatus() == QMediaPlayer.LoadedMedia:
                self.player.play()
            elif self.player.mediaStatus() == QMediaPlayer.BufferedMedia:
                self.player.play()
        elif self.player.state() == QMediaPlayer.PlayingState:
            pass
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()

        # try:
        #     self.player.setPlaylist(self.current_playlist)
        # except Exception as e:
        #     print(e)
        # try:
        #     self.player.play()
        # except Exception as e:
        #     print(e)

    def init_player(self):
        # print(args)
        url = get_url_by_track(self.current_track_id, client)
        content = QMediaContent(QtCore.QUrl(url))
        self.player.setMedia(content)
        self.player.setVolume(50)
        self.player.play()

    def current_track(self, item: QListWidgetItem):
        self.current_track_id = item.data(256)

    def pause_handler(self):
        self.userAction = 2
        self.statusBar().showMessage('Paused %s at position %s at Volume %d' %
                                     (self.player.metaData(QMediaMetaData.Title),
                                      self.centralWidget().layout().itemAt(0).layout().itemAt(0).widget().text(),
                                      self.player.volume()))
        self.player.pause()

    def stop_handler(self):
        self.userAction = 0
        self.statusBar().showMessage('Stopped at Volume %d' % (self.player.volume()))
        if self.player.state() == QMediaPlayer.PlayingState:
            self.stop_state = True
            self.player.stop()
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.stop()
        elif self.player.state() == QMediaPlayer.StoppedState:
            pass

    def media_status_changed(self):
        if self.player.mediaStatus() == QMediaPlayer.LoadedMedia and self.userAction == 1:
            durationT = self.player.duration()
            self.centralWidget().layout().itemAt(0).layout().itemAt(1).widget().setRange(0, durationT)
            self.centralWidget().layout().itemAt(0).layout().itemAt(2).widget().setText(
                '%d:%02d' % (int(durationT / 60000), int((durationT / 1000) % 60)))
            self.player.play()

    def state_changed(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            self.player.stop()

    def position_changed(self, position, sender_type=False):
        slider_layout = self.centralWidget().layout().itemAt(0).layout()
        if not sender_type:
            slider_layout.itemAt(1).widget().setValue(position)
        # update the text label
        slider_layout.itemAt(0).widget().setText('%d:%02d' % (int(position / 60000), int((position / 1000) % 60)))

    def seek_position(self, position):
        sender = self.sender()
        if isinstance(sender, QSlider):
            if self.player.isSeekable():
                self.player.setPosition(position)

    def volume_changed(self):
        msg = self.statusBar().currentMessage()
        msg = msg[:-2] + str(self.player.volume())
        self.statusBar().showMessage(msg)

    def increase_volume(self):
        vol = self.player.volume()
        vol = min(vol + 5, 100)
        self.player.setVolume(vol)

    def decrease_volume(self):
        vol = self.player.volume()
        vol = max(vol - 5, 0)
        self.player.setVolume(vol)

    def download(self):
        cur_row = self.playlist_window.currentRow()
        cur_track = self.playlist_window.item(cur_row)
        self.current_track_id = cur_track.data(256)
        track = client.track_by_id(self.current_track_id)
        try:
            track.download(f'{self.track_path}{str(track)}.mp3')
        except Exception as e:
            print(e)

    def fill_downloaded_tracks(self):
        list_downloaded_tracks = os.listdir(self.track_path)
        for track in list_downloaded_tracks:
            item = QListWidgetItem(str(track))
            self.downloaded_tracks.addItem(item)

    def prevItemPlaylist(self):
        self.player.playlist().previous()

    def nextItemPlaylist(self):
        self.player.playlist().next()

    def exit_action(self):
        exit_ac = QAction('&Exit', self)
        exit_ac.setStatusTip('Exit App')
        exit_ac.triggered.connect(self.closeEvent)
        return exit_ac

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to exit?', QMessageBox.Yes | QMessageBox.No,
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