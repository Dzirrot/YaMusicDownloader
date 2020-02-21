import os
import re

from mutagen import File
from mutagen.id3 import TIT2, TPE1, TALB, APIC, TDRC, USLT
from yandex_music import Client, Playlist
from yandex_music.exceptions import YandexMusicError

# Задай переменную, куда будут выкачиваться музыкальные файлы.
FOLDER = "music"
DELIMITER = "/"

# Авторизационные данные от Я аккаунта.
LOGIN = ""
PASSWORD = ""


def strip_bad_symbols(text: str) -> str:
    result = re.sub(r"[^\w_.)( -]", "", text)
    return result


def download_playlist(playlist: Playlist, force_redownload=False):
    for short_track in playlist.tracks:
        track = short_track.track
        print(f"Downloading `{track.artists[0]['name']} - {track.title}`", end="... ")
        if not track.available:
            print("not available")
            continue

        track_path = os.path.normpath(os.path.join(
            strip_bad_symbols(track.artists[0]['name']),
            strip_bad_symbols(track.albums[0]['title'])
        ))

        os.makedirs(track_path, exist_ok=True)
        os.chdir(track_path)

        file_name = strip_bad_symbols(f'{track.title}')
        used_codec = None
        for info in sorted(track.get_download_info(), key=lambda x: x['bitrate_in_kbps'], reverse=True):
            codec = info['codec']
            bitrate = info['bitrate_in_kbps']
            full_file_name = f'{file_name}.{codec}'
            # file is not created 'til all bytes of it recieved,
            # so we can check if track was already downloaded
            # by just checking its existence on disk
            if os.path.exists(full_file_name) and not force_redownload:
                used_codec = codec # to prevent wrong `unknown downloading error` message
                break
            try:
                track.download(
                    full_file_name,
                    codec=codec,
                    bitrate_in_kbps=bitrate
                )
                used_codec = codec
                break
            except (YandexMusicError, TimeoutError):
                continue

        if not used_codec:
            print("unknown downloading error")
            continue

        cover_filename = file_name + ".jpg"
        track.download_cover(cover_filename, size="300x300")
        file = File(f'{file_name}.{used_codec}')
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
            'APIC': APIC(encoding=3, text=cover_filename, data=open(cover_filename, 'rb').read())
        })
        lyrics = client.track_supplement(track.track_id).lyrics
        if lyrics:
            # Song lyrics
            file.tags.add(USLT(encoding=3, text=lyrics.full_lyrics))

        file.save()
        os.chdir(pwd)
        print("done")


if __name__ == "__main__":
    folder = os.path.normpath(FOLDER)

    os.makedirs(folder, exist_ok=True)
    os.chdir(folder)
    pwd = os.getcwd()

    client = Client.from_credentials(LOGIN, PASSWORD)

    liked_by_plist = client.users_playlists(kind=3)
    if liked_by_plist:
        download_playlist(liked_by_plist[0])
    else:
        print("`Liked by me` list is empty")
