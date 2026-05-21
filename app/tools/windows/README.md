`flac.zip` is the official FLAC 1.5.0 Windows tools archive from Xiph.org:

```text
https://github.com/xiph/flac/releases/download/1.5.0/flac-1.5.0-win.zip
```

It contains `metaflac.exe`, `flac.exe`, and the upstream license files. The app
uses it only for the optional cover-embedding flow, extracts it into the
user-local managed tools folder, and adds that folder to the runtime search path.
