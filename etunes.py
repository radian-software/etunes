#!/usr/bin/env python3

import mutagen
import os
import yaml

# External metadata


def merge_metadata(parent_metadata, child_metadata):
    merged_metadata = {}
    for key, val in parent_metadata.items():
        merged_metadata[key] = val
    for key, val in child_metadata.items():
        merged_metadata[key] = val
    return merged_metadata


def split_metadata(parent_metadata, merged_metadata):
    child_metadata = {}
    # If there is metadata in the merged version and it's different
    # from the parent, put the modified version in the child.
    for key, val in merged_metadata.items():
        if key in parent_metadata and parent_metadata[key] == val:
            continue
        child_metadata[key] = val
    # If there *isn't* metadata in the merged version but there is in
    # the parent, explicitly override it to None in the child.
    for key in parent_metadata:
        if key not in merged_metadata:
            child_metadata[key] = None
    return child_metadata


def read_external_metadata(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def write_external_metadata(filename, metadata):
    tmp_filename = filename + '.tmp'
    with open(tmp_filename) as f:
        yaml.dump(metadata, f)
    os.rename(tmp_filename, filename)

# Embedded metadata


def get_id3_str(dictlike, key):
    try:
        return str(dictlike[key])
    except KeyError:
        return None


def get_id3_fraction(dictlike, key):
    try:
        frac = str(dictlike[key])
        if '/' in frac:
            pivot = frac.index('/')
            num = frac[:pivot]
            den = frac[pivot+1:]
        else:
            num = frac
            den = None
        return num, den
    except KeyError:
        return None, None


def read_embedded_metadata(filename):
    f = mutagen.File(filename)
    track, total_tracks = get_id3_fraction(f, 'TRCK')
    disk, total_disks = get_id3_fraction(f, 'TPOS')
    return {
        'album-name': get_id3_str(f, 'TALB'),
        'artist': get_id3_str(f, 'TPE1'),
        'album-artist': get_id3_str(f, 'TPE2'),
        'comment': get_id3_str(f, 'COMM::eng'),
        'composer': get_id3_str(f, 'TCOM'),
        'disk': disk,
        'sort-artist': get_id3_str(f, 'TSOA'),
        'sort-title': get_id3_str(f, 'TSOT'),
        'title': get_id3_str(f, 'TIT2'),
        'total-disks': total_disks,
        'total-tracks': total_tracks,
        'track': track,
        'year': get_id3_str(f, 'TDRC'),
    }


def write_embedded_metadata(filename, metadata):
    print("Write embedded metadata to '{}'".format(filename))
