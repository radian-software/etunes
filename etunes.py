#!/usr/bin/env python3

import collections
import importlib.util
import json
import os
import sys
import yaml

# Exceptions

class MalformedMetadataError(Exception):
    pass

# Configuration

HOME_DIR = os.path.expanduser('~')
ETUNES_SRC_DIR = os.path.split(__file__)[0]

class Config:

    def __init__(self):
        self.emacs_dir = '.emacs.d'
        self.etunes_dir = 'etunes'
        self.etunes_artwork_dir = 'artwork'
        self.etunes_media_dir = 'media'
        self.etunes_metadata_dir = 'metadata'
        self.etunes_playlist_dir = 'playlist'
        self.file_extension = '.yml'
        self.user_plugin_file = 'etunes_plugin.py'

    def set_emacs_dir(self, emacs_dir):
        self.emacs_dir = emacs_dir

    def set_etunes_dir(self, etunes_dir):
        self.etunes_dir = etunes_dir

    def set_etunes_artwork_dir(self, etunes_artwork_dir):
        self.etunes_artwork_dir = etunes_artwork_dir

    def set_etunes_media_dir(self, etunes_media_dir):
        self.etunes_media_dir = etunes_media_dir

    def set_etunes_metadata_dir(self, etunes_metadata_dir):
        self.etunes_metadata_dir = etunes_metadata_dir

    def set_etunes_playlist_dir(self, etunes_playlist_dir):
        self.etunes_playlist_dir = etunes_playlist_dir

    def set_file_extension(self, file_extension):
        assert file_extension in ['.json', '.yml']
        self.file_extension = file_extension

    def set_user_plugin_file(self, user_plugin_file):
        self.user_plugin_file = user_plugin_file

    def get_album_artwork_filepath(self, artwork_filename):
        return os.path.join(
            HOME_DIR,
            self.emacs_dir,
            self.etunes_dir,
            self.etunes_artwork_dir,
            artwork_filename)

    def get_media_filepath(self, media_filename):
        return os.path.join(
            HOME_DIR,
            self.emacs_dir,
            self.etunes_dir,
            self.etunes_media_dir)

    def get_album_metadata_filepath(self, album_name):
        return os.path.join(
            HOME_DIR,
            self.emacs_dir,
            self.etunes_dir,
            self.etunes_metadata_dir,
            album_name + self.file_extension)

    def get_playlist_data_filepath(self, playlist_name):
        return os.path.join(
            HOME_DIR,
            self.emacs_dir,
            self.etunes_dir,
            self.etunes_playlist_dir,
            playlist_name + self.file_extension)

    def get_user_plugin_filepath(self):
        return os.path.join(
            HOME_DIR,
            self.emacs_dir,
            self.etunes_dir,
            self.user_plugin_file)

# Filesystem utilities

def ensure_parent_directories(filepath):
    os.makedirs(os.path.split(filepath)[0], exist_ok=True)

# External metadata

def read_data_file(filename):
    if filename.endswith('.json'):
        load = json.load
    elif filename.endswith('.yml'):
        load = yaml.safe_load
    else:
        assert False, 'Unknown metadata file type: ' + filename
    with open(filename) as f:
        return load(f)

def write_data_file(filename, metadata):
    if filename.endswith('.json'):
        dump = json.dump
    elif filename.endswith('.yml'):
        def dump(*args):
            yaml.dump(
                *args, default_flow_style=False, default_style='|')
    else:
        assert False, 'Unknown metadata file type: ' + filename
    ensure_parent_directories(filename)
    tmp_filename = filename + '.tmp'
    with open(tmp_filename, 'w') as f:
        dump(metadata, f)
    os.rename(tmp_filename, filename)

def merge_metadata(parent_metadata, child_metadata):
    merged_metadata = {}
    for key, val in parent_metadata.items():
        merged_metadata[key] = val
    for key, val in child_metadata.items():
        merged_metadata[key] = val
    return merged_metadata

def split_metadata(children):
    all_keys = set()
    for child in children:
        all_keys.update(child.keys())
    parent = {}
    for key in all_keys:
        counts = collections.Counter(child.get(key) for child in children)
        for val in counts:
            if val and counts[val] * 2 >= len(children):
                parent[key] = val
                break
    new_children = []
    for child in children:
        new_child = {}
        for key in child:
            if child[key] != parent.get(key):
                new_child[key] = child[key]
        new_children.append(new_child)
    return parent, new_children

# Data objects

class Song:

    def __init__(self, metadata):
        self.metadata = metadata

class Album:

    def __init__(self, name, songs):
        self.name = name
        self.songs = songs

def read_album_metadata(name, config):
    metadata = read_data_file(config.get_album_metadata_filepath(name))
    if not isinstance(metadata, dict):
        raise MalformedMetadataError('album metadata is not map: ' + name)
    for key in ['album', 'songs']:
        if key not in metadata:
            raise MalformedMetadataError(
                "album metadata missing key '{}': {}"
                .format(key, name))
        if not isinstance(metadata[key], dict):
            raise MalformedMetadataError(
                "album metadata has non-map for key '{}': {}"
                .format(key, name))
        for subkey, val in metadata[key].items():
            if not isinstance(subkey, str):
                raise MalformedMetadataError(
                    "album metadata has non-string as key under '{}': {}"
                    .format(key, name))
            if not isinstance(val, str):
                raise MalformedMetadataError(
                    "album metadata has non-string for "
                    "subkey '{}' under '{}': {}"
                    .format(subkey, key, name))
    for key in metadata:
        if key not in ['album', 'songs']:
            raise MalformedMetadataError(
                "album metadata has extraneous key: " + name)
    album_metadata = metadata['album']
    songs_metadata = metadata['songs']
    songs = []
    for song_metadata in songs_metadata:
        songs.append(Song(merge_metadata(album_metadata, song_metadata)))
    return Album(name, songs)

def write_album_metadata(album, config):
    filepath = config.get_album_metadata_filepath(album.name)
    songs_metadata = [song.metadata for song in album.songs]
    album_metadata, songs_metadata = split_metadata(songs_metadata)
    metadata = {
        'album': album_metadata,
        'songs': songs_metadata,
    }
    write_data_file(filepath, metadata)

# Plugins

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_plugin(config):
    user_plugin_filepath = config.get_user_plugin_filepath()
    default_plugin_filepath = os.path.join(
        ETUNES_SRC_DIR, 'etunes_plugin_default.py')
    if os.path.isfile(user_plugin_filepath):
        return load_module('etunes_plugin', user_plugin_filepath)
    else:
        return load_module('etunes_plugin_default', default_plugin_filepath)

# Command-line interface

def cli(args):
    config = Config()
    for arg in args:
        for flag, method in (
                ('--emacs-dir=', Config.set_emacs_dir),
                ('--etunes-dir=', Config.set_etunes_dir),
                ('--etunes-artwork-dir=', Config.set_etunes_artwork_dir),
                ('--etunes-media-dir=', Config.set_etunes_media_dir),
                ('--etunes-metadata-dir=', Config.set_etunes_metadata_dir),
                ('--etunes-playlist-dir=', Config.set_etunes_playlist_dir),
                ('--file-extension=', Config.set_file_extension),
                ('--user-plugin-file=', Config.set_user_plugin_file)
        ):
            if arg.startswith(flag):
                val = arg[len(flag):]
                method(config, val)
                break
    print('ok')
    print('output')

if __name__ == '__main__':
    cli(sys.argv[1:])
