# Preview

Specific the location of `library.yml`, otherwise `etunes` recurses
upwards from the working directory to find it.

    $ etunes --library=<library.yml> ...

Manipulate global options:

    $ etunes get-option media-directory
    media
    $ etunes set-option deduplication-threshold 0.75
    $ etunes set-option user-plugin-file plugins/user_plugin.py

Make queries against the song database:

    $ etunes query [--file=<query.json> | --json={...}]

Get information about a song (query):

    [
      {
        "filter": {
          "album": "2 years of failure",
          "track": "5"
        },
        "get": ["artist", "disk", "year"]
      }
    ]

Get information about a song (response):

    {
      "success": true,
      "data": [
        [
          {
            "artist": "C418",
            "disk": "1",
            "year": "2016"
          }
        ]
      ]
    }

Update album metadata (query):

    [
      {
        "filter": {
          "album": "Final Fantasy VII"
        },
        "set": {
          "sort-album": "Final Fantasy 7"
        }
      }
    ]

Update album metadata (response):

    {
      "success": true,
      "data": [[]]
    }

Error responses:

    {
      "success": false,
      "error-type": "malformed-query",
      "error-message": "subquery 3 is a vector, but should be a map"
    }

    {
      "success": false,
      "error-type": "no-matches",
      "error-message": "subquery 1 matched no songs, but specified 'require-match'"
    }

    {
      "success": false,
      "error-type": "malformed-database",
      "error-message": "database file '<library.yml>' at path 'options' > 'deduplication-threshold' has string, but should have float"
    }
