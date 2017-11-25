## eTunes specification

The `etunes-dir` (by default, `~/.emacs.d/etunes/`) is the default
location of other eTunes directories.

The `etunes-media-dir` (by default, `${etunes-dir}/media/`) is the
directory relative to which media filepaths are expanded. It may
contain an arbitrary directory tree of media and other files.

The `etunes-metadata-dir` (by default, `${etunes-dir}/metadata/`) is
the directory containing album metadata. For each album, there is a
`.json` or `.yml` file of the same name containing the metadata for
that album and its songs.

The `etunes-artwork-dir` (by default, `${etunes-dir}/artwork/`) is the
directory relative to which album artwork filepaths are expanded. It
may contain an arbitrary directory tree of image and other files.

The `etunes-playlist-dir` (by default, `${etunes-dir}/playlists/`) is
the directory containing playlist data. For each playlist, there is a
`.json` or `.yml` file of the same name containing the metadata for
that playlist.

An album metadata file contains the JSON or YAML encoding of a map.
The keys of the map are `album` and `songs`. The `album` key maps to a
map with arbitrary keys and values representing the metadata shared by
all songs in the album. In this map, the value `null` is reserved to
indicate the lack of metadata for a particular key; that is,
applications may not distinguish between a metadata key with `null` as
its value and a metadata key which is missing entirely. The `songs`
key maps to an array of maps with arbitrary keys and values
representing the metadata for each particular song (including, for
example, the name and filename). At the song level, the key `uuid` is
reserved for an automatically generated UUID particular to the song.

A playlist data file contains the JSON and YAML encoding of an array.
The entries in this array are UUIDs which corresponding to the `uuid`
entries in songs.
