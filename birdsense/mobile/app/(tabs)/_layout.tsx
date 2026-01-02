/**
 * 🐦 BirdSense Mobile - Tabs Layout
 * Developed by Soham
 */

import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Platform, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HistoryProvider } from '../../src/context/HistoryContext';

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  
  return (
    <HistoryProvider>
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#22c55e',
        tabBarInactiveTintColor: '#64748b',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopWidth: 1,
          borderTopColor: '#e2e8f0',
          height: 56 + insets.bottom,
          paddingBottom: insets.bottom,
          paddingTop: 6,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: '#1a472a',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
        tabBarHideOnKeyboard: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="audio"
        options={{
          title: 'Audio',
          headerTitle: '🎵 Audio ID',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? 'mic' : 'mic-outline'} size={24} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="image"
        options={{
          title: 'Image',
          headerTitle: '📷 Image ID',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? 'camera' : 'camera-outline'} size={24} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="describe"
        options={{
          title: 'Describe',
          headerTitle: '📝 Description',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? 'document-text' : 'document-text-outline'} size={24} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'History',
          headerTitle: '📚 History',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? 'time' : 'time-outline'} size={24} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          headerTitle: '👤 Profile',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons name={focused ? 'person' : 'person-outline'} size={24} color={color} />
          ),
        }}
      />
    </Tabs>
    </HistoryProvider>
  );
}
