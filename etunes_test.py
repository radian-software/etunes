#!/usr/bin/env python3

import etunes
import os

itunes_dir = os.path.join(etunes.HOME_DIR, 'files', 'itunes', 'Music')

config = etunes.Config()
config.set_etunes_media_dir(itunes_dir)

for artist in os.listdir(itunes_dir):
    artist_dir = os.path.join(itunes_dir, artist)
    for album in os.listdir(artist_dir):
        album_dir = os.path.join(artist_dir, album)
        if not os.path.isdir(album_dir):
            continue
        songs = []
        for song in os.listdir(album_dir):
            if song[-4:] in ['.mp3', '.m4a', '.aiff']:
                song_filename = os.path.join(album_dir, song)
                metadata = etunes.read_embedded_metadata(song_filename)
                songs.append(etunes.Song(metadata))
        if not songs:
            continue
        album = etunes.Album(album, songs)
        etunes.write_album_metadata(album, config)
        print(artist + ' - ' + album.name)
