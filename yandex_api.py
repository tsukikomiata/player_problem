import os
import requests
from typing import List, Union, Tuple

import yandex_music as ym
from yandex_music.exceptions import BadRequest, Captcha


LOGIN = os.getenv('username')
PASSWORD = os.getenv('password')


def check_anonymous(func):
    def decorator(self, *args, **kwargs):
        if self.is_anonymous:
            return None
        else:
            return func(self, *args, **kwargs)
    return decorator


class YandexTrack:
    def __init__(self, track: Union[ym.Track, ym.TrackShort]):
        if isinstance(track, ym.TrackShort):
            self.__track = track.fetch_track()
        else:
            self.__track = track
        self.__id = self.__track.track_id

    @property
    def title(self) -> str:
        return self.__track.title

    @property
    def id(self):
        return self.__id

    @property
    def artists_list(self) -> List:
        artists = list()
        for artist in self.__track.artists:
            artists.append(YandexArtist(artist))
        return artists

    def __repr__(self):
        """Возвращает песню в формате НАЗВАНИЕ by ИСПОЛНИТЕЛЬ_1, ИСПОЛНИТЕЛЬ_2 и т.д."""
        return self.title + ' by ' + ', '.join(list(map(str, self.artists_list)))

    def __str__(self):
        return self.__repr__()

    @property
    def duration(self) -> str:
        """Продолжительность трека в формате минуты:секунды (без часов)"""
        duration_ms = self.__track.duration_ms
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds -= minutes * 60
        s_seconds = str(seconds) if seconds >= 10 else '0' + str(seconds)
        s_minutes = str(minutes) if minutes >= 10 else '0' + str(minutes)
        return f'{s_minutes}:{s_seconds}'

    @property
    def duration_sec(self):
        """Целочисленное значение продолжительности трека в секундах"""
        return self.__track.duration_ms // 1000

    def download_link(self) -> str:
        """
        Возвращает прямую ссылку на трек
        Ссылка работает только минуту после генерации, после запрос выдаст 401
        """
        return self.__track.get_download_info()[0].get_direct_link()

    def get_track(self) -> requests.Response:
        """Получаем трек с помощью ссылки из метода download_link"""
        r = requests.get(self.download_link())
        return r

    def download(self, filename: str):
        """
        Скачиваем трек в формате mp3
        :param filename: Имя файла вместе с расширением
        """
        self.__track.download(filename, codec='mp3')


class YandexPlaylist:
    def __init__(self, playlist: ym.Playlist):
        self.__playlist = playlist

    @property
    def title(self) -> str:
        return self.__playlist.title

    def __repr__(self):
        return self.title

    def __len__(self):
        return self.__playlist.track_count

    @property
    def tracks(self) -> List[YandexTrack]:
        """Получаем список треков, которые лежат в плейлисте"""
        tracklist = list()
        for track in self.__playlist.tracks:
            track = YandexTrack(track)
            tracklist.append(track)
        return tracklist


class YandexAlbum:
    def __init__(self, album: ym.Album):
        self.__album = album

    @property
    def title(self):
        return self.__album.title

    def __repr__(self):
        return self.title

    def __len__(self):
        return self.__album.track_count

    def get_tracks(self) -> List[YandexTrack]:
        """Получаем список треков, лежащих в альбоме (без разделения на диски)"""
        all_tracks = list()
        for volume in self.__album.volumes:
            for track in volume:
                all_tracks.append(YandexTrack(track))
        return all_tracks


class YandexArtist:
    def __init__(self, artist: ym.Artist):
        self.__artist = artist

    @property
    def name(self):
        return self.__artist.name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_albums(self) -> List[YandexAlbum]:
        """
        Получаем список всех альбомов артиста, включая:
        синглы, сборники и альбомы другого артиста, если в них есть фит с этим
         """
        all_albums = list()
        page = 0
        albums_on_page = True
        while albums_on_page:
            if not self.__artist.get_albums(page=page):
                albums_on_page = False
            else:
                for album in self.__artist.get_albums(page=page):
                    all_albums.append(YandexAlbum(album))
                page += 1
        return all_albums

    def get_tracks(self) -> List[YandexTrack]:
        all_tracks = list()
        page = 0
        tracks_on_page = True
        while tracks_on_page:
            if not self.__artist.get_tracks(page=page):
                tracks_on_page = False
            else:
                for track in self.__artist.get_tracks(page=page):
                    all_tracks.append(YandexTrack(track))
                page += 1
        return all_tracks


class YandexClient:
    def __init__(self, yandex_client: Union[ym.Client, Tuple[str, str]] = ym.Client()):
        """
        :param yandex_client: Принимает инстанс класса ym.Client, либо кортеж из двух строк
        Во втором случае пытается войти в аккаунт по логину/паролю, в случае неуспеха YandexClient создаётся,
        но факт ошибки сохраняется.
        Если параметр не указывается, создаём анонимного пользователя
        """
        self.__error = False
        self.__client = None
        if isinstance(yandex_client, ym.Client):
            self.__client = yandex_client
        else:
            self.init_client(yandex_client)
        if self.__error:
            self.is_anonymous = True
        else:
            if self.__client.account_status()['account']['login'] is None:
                self.is_anonymous = True
            else:
                self.is_anonymous = False
        self.subscription_status = False
        if not self.is_anonymous:
            self.subscription_status = self.__client.account_status()['plus'].has_plus

    def init_client(self, yandex_client: Tuple[str, str]):
        """
        Инициализация клиента. Вынесена в отдельную функцию, поскольку иногда требуется ввод капчи
        Капча загружается в файл captcha.png в рабочей директории
        Ответ на капчу вводится обычным инпутом
        :param yandex_client: Кортеж из двух строк (логин и пароль)
        Пока не будет введена правильная капча, она будет перезагружаться
        """
        login, pwd = yandex_client
        try:
            captcha_key = captcha_answer = None
            while not self.__client:
                try:
                    self.__client = ym.Client.fromCredentials(login, pwd, captcha_answer, captcha_key)
                except Captcha as captcha:
                    print(captcha_key, captcha_answer)
                    try:
                        os.remove('captcha.png')
                    except FileNotFoundError:
                        pass
                    captcha.captcha.download('captcha.png')
                    captcha_key = captcha.captcha.x_captcha_key
                    captcha_answer = input()
        except BadRequest:
            self.__error = True
            self.__client = ym.Client()

    @property
    def error(self) -> bool:
        """True, если не получилось войти по логину/паролю (можно сообщить пользователю об этом)"""
        return self.__error

    @check_anonymous
    def like_track(self, track: YandexTrack) -> bool:
        """True, если получилось лайкнуть трек"""
        return self.__client.users_likes_tracks_add(track.id)

    @check_anonymous
    def dislike_track(self, track: YandexTrack) -> bool:
        """True, если получилось дизлайкнуть трек"""
        return self.__client.users_dislikes_tracks_add(track.id)

    @check_anonymous
    def get_user_favourite_tracks(self) -> Union[None, List[YandexTrack]]:
        tracks = list()
        for track in self.__client.users_likes_tracks():
            tracks.append(YandexTrack(track))
        return tracks

    @check_anonymous
    def get_playlists(self) -> Union[None, List[YandexPlaylist]]:
        """Список всех плейлистов юзера либо None, если пользователь не вошёл"""
        playlists_list = list()
        for playlist in self.__client.users_playlists_list():
            playlist_kind = playlist.kind
            playlists_list.append(YandexPlaylist(self.__client.users_playlists(kind=playlist_kind)))
        return playlists_list

    def search_artist_by_name(self, name: str, full_compar: bool = False) -> List[YandexArtist]:
        """
        :param name: Строка, по которой будет производиться поиск
        :param full_compar: Если True, ищем только полные соответствия (по умолчанию False)
        :return: Список артистов, удовлетворивших критериям поиска
        """
        artist_list = list()
        for result in self.__client.search(name).artists.results:
            if (full_compar and result.name == name) or not full_compar:
                artist_list.append(YandexArtist(result))
        return artist_list

    def search_track_by_title(self, title: str, full_compar: bool = False) -> List[YandexTrack]:
        """
        :param title: Название трека, по которому производится поиск
        :param full_compar: Если True, ищем только полные соответствия (по умолчанию False)
        :return: Список треков, удовлетворивших условиям поиска
        """
        track_list = list()
        for result in self.__client.search(title).tracks.results:
            if (full_compar and result.title == title) or not full_compar:
                track_list.append(YandexTrack(result))
        return track_list

    def search_all(self, name: str, full_compar: bool = False) -> List[Union[List[YandexArtist], List[YandexTrack]]]:
        """
        Поиск артистов и треков по заданной строке
        :return: Список списков артистов и треков
        """
        artist_list = self.search_artist_by_name(name, full_compar)
        track_list = self.search_track_by_title(name, full_compar)
        return [artist_list, track_list]

    def track_by_id(self, track_id: str) -> YandexTrack:
        track = self.__client.tracks(track_id)[0]
        return YandexTrack(track)

    def get_world_chart(self) -> YandexPlaylist:
        """Возвращает мировой чарт в виде плейлиста"""
        chart = self.__client.chart('world')
        return YandexPlaylist(chart.chart)

    def get_ru_chart(self) -> YandexPlaylist:
        """Возвращает русский чарт в виде плейлиста"""
        chart = self.__client.chart('russia')
        return YandexPlaylist(chart.chart)

    @check_anonymous
    def get_generated_playlists(self) -> Union[None, List[YandexPlaylist]]:
        """
        Возвращает автоматически сгенерированные плейлисты (как плейлист дня, тайник и подобные)
        Если юзер анонимный, возвращает None
        """
        playlists = list()
        for generated_playlist in self.__client.feed().generated_playlists:
            playlists.append(YandexPlaylist(generated_playlist.data))
        return playlists

