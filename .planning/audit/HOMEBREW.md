# Homebrew Audit

**Source:** `/Volumes/Macintosh HD-1/opt/homebrew/` (Apple Silicon)

## Old Laptop — Formulae (Cellar)

ada-url, ansible, aom, aribb24, asdf, aspell, autojump, aws-sam-cli, awscli,
azure-cli, bash, bdw-gc, brotli, c-ares, ca-certificates, cairo, certifi, cffi,
cfn-lint, cjson, cryptography, csvkit, dav1d, deno, docker, docker-completion,
docker-compose, docker-machine, docutils, dos2unix, editorconfig, egctl, emacs,
expat, fdupes, ffmpeg, flac, fmt, fontconfig, freetype, frei0r, fribidi, fzf,
gdbm, gdk-pixbuf, gemini-cli, gettext, gh, giflib, git, git-delta,
git-filter-repo, git-flow, git-quick-stats, glib, gmp, gnu-sed, gnupg, gnutls,
go, gobject-introspection, gogcli, gpgme, gpgmepp, graphite2, guile, gum,
harfbuzz, hdrhistogram_c, helm, highway, himalaya, ical-buddy, icu4c@75,
icu4c@76, icu4c@78, imagemagick, imath, jasper, jpeg, jpeg-turbo, jpeg-xl, jq,
keyring, krb5, lame, leptonica, libarchive, libass, libassuan, libb2, libbluray,
libcbor, libde265, libdeflate, libevent, libfido2, libgcrypt, libgit2, libgpg-error,
libheif, libidn2, libksba, liblqr, libmagic, libmicrohttpd, libnghttp2, libnghttp3,
libngtcp2, libogg, libomp, libpng, libraw, librist, librsvg, libsamplerate,
libsndfile, libsodium, libsoxr, libssh, libssh2, libtasn1, libtiff, libtool,
libultrahdr, libunibreak, libunistring, libusb, libuv, libvidstab, libvmaf,
libvorbis, libvpx, libx11, libxau, libxcb, libxdmcp, libxext, libxml2,
libxrender, libyaml, libzip, little-cms2, llhttp, llvm, lpeg, lua, luajit, luv,
lz4, lzo, m4, mas, mbedtls, mongocli, mongosh, mpdecimal, mpg123, ncurses,
neovim, nettle, nginx, node, npth, nspr, nss, obsidian-cli, oniguruma,
opencore-amr, openexr, openjdk, openjpeg, openjph, openssl@1.1, openssl@3, opus,
p11-kit, pango, pcre, pcre2, peekaboo, pinentry, pinentry-mac, pixman, pkgconf,
pkl, pnpm, poppler, popt, postgresql@14, pv, pycparser, python-certifi,
python-cryptography, python-packaging, python@3.10, python@3.11, python@3.12,
python@3.13, python@3.14, python@3.9, rav1e, readline, reattach-to-user-namespace,
remindctl, rename, rsync, rubberband, ruby, rust, saml2aws, sdl2,
shared-mime-info, simdjson, snappy, sops, speex, sqlite, srt, ssh-copy-id, stow,
streamlink, summarize, supabase, svt-av1, teleport, terraform-docs, tesseract,
the_silver_searcher, theora, things.sh, tmux, tree-sitter, unbound, unibilium,
utf8proc, uv, uvwasi, vault, vim, webp, wget, x264, x265, xcodegen, xorgproto,
xvid, xxhash, xz, yarn, ykman, yq, z, z3, zeromq, zimg, zlib, zplug, zsh,
zsh-history-substring-search, zstd

## Old Laptop — Casks (Caskroom)

1password, 1password-cli, alfred, android-commandlinetools, android-ndk,
android-platform-tools, autodesk-fusion, autodesk-fusion360, bartender,
chatgpt-atlas, chromedriver, dropbox, expo-orbit, firefox, flux, flux-app,
git-credential-manager, handbrake, handbrake-app, iterm2, karabiner-elements,
licecap, macdown, marked, marked-app, neo4j, neo4j-desktop, ngrok, obsidian,
sequel-ace, sublime-text, visual-studio-code

## Current Dotfiles — Declared Packages

| Module | Formulae | Casks |
|--------|----------|-------|
| git | git, git-delta, gh, git-flow | kdiff3, google-chrome |
| zsh | zsh, zsh-history-substring-search | — |
| node | asdf, node, pnpm | — |
| editor | emacs, vim, neovim | — |
| productivity | autojump, z, fzf | — |
| docker | docker, docker-compose, docker-machine | — |
| macos | mas | — |
| speckit | uv | — |
| example | tree, htop | — |
| 1password | — | 1password |
| alfred | — | alfred |
| chatgpt | — | chatgpt |
| chrome | — | google-chrome |
| claude | — | claude |
| cursor | — | cursor |
| grammarly | — | grammarly-desktop |
| handbrake | — | handbrake |
| iterm | — | iterm2 |
| obsidian | — | obsidian |
| spotify | — | spotify |

## Gap Analysis — On Old Laptop, NOT in Dotfiles

### Formulae worth adding
- **ffmpeg** — media processing (many deps come with it)
- **go** — Go language
- **imagemagick** — image processing
- **jq** — JSON processor
- **nginx** — web server
- **postgresql@14** — database
- **rust** — Rust language
- **stow** — GNU Stow (used by the dotfiles system itself!)
- **tmux** — terminal multiplexer
- **wget** — HTTP fetcher
- **gnupg, pinentry-mac** — GPG/signing
- **sops** — secret management
- **streamlink** — stream extraction
- **rename** — batch file rename
- **rsync** — file sync
- **dos2unix** — line ending conversion
- **git-filter-repo** — git history rewriting
- **git-quick-stats** — git statistics
- **things.sh** — Things 3 CLI
- **ical-buddy** — calendar CLI
- **obsidian-cli** — Obsidian CLI
- **reattach-to-user-namespace** — tmux clipboard fix
- **gnu-sed** — GNU sed

### Casks worth adding
- **karabiner-elements** — keyboard customization (has config on old laptop)
- **firefox** — browser
- **ngrok** — tunneling
- **visual-studio-code** — editor
- **sequel-ace** — database GUI
- **flux** — blue light filter
- **bartender** — menu bar management
- **dropbox** — cloud storage
- **licecap** — screen recording

### Corporate/Skip
- aws-sam-cli, awscli, azure-cli — cloud CLIs (corporate context)
- cfn-lint — CloudFormation linter (corporate)
- egctl — Expedia tool
- helm, teleport, vault — infrastructure (corporate context)
- saml2aws — SAML auth (corporate)
- terraform-docs — infrastructure docs (corporate)
- mongocli, mongosh — MongoDB (corporate)
- android-commandlinetools, android-ndk, android-platform-tools — Android dev (corporate)
- git-credential-manager — replaced by gh auth
- 1password-cli — installed separately via 1Password module
- chromedriver — testing tool (install on demand)
- autodesk-fusion/fusion360, neo4j/neo4j-desktop — specialized (install on demand)
- expo-orbit — React Native (corporate)
- chatgpt-atlas — old ChatGPT cask name
- marked/marked-app, macdown — markdown editors (install on demand)
- sublime-text — replaced by Cursor/VS Code
