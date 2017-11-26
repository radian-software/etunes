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
(require 'subr-x)

;;;; User options

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

(defcustom etunes-artwork-dir "artwork/"
  "The directory for etunes to store album artwork files.
This path is expanded relative to `etunes-dir', but it can be
absolute instead. The trailing slash is recommended but not
necessary.")

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

(defcustom etunes-metadata-format 'yaml
  "The format in which to store `etunes' metadata.
This may be either `json' or `yaml'."
  :type '(choice
          (const :tag "JSON" json)
          (const :tag "YAML" yaml))
  :group 'etunes)

(defcustom etunes-user-plugin-file "etunes_plugin.py"
  "File containing the user-defined `etunes' plugin, if any.
This path is expanded relative to `etunes-dir', but it can be
absolute instead."
  :type 'file
  :group 'etunes)

;;;; Path variables

(defvar etunes-source-directory
  (file-name-directory (file-truename (or load-file-name buffer-file-name)))
  "The directory containing `etunes' source code.
This is used to locate the backend script.")

(defvar etunes-backend-script
  (expand-file-name "etunes.py" etunes-source-directory)
  "The fully qualified name of the backend script for `etunes'.")

;;;; Backend invocation

(defun etunes-raw-invoke-backend (&rest args)
  "Call `etunes-backend-script' with ARGS, and return output as a string."
  (with-temp-buffer
    (apply #'call-process etunes-backend-script nil t nil args)
    (let ((resp (buffer-string))
          (prefix "ok\n"))
      (unless (string-prefix-p prefix resp)
        (error "Malformed response from backend script: %s" resp))
      (substring resp (length prefix)))))

(defun etunes-invoke-backend (&rest args)
  "Call `etunes-backend-script' with ARGS and default parameters.
Return output as a string."
  (apply #'etunes-raw-invoke-backend
         (concat "--emacs-dir=" (expand-file-name user-emacs-directory))
         (concat "--etunes-dir=" (expand-file-name etunes-dir))
         (concat "--etunes-artwork-dir=" (expand-file-name etunes-artwork-dir))
         (concat "--etunes-media-dir=" (expand-file-name etunes-media-dir))
         (concat "--etunes-metadata-dir="
                 (expand-file-name etunes-metadata-dir))
         (concat "--file-extension="
                 (pcase etunes-metadata-format
                   (`json ".json")
                   (`yaml ".yml")
                   (`nil (error "Unexpected metadata format: %S"
                                etunes-metadata-format))))
         (concat "--user-plugin-file=" etunes-user-plugin-file)
         args))

;;;; Closing remarks

(provide 'etunes)

;;; etunes.el ends here

;; Local Variables:
;; outline-regexp: ";;;;* "
;; End:
