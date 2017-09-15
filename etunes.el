;;; etunes.el --- Declarative music library manager. -*- lexical-binding: t -*-

;; Copyright (C) 2017 Radon Rosborough

;; Author: Radon Rosborough <radon.neon@gmail.com>
;; Homepage: https://github.com/raxod502/etunes
;; Keywords: extensions
;; Created: 13 Sep 2017
;; Package-Requires: ((emacs "25"))

;;; Commentary:

;; FIXME

;;; Code:

;; To see the outline of this file, run M-x outline-minor-mode and
;; then press C-c @ C-t. To also show the top-level functions and
;; variable declarations in each section, run M-x occur with the
;; following query: ^;;;;* \|^(

;;;; Libraries

(require 'let-alist)

;;;; Customization group

(defgroup etunes nil
  "The declarative, version-controlled music library manager."
  :group 'applications
  :prefix "etunes-")

;;;; Directory handling
;;;;; Path user options

(defcustom etunes-dir "etunes/"
  "The directory for etunes to store data.
This path is expanded relative to `user-emacs-directory', but it
can be absolute instead. The trailing slash is recommended but
not necessary."
  :type 'directory
  :group 'etunes)

(defcustom etunes-media-dir "media/"
  "The directory for etunes to store media files.
This path is expanded relative to `etunes-dir', but it can be
absolute instead. The trailing slash is recommended but not
necessary."
  :type 'directory
  :group 'etunes)

(defcustom etunes-metadata-dir "metadata/"
  "The directory for etunes to store media metadata.
This path is expanded relative to `etunes-dir', but it can be
absolute instead. The trailing slash is recommended but not
necessary."
  :type 'directory
  :group 'etunes)

(defcustom etunes-playlist-dir "playlists/"
  "The directory for etunes to store playlists.
This path is expanded relative to `etunes-dir', but it can be
absolute instead. The trailing slash is recommended but not
necessary."
  :type 'directory
  :group 'etunes)

;;;;; Path utility functions

(defun etunes-path-join (base &rest segments)
  "Add to BASE some additional path SEGMENTS.
If no SEGMENTS are given, the result is BASE. Otherwise, the
first SEGMENT is passed to `expand-file-name' with a
`default-directory' of BASE; then the second SEGMENT is passed
using a `default-directory' of the result of the previous step;
and so on until all the SEGMENTS are exhausted. In this way, any
of the SEGMENTS can be either relative or absolute. Trailing
slashes for intermediate directories are recommended but not
necessary."
  (if segments
      (apply #'etunes-path-join
             (expand-file-name (car segments) base)
             (cdr segments))
    base))

;;;;; Path generation

(defun etunes-default-media-filename-format (metadata)
  "Default value for `etunes-media-filename-format'.
It returns values like \"<album>/<disk>-<track>-<name>.<ext>\".
METADATA is the metadata alist for the track whose filename is
being generated."
  (let-alist metadata
    (concat .album-name "/"
            (when .disk-number
              (number-to-string .disk-number))
            (when (and .disk-number .track-number) "-")
            (when .track-number
              (number-to-string .track-number))
            (when (or .disk-number .track-number) "_")
            .track-name "." .filetype)))

(defcustom etunes-media-filename-format
  #'etunes-default-media-filename-format
  "How to generate the filenames of music files.
This function is called with the metadata alist of a track, and
it should return a string that is the path of the file for that
track. The returned path is recommended to be relative, but this
is not required. It is expanded relative to `etunes-media-dir'."
  :type '(choice
          (const etunes-default-media-filename-format
                 :tag "Default format")
          (function :tag "Custom format")))

;;;; Closing remarks

(provide 'etunes)

;;; etunes.el ends here

;; Local Variables:
;; outline-regexp: ";;;;* "
;; End:
