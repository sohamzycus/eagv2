/**
 * 🐦 BirdSense Mobile - Tabs Index
 * Redirects to audio tab by default
 */

import { Redirect } from 'expo-router';

export default function TabsIndex() {
  return <Redirect href="/(tabs)/audio" />;
}

