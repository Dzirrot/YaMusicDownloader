import os
import re

from mutagen import File
from mutagen.id3 import TIT2, TPE1, TALB, APIC, TDRC, USLT
from yandex_music import *
from yandex_music.exceptions import YandexMusicError

# Задай переменную, куда будут выкачиваться музыкальные файлы.
FOLDER = "music"

# Авторизационные данные от Я аккаунта.
LOGIN = ''
PASSWORD = ''

DELIMITER = '/'


def cut_bad_symbols(text: str) -> str:
    result = re.sub(r"[\"#%&{}/\<>*?$!`“:+=|\[\]]", "", text)
    print(result)
    return result


if __name__ == '__main__':
    if not FOLDER:
        folder = "music"
    else:
        folder = os.path.normpath(FOLDER)

    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)
    pwd = os.getcwd()

    client = Client.from_credentials(LOGIN, PASSWORD)

    # Вот тут можно поиграться и повыбирать откуда выкачивать музыку. Сейчас задано из "Моя Музыка/Мне нравится".
    # Получить список треков из определённого пользовательского списка
    # playlist = client.users_playlists_list()[2] - где 2 это номер плейлиста в списке.
    # shorted_tracks = client.users_playlists(kind=playlist.kind, user_id=playlist.uid)[0].tracks
    #
    # playlist = client.landing('personalplaylists').blocks[0].entities[0].data.data
    # shorted_tracks = client.users_playlists(kind=playlist.kind, user_id=playlist.uid)[0].tracks
    for playlist in client.users_playlists_list():
        shorted_tracks = client.users_playlists(kind=playlist.kind, user_id=playlist.uid)[0].tracks
        for short_track in shorted_tracks:
            track = short_track.track
            if not track.available:
                continue
            track_path = cut_bad_symbols(os.path.normpath(f"{track.artists[0]['name']}/{track.albums[0]['title']}"))
            if 'The Neighbourhood' in track_path:
                x = 5
            os.makedirs(track_path, exist_ok=True)
            os.chdir(track_path)

            for info in sorted(track.get_download_info(), key=lambda x: x['bitrate_in_kbps'], reverse=True):
                codec = info['codec']
                bitrate = info['bitrate_in_kbps']
                file_name = cut_bad_symbols(f'{track.title}')
                try:
                    track.download(
                        file_name + f'.{codec}',
                        codec=codec,
                        bitrate_in_kbps=bitrate
                    )
                    break
                except (YandexMusicError, TimeoutError):
                    continue
            track.download_cover(file_name + '.jpg', size='300x300')
            file = File(file_name + f'.{codec}')
            file.update({
                # Title
                'TIT2': TIT2(encoding=3, text=track.title),
                # Artist
                'TPE1': TPE1(encoding=3, text=DELIMITER.join(i['name'] for i in track.artists)),
                # Album
                'TALB': TALB(encoding=3, text=DELIMITER.join(i['title'] for i in track.albums)),
                # Year
                'TDRC': TDRC(encoding=3, text=str(track.albums[0]['year'])),
                # Picture
                'APIC': APIC(encoding=3, text=file_name + '.jpg', data=open(file_name + '.jpg', 'rb').read())
            })
            lyrics = client.track_supplement(track.track_id).lyrics
            if lyrics:
                # Song words
                file.tags.add(USLT(encoding=3, text=lyrics.full_lyrics))

            file.save()
            os.chdir(pwd)
