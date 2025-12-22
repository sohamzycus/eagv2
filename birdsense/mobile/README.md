# 🐦 BirdSense Mobile

**React Native Mobile App for Bird Identification**

Developed by Soham

---

## Features

- **🎵 Audio Recording** - Record bird calls and identify with BirdNET + AI
- **📷 Image Capture** - Take photos or select from gallery for Vision AI
- **📝 Description** - Describe birds in natural language
- **🇮🇳 India-Specific** - Local names, habitats, birding spots

---

## Quick Start

### Prerequisites

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Expo Go app on your phone

### Install & Run

```bash
cd mobile

# Install dependencies
npm install

# Start Expo development server
npm start
```

### Running on Device

1. Install **Expo Go** app from App Store/Play Store
2. Scan QR code from terminal with your camera
3. App will load on your device

---

## Authentication

Default credentials:

| Username | Password |
|----------|----------|
| `mazycus` | `ZycusMerlinAssist@2024` |
| `demo` | `demo123` |
| `soham` | `birdsense2024` |

---

## API Configuration

Edit `src/services/api.ts` to change the API endpoint:

```typescript
const API_CONFIG = {
  // Production
  BASE_URL: 'https://birdsense-xxxxx.run.app',
  
  // Local development
  // BASE_URL: 'http://localhost:8000',
};
```

---

## Build for Production

### iOS

```bash
eas build --platform ios
```

### Android

```bash
eas build --platform android
```

### Web

```bash
expo export:web
```

---

## Project Structure

```
mobile/
├── app/                    # Expo Router screens
│   ├── (tabs)/            # Tab navigation
│   │   ├── audio.tsx      # Audio identification
│   │   ├── image.tsx      # Image identification
│   │   ├── describe.tsx   # Description identification
│   │   └── profile.tsx    # User profile
│   ├── login.tsx          # Login screen
│   └── _layout.tsx        # Root layout
├── src/
│   ├── components/        # Reusable components
│   │   └── BirdCard.tsx   # Bird result card
│   ├── context/           # React context providers
│   │   └── AuthContext.tsx
│   └── services/          # API services
│       └── api.ts         # BirdSense API client
└── assets/                # Images, icons
```

---

**🐦 BirdSense Mobile** - *Developed by Soham*

