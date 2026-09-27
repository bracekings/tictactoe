# Humbly Plural

A free, open-source replica of Simply Plural - a comprehensive plural system management app for managing DID/OSDD systems.

## Features

- **Member Management**: Add, edit, and view system members with names, pronouns, roles, and descriptions
- **Fronting Tracking**: Track who's currently fronting, start/end switches, and co-fronting
- **Journal System**: Keep notes and journal entries with timestamps
- **Statistics Dashboard**: View system statistics and activity patterns
- **Data Persistence**: All data is saved locally in JSON format

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python humbly_plural.py
```

Or use the provided batch file:
```bash
run_humbly_plural.bat
```

## Data Storage

All data is stored locally in the `data/` directory:
- `members.json` - System member information
- `switches.json` - Fronting switch history
- `notes.json` - Journal entries
- `settings.json` - App settings

## Features in Detail

### Members Tab
- View all system members in a scrollable list
- Add new members with detailed profiles
- Edit existing member information
- Support for pronouns, roles, and descriptions

### Fronting Tab
- Select one or multiple members who are currently fronting
- Start and end switches with timestamps
- Add notes to switches
- Track co-fronting situations

### Journal Tab
- Create and edit journal entries
- View entries chronologically
- Rich text support for detailed notes

### Stats Tab
- Total member count
- Switch history statistics
- Most active members
- Recent activity overview

## Privacy & Security

- All data is stored locally on your device
- No internet connection required
- No data is sent to external servers
- Complete privacy and control over your information

## Building for Mobile

This app is built with Kivy, which supports deployment to:
- Android (via Buildozer)
- iOS (via kivy-ios)
- Desktop platforms (Windows, macOS, Linux)

## Contributing

This is a community project. Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Help with translations

## License

This project is open source and free to use. Please respect the privacy and consent of plural systems when sharing or discussing this software.

## Disclaimer

This app is not a substitute for professional mental health care. It is a tool for self-management and should be used responsibly.