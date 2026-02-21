(with-eval-after-load 'exec-path-from-shell
  (setq exec-path-from-shell-arguments (delete "-i" exec-path-from-shell-arguments)))

;; Allow unsigned packages (works around GNU ELPA signature verification failures)
(with-eval-after-load 'package
  (setq package-check-signature nil))

;; Disable Prelude's default zenburn theme — dracula is loaded in personal/init.el
(setq prelude-theme nil)
