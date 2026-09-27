# Humbly Plural Publishing Guide

This guide helps you publish the Windows version of Humbly Plural and prepare for future mobile releases.

## 1. Verify the Windows build

1. Run the app from `dist\HumblyPlural.exe`.
2. Confirm the fronting screen works and all core features behave as expected.
3. Use `test_app.py` if you want a quick smoke test:

```powershell
python test_app.py
```

## 2. Package the release

Use the provided script to create a zip package with the executable and documentation.

```powershell
.\package_release.ps1
```

This creates a file like `HumblyPlural-Windows-YYYYMMDD.zip` in the repository root.

## 3. Package for app stores and direct distribution

For Windows distribution, use the packaged zip or standalone executable.

### Direct distribution
- Use `HumblyPlural.exe` or the packaged zip.
- Host files on your own website or a file-sharing service.
- Share a direct download link instead of relying on a public GitHub release.

### Windows store options
- Microsoft Store: prepare a Win32 app package and submit it through Partner Center.
- Itch.io: use the ZIP or standalone EXE for easy indie distribution.
- Share your store link with your community.

## 4. Publish to community download locations

### Recommended options
- Your own website or blog
- Cloud storage link (Google Drive, Dropbox, OneDrive)
- Discord/Telegram/Matrix community channels
- Itch.io or similar indie distribution sites

### Alternative download options
- Your website or blog
- Discord/Telegram/Matrix community channels
- Itch.io or similar indie distribution sites
- Cloud storage link (Google Drive, Dropbox, OneDrive)

## 5. Create a simple install note for users

Ask users to:
1. Download `HumblyPlural.exe` or the zip file.
2. Run `HumblyPlural.exe`.
3. If using the zip, extract it first and then run the executable.

## 6. Future mobile publishing

### Android
- Build an APK on Linux or WSL using Buildozer and Kivy.
- Create a Google Play Developer account.
- Prepare screenshots and a privacy policy.

### iOS
- Build an IPA on macOS using `kivy-ios`.
- Enroll in Apple Developer Program.
- Submit through App Store Connect.

## 7. Recommended release metadata

- App name: **Humbly Plural**
- Short description: "Private plural system manager with member tracking, fronting logs, journal notes, and stats."
- Category: Productivity / Wellness
- Privacy note: "No internet access or remote data collection. Data is stored locally in JSON files."

---

If you want, I can also create the exact GitHub release notes text and a short community announcement message. 