# Corporate & Secret Items — EXCLUDED

## Corporate Artifacts Found

### Git Config
- `[user] email = ianderson@expediagroup.com`
- `[credential "https://github.expedia.biz"]` with gh auth helper
- `[credential "https://dev.azure.com"]` with useHttpPath

### GitHub CLI
- `~/.config/gh/hosts.yml` — configured host `github.expedia.biz`, user `ianderson_expedia`

### ~/bin Scripts (4 flagged)
| Script | Reference |
|--------|-----------|
| aql | `artylab.expedia.biz` |
| asset-import | `dsrs.expedia.biz/flows/trigger/...` |
| git-report | `@expediagroup.com` email fallback (line 174) |
| rotate-artifactory-auth | `artylab.expedia.biz`, `artifactory-edge.expedia.biz` |

### ~/bin Symlinks to Corporate Projects (40+ scripts)
All symlinks into `~/src/ops-metrics/`, `~/src/hillia/`, `~/src/ms-graph/`,
`~/src/dsrs-scripts/`, `~/src/cyclops/` — entirely corporate.

### .config/ Corporate Items
| Path | Content |
|------|---------|
| `.config/egctl.yaml` | Expedia partner API credentials |
| `.config/okta-auth/sessions/` | Cached Okta session tokens for `expediagroup.oktapreview.com` |
| `.config/hillia/` | Hillia project tracking config |
| `.config/schema-deploy-auth/` | Corporate deployment auth |

### Home Directory
- `OneDrive - Expedia Group/` directory
- `.zcompdump.EXPFVFGG04ZQ05Q.*` files (hostname reveals corporate machine)

### Homebrew — Corporate Packages
aws-sam-cli, awscli, azure-cli, cfn-lint, egctl, helm, mongocli, mongosh,
saml2aws, teleport, terraform-docs, vault, android-commandlinetools,
android-ndk, android-platform-tools, expo-orbit

## Secrets Found

### HIGH — Plaintext Credentials
| Location | Secret Type |
|----------|-------------|
| `~/bin/dsrs-env` (symlink) | Hardcoded DB password: `26329a1f-...` for `designresource_appuser` on AWS RDS |
| `~/.npmrc` | Base64-encoded Artifactory auth tokens for `artylab.expedia.biz` |
| `~/.config/okta-auth/sessions/` | Okta `stateToken` and `sessionToken` for `s-egds-rsc-service@expediagroup.com` |

### LOW — Credential Helper References (no actual secrets)
| Location | Type |
|----------|------|
| `.gitconfig` | Credential helper paths (gh, gcm-core, osxkeychain) |
| `.gitconfig` | SSH signing key (public key, not private) |

### Not Found
- No `export.*KEY=`, `export.*TOKEN=`, `export.*SECRET=` in shell configs
- No `.env` files with real secrets (only a `.env.example` in postgres-project)
- No `.pem` or `.key` files (the one `.key` found was a Keynote presentation)

## Summary

All corporate items are accounted for and will be excluded from the dotfiles repo.
The 3 high-severity secrets are on the old laptop volume only — none are in the
current dotfiles repo. No secrets will be committed.
