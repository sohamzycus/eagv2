# 🐦 BirdSense Mobile - Build Instructions

## Prerequisites

1. **Expo Account**: Create a free account at https://expo.dev
2. **EAS CLI**: Install globally

```bash
npm install -g eas-cli
```

3. **Login to Expo**:

```bash
eas login
```

---

## Development Builds

### Android APK (Debug)

```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense/mobile

# Build development APK
eas build --platform android --profile development
```

The APK will be available for download from Expo dashboard once built.

### iOS Development Build

```bash
# For iOS Simulator
eas build --platform ios --profile development

# For physical device (requires Apple Developer account)
eas build --platform ios --profile preview
```

---

## Quick Local Build (Android Only)

If you have Android Studio installed, you can build locally:

```bash
# Generate native project
npx expo prebuild --platform android

# Build APK
cd android
./gradlew assembleDebug

# APK location: android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Build Both Platforms

```bash
eas build --platform all --profile development
```

---

## Installing on Device

### Android
1. Download the APK from Expo dashboard
2. Transfer to device
3. Enable "Install from unknown sources"
4. Install APK

### iOS
1. For simulator: Build will auto-install
2. For device: Requires TestFlight (production) or ad-hoc distribution

---

## Alternative: Local Development with Expo Go

For quick testing without builds, use Expo Go app:

```bash
npx expo start
```

Scan QR code with Expo Go app on your device.

---

## Credentials

**Demo Login**: 
- Username: `mazycus`
- Password: `ZycusMerlinAssist@2024`

**API Endpoint**: 
- https://birdsense-api-1021486398038.us-central1.run.app

---

## Troubleshooting

### Build fails with signing error (iOS)
- Requires Apple Developer account ($99/year)
- For testing, use simulator profile

### Build takes too long
- EAS builds run on Expo servers
- Free tier has limited build capacity
- Consider local Android build for faster iteration

### App crashes on start
- Clear app data and reinstall
- Check API endpoint is reachable
- Verify network permissions

---

## Build Profiles

| Profile | Android | iOS | Use Case |
|---------|---------|-----|----------|
| development | Debug APK | Simulator | Development/testing |
| preview | Release APK | Ad-hoc | Internal distribution |
| production | AAB | App Store | Store release |

