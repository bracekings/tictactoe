# itch.io Publishing Guide for Humbly Plural

This guide shows you how to publish the Android APK to itch.io so your app is public.

## 1. Build the APK

Follow the steps in `APP_STORE_PUBLISHING.md` to build and sign the APK using WSL/Linux and Buildozer.

The key commands are:
```bash
cd /mnt/c/src/GitHub/bracekings/tictactoe
./build_android.sh
```

Then create a keystore and update `buildozer.spec`:
```bash
keytool -genkeypair -v -keystore humblyplural.keystore -alias humblyplural -keyalg RSA -keysize 2048 -validity 10000
```

Set these in `buildozer.spec`:
```ini
android.release_keystore = /mnt/c/src/GitHub/bracekings/tictactoe/humblyplural.keystore
android.release_keyalias = humblyplural
android.release_keypass = yourpassword
android.release_storepass = yourpassword
```

Then build the signed release APK:
```bash
buildozer android release
```

## 2. Prepare your itch.io account

1. Go to https://itch.io and create a free account.
2. Verify your email address.
3. Open your user dashboard.

## 3. Create a new game/app page

1. Click **Upload new project**.
2. Fill in the title: `Humbly Plural`.
3. Choose a project type such as **Game** or **Tool**.
4. Select **Downloadable**.
5. Choose **Public** visibility.

## 4. Upload the APK

1. In the "Uploads" section, click **Upload files**.
2. Select your signed release APK from the Buildozer output.
3. Set the file to **This file is the game**.
4. Save the upload.

## 5. Add page details

- **Short description**: Private plural system manager for member tracking, fronting logs, journal notes, and system statistics.
- **Full description**: Use the text from `AMAZON_APPSTORE_NOTES.md` or `APP_STORE_PUBLISHING.md`.
- **Screenshots**: Capture your app screens and upload them.
- **Project tags**: `android`, `privacy`, `journal`, `wellness`, `plural system`.
- **Price**: Free.

## 6. Publish the page

1. Set the project status to **Public**.
2. Make sure the APK upload is marked as the downloadable game file.
3. Publish the page.

## 7. Share the public link

Once published, itch.io will give you a public page URL.

Example:
```text
https://yourusername.itch.io/humbly-plural
```

Share that link with others. They can download the APK from itch.io and install it on Android.

## Notes
- Users will still need to install the APK manually after download.
- itch.io is a trusted public platform, so it avoids the need for random file-hosting.
- This is the best free public distribution option for your Android app right now.
