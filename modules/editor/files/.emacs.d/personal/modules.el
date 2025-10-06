;; Typescript Extension
(require 'prelude-ts)
(require 'web-mode)

;; aligns annotation to the right hand side
(setq company-tooltip-align-annotations t)

;; formats the buffer before saving
;;(add-hook 'before-save-hook 'tide-format-before-save)

;;(add-hook 'typescript-mode-hook #'setup-tide-mode)

(add-to-list 'auto-mode-alist '("\\.tsx\\'" . web-mode))
(add-hook 'web-mode-hook
  (lambda ()
    (when (string-equal "tsx" (file-name-extension buffer-file-name))
      (prelude-ts-mode-defaults))))
;; enable typescript-tslint checker
(flycheck-add-mode 'typescript-tslint 'web-mode)

;; Associate .jsonl files with json-mode
(add-to-list 'auto-mode-alist '("\\.jsonl\\'" . json-mode))

;; Grammarly Hooks
(use-package lsp-grammarly
  :ensure t
  :hook (text-mode . (lambda ()
                       (require 'lsp-grammarly)
                       (lsp))))

(add-hook 'typescript-mode-hook
  (lambda ()
    (local-set-key (kbd "C-x f") 'tide-fix)))
