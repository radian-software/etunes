**eTunes**: the declarative, version-controlled music library manager
for Emacs.

## Summary

eTunes attempts to provide a similar user experience to the popular
music player iTunes, except (1) inside Emacs and (2) not terrible.
eTunes is unique because it provides for a declarative,
version-controlled music library. The user, however, need not be aware
of this and can use eTunes just like they would use iTunes, if they so
choose.

The eTunes model is based on storing metadata externally to media
files, and taking that external metadata to be the source of truth.
This allows for tracking the evolution of your music library using
robust version-control tools such as Git, with good old plain-text
diffs. Metadata is stored in YAML format, in an easy-to-understand
file hierarchy.

The most important music management commands for eTunes are the
*synchronization* commands. These allow you to interactively resolve
differences between eTunes' external metadata and the actual
filenames and ID3 tags on your media, thus ensuring that your external
metadata is an accurate reflection of your library (or, depending on
your perspective, that your library is an accurate reflection of your
carefully curated metadata).

But eTunes of course also provides many of the trappings of a standard
media player:

* playing your music, of course
* browse music by album, artist, year, or other tags
* search, sort, and filter songs and albums by metadata
* perform individual and bulk editing of metadata
* in a graphical Emacs, attractive displaying of album art
* creation and management of playlists
* programmatic API for massive automated refactoring of your library,
  directly in Emacs Lisp
* no binary data except your music files (which are treated as
  second-class citizens with regard to metadata)
