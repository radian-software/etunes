# Preview

Specify the location of `library.yml`, otherwise `etunes` recurses
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

# Specification

`etunes` is a command-line utility for managing a media library.

## Command-line interface

Describe usage:

    $ etunes [help | -h | -help | --help | -?]

For most operations `etunes` requires a library file, which is in YAML
format. This can be specified by the flag `--library=<library.yml>`,
or the environment variable `$ETUNES_LIBRARY`. If neither is given
then `etunes` aborts.

Create a new `library.yml` file with defaults:

    $ etunes init

## Query subcommand

Usage:

    $ etunes query [<json> | @query.json | -]

Response is output to stdout in JSON format. Return code is always 0
except in the case of an internal error in `etunes`. Malformed or
failed queries can be detected by inspecting the JSON response.

## Query JSON format

Query JSON is a list of subqueries. Subqueries are maps. The `type`
key of a subquery determines how the other keys are interpreted.

### Response format

The response JSON is always a map. Key `success` is a boolean for
whether the query was completed successfully. Key `in-progress` is a
boolean for whether the query made some changes before failing, and
needs to be either completed or reverted. Key `error-type` is a string
identifying the type of error that occurred, or null (if query
succeeded). The values of this key are considered to be part of the
API. Key `error-message` is a string explaining the error that
occurred, or null (if query succeeded). Key `response` is a list of
responses from the subqueries, or null (if query failed).

### Options subqueries

Type `options` indicates operation on library-wide options. Key `get`
is a list of options to get the values of (defaults to all options).
Missing options are reported with their default values. Key `set` is a
map of options to their values (defaults to no options). These options
are updated to the values given. Key `current` is a map of options to
current values. If any of the options do not currently have the values
specified then the query fails. Invalid option names or values cause
the query to fail. The response is a list of the values of options
requested by the `get` key (may be empty).

### Songs subqueries

Type `songs` indicates operation on song metadata (YAML or ID3). Key
`get` is a list of metadata fields to return for each song matched by
the query (defaults to all fields). Unset fields are considered to be
null. Key `set` is a map from metadata fields to values to set for
those metadata fields, for each song matched by the query. Null values
mean to unset those metadata fields. Key `current` is a map of
metadata fields to current values. If any song matched by the query
has a value for one of those metadata fields which does not match the
value given in `current` then the query fails. Key `extract` is a list
of metadata fields to set from embedded ID3 (defaults to none). Key
`embed` is a list of metadata fields to write into embedded ID3
(defaults to none). `extract` and `set` must not have any fields in
common, and likewise `extract` and `embed` must not have any fields in
common. However `set` and `embed` may share keys, in which case the
values given by `set` will be written into the YAML and also embedded.
Key `filter` is a list of filters, which are maps. Filter maps have
keys `field`, `value`, and `operation`. Key `field` specifies the
metadata field to filter on. Key `value` is the value to compare
against. Key `operation` specifies how to compare the given value and
the song's value to determine if the song is matched by the filter or
not (defaults to `equal`, *no other operations defined yet*). If no
filters are specified (the default) then the query matches all songs
in the library. If query matches no songs, it fails, unless boolean
key `allow-no-matches` is true. Response is a list of songs matched by
the query, which are maps with the keys specified by `get`, unless
boolean key `quiet` is true, in which case response is the number of
songs matched. The values reflect any updates by `set`.

# Query specification

A query is a single JSON map. This map is keyed by object type
(option, song). Each subpart matches some set of the object in
question (controlled by filters), and then performs an operation on
all of them. Here is an example query:

    {
        "options": [
            {
                "name": "deduplication-threshold",
                "set": "0.75"
            },
            {
                "name": "media-directory"
            }
        ],
        "media"
    }

And the resulting response could be:

    {
        "success": true,
        "options": [
            {
                "name": "deduplication-threshold",
                "value": "0.75",
                "set": "0.75"
            },
            {
                "name": "media-directory",
                "value": "media"
            }
        ]
    }

Errors that could occur:

    {
        "success": false,
        "errors": [
            {
                "type": "option/does-not-exist",
                "name": "duplication-threshold",
                "message": "option does not exist: duplication-threshold"
            }
        ]
    }
