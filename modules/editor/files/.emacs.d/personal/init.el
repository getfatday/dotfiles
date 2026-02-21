;; No Line Numbers
(global-display-line-numbers-mode -1)
;; No Menu Bar
(menu-bar-mode -1)

;;(add-to-list `exec-path-from-shell-arguments `"-i")

;;(setq exec-path-from-shell-arguments (delete "-i" exec-path-from-shell-arguments) )

(when (daemonp)
  (exec-path-from-shell-initialize))

(require 'server)
;; delete server socket settings
;; (setq delete-by-moving-to-trash nil)

;; some systems don't auto-detect the socket dir, so specify it here and for the client:
;; (setq server-socket-dir "~/.emacs.d/server")
(server-start)

(add-to-list 'package-archives
    '("melpa" . "http://melpa.milkbox.net/packages/") t)
(add-to-list 'package-archives
    '("marmalade" . "http://marmalade-repo.org/packages/") t)

;;(setq el-get-dir "~/.emacs.d/personal/el-get/el-get")
;;(add-to-list 'load-path el-get-dir)

;;(unless (require 'el-get nil 'noerror)
;;  (with-current-buffer
;;      (url-retrieve-synchronously
;;       "https://raw.github.com/dimitri/el-get/master/el-get-install.el")
;;    (goto-char (point-max))
;;    (eval-print-last-sexp)))

;;(add-to-list 'el-get-recipe-path "~/.emacs.d/personal/recipes")
;;(el-get 'sync)

;; Setup mouse for iTerm2
(require 'mouse)
(xterm-mouse-mode t)
(defun track-mouse (e))

;; Setup Mouse Scrolling
;; Enable mouse support
(unless window-system
  (require 'mouse)
  (xterm-mouse-mode t)
  (global-set-key [mouse-4] '(lambda ()
                              (interactive)
                              (scroll-down 1)))
  (global-set-key [mouse-5] '(lambda ()
                              (interactive)
                              (scroll-up 1)))
  (defun track-mouse (e))
  (setq mouse-sel-mode t)
)

;; Set default charset and language
(prefer-coding-system 'utf-8)
(set-default-coding-systems 'utf-8)
(set-terminal-coding-system 'utf-8)
(set-keyboard-coding-system 'utf-8)
(set-language-environment 'utf-8)

;; Custom key binding
(global-set-key [remap other-window] 'other-window)

;; Prevent Autosave

;disable backup
(setq create-lockfiles nil)
(setq backup-directory-alist `(("." . "~/.saves")))
(setq backup-by-copying t)
(setq delete-old-versions t
  kept-new-versions 6
  kept-old-versions 2
  version-control t)

;disable clean whitespace
(setq prelude-clean-whitespace-on-save nil)

;whitespace style
(setq whitespace-style '(face tabs trailing lines space-before-tab newline indentation empty space-after-tab tab-mark newline-mark))
(setq whitespace-style '(face empty trailing lines-tail))

(setq whitespace-display-mappings
      ;; all numbers are Unicode codepoint in decimal. ⁖ (insert-char 182 1)
      '(
        (space-mark 32 [183] [46]) ; 32 SPACE 「 」, 183 MIDDLE DOT 「·」, 46 FULL STOP 「.」
        (newline-mark 10 [8629 10]) ; 10 LINE FEED
        (tab-mark 9 [9654 9] [92 9]) ; 9 TAB, 9655 WHITE RIGHT-POINTING TRIANGLE 「▷」
      ))

;; Rebind set-mark-command to M-Space
(global-set-key (kbd "M-SPC") 'set-mark-command)

;; Dracula theme
(prelude-require-package 'dracula-theme)
(load-theme 'dracula t)

;; Visual Bell
(setq visible-bell 'top-bottom)

;; Hide the menu bar
(menu-bar-mode -1)

;; Setup window transparency hook
(set-frame-parameter (selected-frame) 'alpha '(85 50))
(add-to-list 'default-frame-alist '(alpha 85 50))

(defun osx-pbcopy (beg end)
  "Copies region to OSX Clipboard"
  (shell-command-on-region beg end "pbcopy")
  )

(defun osx-kill-ring-save (beg end)
  "Wrap kill-ring-save and save to OSX Clipboard"
  (interactive "r")
  (osx-pbcopy beg end)
  (kill-ring-save beg end)
  )

(defun osx-kill-region (beg end)
  "Wrap kill-ring-save and save to OSX Clipboard"
  (interactive "r")
  (osx-pbcopy beg end)
  (kill-region beg end)
  )

;; Modes
(add-to-list 'interpreter-mode-alist
    '("node" . js3-mode)
    )

(add-to-list 'auto-mode-alist
    '("gradle" . groovy-mode)
    )

;; Key Bindings
;; Bind kill-ring-save and kill-region wrappers
(global-set-key (kbd "C-w") 'osx-kill-ring-save)
(global-set-key (kbd "M-w") 'osx-kill-region)

(global-set-key (kbd "ESC <down>") 'forward-sentence)
(global-set-key (kbd "ESC <up>") 'backward-sentence)


;; Start Sauron
;; (sauron-start)

;; Disable prompts
(fset 'yes-or-no-p 'y-or-n-p)           ; replace y-e-s by y
(defadvice yes-or-no-p (around prevent-dialog activate)
  "Prevent yes-or-no-p from activating a dialog"
  (let ((use-dialog-box nil))
    ad-do-it))
(defadvice y-or-n-p (around prevent-dialog-yorn activate)
  "Prevent y-or-n-p from activating a dialog"
  (let ((use-dialog-box nil))
    ad-do-it))
(defadvice message-box (around prevent-dialog activate)
  "Prevent message-box from activating a dialog"
  (apply #'message (ad-get-args 0)))
(setq use-dialog-box nil)
(setq flymake-gui-warnings-enabled nil)

(defun kill-other-buffers ()
    "Kill all other buffers."
    (interactive)
    (mapc 'kill-buffer
          (delq (current-buffer)
                (remove-if-not 'buffer-file-name (buffer-list)))))

;; Create a SUDO handle to SSH as sudo
(set-default 'tramp-default-proxies-alist (quote ((".*" "\\`root\\'" "/ssh:%h:"))))

;; Always follow symbolic links
(setq vc-follow-symlinks t)
