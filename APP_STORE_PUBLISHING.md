# Humbly Plural App Store Publishing Guide

This document helps you prepare and publish Humbly Plural to app stores.

## Local GitHub disconnect

The local repository has been disconnected from GitHub to prevent accidental pushes.

## 1. Windows distribution

### Option 1: Direct download
- Provide `dist\HumblyPlural.exe` or the zip package to users.
- Host on a personal website or cloud storage.
- Tell users to download and run the executable.

### Option 2: Microsoft Store
- Create a Microsoft Partner Center account.
- Package the app as a Win32 app.
- Requirements:
  - App manifest and icons
  - Signed executable
  - Privacy policy text
- Submit the package through Partner Center.

### Option 3: Itch.io
- Create an itch.io account.
- Upload `HumblyPlural.exe` or `HumblyPlural-Windows-YYYYMMDD.zip`.
- Provide a short description and screenshots.

## 2. Android publishing

### Build environment
- Use Linux or WSL for Buildozer.
- Install required Android SDK/NDK components.

### Set up WSL and Ubuntu
1. In Windows PowerShell as admin, run:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Open Ubuntu and update packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv git zip unzip openjdk-17-jdk build-essential
   ```
3. Install Buildozer and Kivy in your WSL home:
   ```bash
   python3 -m pip install --user --upgrade pip
   python3 -m pip install --user buildozer Cython kivy
   ```
4. Add the local pip binary folder to your path if needed:
   ```bash
   echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

### Build steps
1. From Ubuntu, open your project folder mounted from Windows:
   ```bash
   cd /mnt/c/src/GitHub/bracekings/tictactoe
   ```
2. Run a debug build first:
   ```bash
   ./build_android.sh
   ```
3. Confirm the APK builds and the app works when installed on your device.
4. Create a signing keystore for release builds:
   ```bash
   keytool -genkeypair -v -keystore humblyplural.keystore -alias humblyplural -keyalg RSA -keysize 2048 -validity 10000
   ```
5. Configure your `buildozer.spec` with the keystore values:
   ```ini
   android.release_keystore = /mnt/c/src/GitHub/bracekings/tictactoe/humblyplural.keystore
   android.release_keyalias = humblyplural
   android.release_keypass = yourpassword
   android.release_storepass = yourpassword
   ```
6. Build the release package:
   ```bash
   buildozer android release
   ```

### Google Play
- Create a Google Play Developer account.
- Create a new app in Play Console.
- Upload the signed APK or AAB.
- Provide store listing details, screenshots, and privacy policy.

### Amazon Appstore (free alternative)
- Create an Amazon Developer account at https://developer.amazon.com/.
- Use the Amazon Appstore Console to add a new Android app.
- Upload the same signed APK built with Buildozer.
- Fill in app details, screenshots, pricing, and availability.
- Amazon does not charge a developer registration fee for publishing apps.

Amazon is the best store option if you want your app public without paying for Google Play, but if you cannot use Amazon Appstore then itch.io is the next best public option.

### itch.io publishing
- itch.io lets you publish APKs publicly with no developer fee.
- Create a free itch.io account and login.
- Create a new project and choose "Downloadable".
- Upload your signed APK file and set it to public.
- Add a short description, screenshots, and any install instructions.
- itch.io gives you a public page and shareable link.

This is the best route for a public release if you cannot use Amazon or Google Play.

### Preferred Android install flow
For your goal — "out there" without random websites — the best option is itch.io or Amazon Appstore.

- itch.io gives you a public store-style page for your APK.
- Amazon Appstore is also public but may require parental permission.
- Both avoid random file-hosting sites and provide a trusted public page.

### Internal testing steps
1. In Play Console, open your app and choose **Testing > Internal testing**.
2. Create a new internal test release.
3. Upload the signed APK/AAB.
4. Add your Google account as an internal tester.
5. Publish the internal test.
6. Open the Play Store on your Android device and install via the internal testing link.

### If you still want a direct APK download
- Use a trusted host you control (e.g. your own website, private cloud storage, or a secure local network share).
- Share only the direct APK link with yourself.
- On Android, enable installation from unknown sources for that file.

### No-cost install option (recommended if you do not want to pay)
You do not need a paid developer account to get the app onto your own device.

1. Build the APK using WSL/Linux and Buildozer.
2. Copy the APK to your phone via USB, Wi-Fi transfer, or a private cloud folder.
3. On the phone, open the APK file and install it.
4. Enable "Install unknown apps" only for the app you use to open the APK (browser, file manager, etc.).

This is the simplest free path if you only need the app for yourself.

### Recommended route for you
- Build the app in Linux/WSL.
- Use direct APK install if you want to avoid paying for Play Store.
- If you later want a public store listing, move the same app to a Play Store or Amazon Appstore release.

## 3. iOS publishing

### Build environment
- You must use macOS.
- Install `kivy-ios` and Xcode.

### Build steps
1. Install the kivy-ios toolchain.
2. Create an Xcode project from the Kivy app.
3. Open the project in Xcode.
4. Build and archive the app.
5. Upload the IPA to App Store Connect.

### App Store Connect
- Enroll in the Apple Developer Program.
- Create a new app record.
- Upload the IPA and fill in app metadata.
- Submit for review.

## 4. Publishing notes

### Metadata suggestions
- App name: **Humbly Plural**
- Short description: "Private plural system manager for members, fronting, journals, and stats."
- Privacy: "Data is stored locally on the device; no network access required."

### Testing
- Test the Windows executable on at least one other machine.
- Test Android on a physical device if possible.
- Test iOS on a simulator and a device if available.

## 5. What I can help with

- Drafting App Store / Play Store listing text.
- Preparing screenshots and release notes.
- Reviewing packaging steps for Android or iOS.
- Helping generate a privacy policy statement.
