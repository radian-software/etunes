;;; etunes.el --- Declarative music library manager. -*- lexical-binding: t -*-

;; Copyright (C) 2017 Radon Rosborough

;; Author: Radon Rosborough <radon.neon@gmail.com>
;; Homepage: https://github.com/raxod502/etunes
;; Keywords: extensions
;; Created: 13 Sep 2017

;;; Commentary:

;; FIXME

;;; Code:

;; To see the outline of this file, run M-x outline-minor-mode and
;; then press C-c @ C-t. To also show the top-level functions and
;; variable declarations in each section, run M-x occur with the
;; following query: ^;;;;* \|^(

(defgroup etunes nil
  "The declarative, version-controlled music library manager."
  :group 'applications
  :prefix "etunes-")

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

;;;; Closing remarks

(provide 'etunes)

;;; etunes.el ends here

;; Local Variables:
;; outline-regexp: ";;;;* "
;; End:
