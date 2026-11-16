# Project instructions

## Version updates and GitHub synchronization

The user requires automatic GitHub synchronization whenever a new client version is produced. Do not ask again for permission to synchronize routine project updates to the existing private repository `angel20009123/mask_s`.

For each functional update:

1. Increment `version.py` using semantic versioning; update the README version and `CHANGELOG.md`.
2. Run relevant calculation and UI checks, then build the versioned Windows executable with `python build.py` and verify it starts.
3. Commit the source, push `main` to the existing `origin`, and push the corresponding new `vX.Y.Z` tag. Never move an existing published tag.
4. The tag triggers `.github/workflows/release.yml`, which tests, builds, and publishes the EXE as a GitHub Release attachment.
5. Check the workflow and confirm the release contains the versioned EXE. If a build or publication fails, investigate and fix it; report any concrete unresolved blocker. Do not claim a release is available before verifying its attachment.
6. Provide the local versioned executable link and verified GitHub release link in the final reply.

Keep the repository private. Keep build outputs out of Git; deliver EXEs through Releases. Documentation-only changes do not need a new application version or tag, but still need to be committed and pushed.
