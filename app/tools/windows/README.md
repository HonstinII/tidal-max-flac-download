Place a redistributable FLAC tools archive at `flac.zip` to enable the
Windows "Use bundled FLAC tools" setup option.

The archive should contain `metaflac.exe` either at the archive root or inside
a `bin/` directory. The app extracts it into the user-local managed tools
folder and adds that folder to the runtime search path.
