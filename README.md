# Command-line interface

General interface:

    $ etunes [--library=<library-file>] <subcommand>

Create a default `library.yml`:

    $ etunes init <path>

Make a query:

    $ etunes query [<json> | @<query-file> | -]

Environment variables:

    $ETUNES_LIBRARY

# Example `library.yml`

    options:
      deduplication-threshold: "0.75"
      media-path: "media/{album-artist}/{album}/{title}.{ext}"
      metadata-path: "metadata/{album-artist}/{album}.yml"

# Example queries

Get the value of an option:

    {
        "options": [
            {
                "name": "deduplication-threshold"
            }
        ]
    }

Response:

    {
        "success": true,
        "id": "404b8adf-4964-4cc0-b715-151a32fc1897",
        "options": [
            {
                "name": "deduplication-threshold",
                "value": "0.75"
            }
        ]
    }

Update the value of an option. Note that we can prevent race
conditions by telling the server to abort if some other transaction
took place in between this one and the previous one:

    {
        "last-id": "404b8adf-4964-4cc0-b715-151a32fc1897",
        "options": [
            {
                "name": "deduplication-threshold",
                "value": "0.5"
            }
        ]
    }

Response, if another transaction happened in the meantime:

    {
        "success": false,
        "errors": [
            {
                "reason": "intervening-transaction",
                "message": "Another transaction happened after 404b8adf-4964-4cc0-b715-151a32fc1897 but before this one",
                "last-id": "6ca38866-3b67-4dbd-9aff-f15e0f3754cb"
            }
        ]
    }

Otherwise:

    {
        "success": true,
        "id": "dd511d86-9552-4770-b3eb-b0cd6f49d06d",
        "options": [
            {
                "name": "deduplication-threshold",
                "value": "0.5"
            }
        ]
    }

Get a list of all the songs:

    {
        "songs": [
            {
                "get": [
                    "title",
                    "album",
                    "album-artist",
                    "track-number"
                ]
            }
        ]
    }

Response:

    {
        "success": true,
        "songs": [
            [
                {
                    "title": "Adventure Awaits! (Alola Region Theme)"
                    "album": "Alola That Jazz",
                    "album-artist": "insaneintherainmusic",
                    "track-number": "1"
                },
                    ...
                {
                    "title": "stranger_think",
                    "album": "2 years of failure",
                    "album-artist": "C418",
                    "track-number": "15"
                }
            ]
        ]
    }

Only get the songs from one album:

    {
        "songs": [
            {
                "filter": {
                    "album": "Time",
                    "album-artist": "Electric Light Orchestra"
                },
                "get": [
                    "title",
                    "track-number",
                    "uuid"
                ]
            }
        ]
    }

Response:

    {
        "success": true,
        "songs": [
            [
                {
                    "title": "Prologue/Twilight",
                    "track-number": "1",
                    "uuid": "710e3091-08f3-4202-8eec-dc6b4176de2b"
                },
                    ...
                {
                    "title": "Hold on Tight/Epilogue",
                    "track-number": "11",
                    "uuid": "edeaa029-be64-4146-ae5a-4f44a0427386"
                }
            ]
        ]
    }

Update the metadata on a single song:

    {
        "songs": [
            {
                "filter": {
                    "uuid": "edeaa029-be64-4146-ae5a-4f44a0427386"
                },
                "set": {
                    "title": "Hold on Tight / Epilogue"
                }
            }
        ]
    }

Response:

    {
        "songs": [
            [
                {}
            ]
        ]
    }

Update the metadata for an entire album:

    {
        "songs": [
            {
                "filter": {
                    "album": "Time",
                    "album-artist": "Electric Light Orchestra"
                },
                "set": {
                    "album-artist": "ELO"
                }
            }
        ]
    }

Response:

    {
        "songs": [
            [
                {},
                    ...
                {}
            ]
        ]
    }

Search the library:

    {
        "songs": [
            {
                "filter": {
                    "!any": {
                        "query": "danger",
                        "type": "literal",
                        "substring": true,
                        "case-fold": true
                    }
                },
                "get": [
                    "title",
                    "album",
                    "album-artist",
                    "track-number",
                    "uuid"
                ]
            }
        ]
    }

Import media files into the library, and extract their metadata:

    {
        "import": [
            {
                "query": "~/Music/iTunes/Music/**/*.mp3",
                "type": "wildcard"
            }
        ],
        "songs": [
            {
                "filter": {
                    "!all": {
                        "query": true,
                        "type": "missing"
                    }
                },
                "extract": [
                    "!all"
                ]
            }
        ]
    }

Add metadata to all songs missing it, and embed:

    {
        "songs": [
            {
                "filter": {
                    "album-artist": {
                        "query": true,
                        "type": "missing"
                    }
                },
                "set": {
                    "album-artist": "Unknown"
                },
                "embed": [
                    "!all"
                ]
            }
        ]
    }

Fully synchronize disk state to match metadata:

    {
        "songs": [
            {
                "embed": true,
                "rename": true
            }
        ]
    }

Response if some songs have missing files:

    {
        "success": false,
        "errors": [
            {
                "reason": "missing-files",
                "error": "7 files were missing on disk"
                "files": [
                    "C418/Dief/01 Texture Prayers.mp3",
                        ...
                    "C418/Dief/07 Match Cut.mp3"
                ]
            }
        ]
    }

Check that all files are present:

    {
        "songs": [
            {
                "check": true
            }
        ]
    }

Response in case of missing files is same as above; response in case
of all files present:

    {
        "songs": [
            [
                {},
                    ...
                {}
            ]
        ]
    }
