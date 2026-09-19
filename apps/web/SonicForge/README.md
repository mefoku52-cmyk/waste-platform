# SonicForge Audio Studio

Offline-first Android audio editor: 16-bit PCM WAV import, real processing
(gain, normalize, compressor, limiter, high-pass, fades) and WAV export.
Compose/Material 3 UI, waveform rendering, unit tests.

## Build (JDK 17)

    gradle wrapper --gradle-version 8.9
    ./gradlew test
    ./gradlew assembleDebug

APK: app/build/outputs/apk/debug/app-debug.apk

Install:

    adb install -r app/build/outputs/apk/debug/app-debug.apk

## Scope

The engine intentionally supports 16-bit PCM WAV. MP3/AAC/FLAC/OGG export
requires a native codec layer (e.g. FFmpeg) and is not faked in this build.

## License

Project template — add your chosen distribution license before publishing.
