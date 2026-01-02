/**
 * 📚 BirdSense Mobile - History Tab
 * View all bird identification history across Audio, Image, and Description
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useHistory, getModeIcon, getModeColor, getModeLabel, RecordingSession } from '../../src/context/HistoryContext';
import BirdCard from '../../src/components/BirdCard';

type FilterMode = 'all' | 'audio-live' | 'audio-record' | 'audio-upload' | 'image' | 'description';

export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const { history, clearHistory, deleteSession } = useHistory();
  const [filter, setFilter] = useState<FilterMode>('all');
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  const filteredHistory = filter === 'all' 
    ? history 
    : history.filter(s => s.mode === filter);

  const filters: { key: FilterMode; label: string; icon: string }[] = [
    { key: 'all', label: 'All', icon: 'apps' },
    { key: 'audio-live', label: 'Live', icon: 'radio' },
    { key: 'audio-record', label: 'Record', icon: 'mic' },
    { key: 'image', label: 'Image', icon: 'camera' },
    { key: 'description', label: 'Describe', icon: 'text' },
  ];

  const handleClearHistory = () => {
    Alert.alert(
      'Clear All History',
      'Are you sure you want to delete all identification history? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: clearHistory,
        },
      ]
    );
  };

  const handleDeleteSession = (session: RecordingSession) => {
    Alert.alert(
      'Delete Session',
      `Delete this ${getModeLabel(session.mode)} session with ${session.birds.length} bird(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteSession(session.id),
        },
      ]
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return `Today, ${date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays === 1) {
      return `Yesterday, ${date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays < 7) {
      return date.toLocaleDateString(undefined, { weekday: 'long', hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
  };

  // Stats
  const totalBirds = history.reduce((sum, s) => sum + s.birds.length, 0);
  const uniqueBirds = new Set(history.flatMap(s => s.birds.map(b => b.name))).size;

  return (
    <LinearGradient colors={['#0f172a', '#1e293b', '#0f172a']} style={styles.container}>
      <ScrollView 
        style={[styles.scrollView, { paddingTop: insets.top + 10 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>📚 Identification History</Text>
          <Text style={styles.headerSubtitle}>
            {history.length} session{history.length !== 1 ? 's' : ''} • {totalBirds} birds • {uniqueBirds} unique species
          </Text>
        </View>

        {/* Filter Chips */}
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          style={styles.filterContainer}
          contentContainerStyle={styles.filterContent}
        >
          {filters.map(f => (
            <TouchableOpacity
              key={f.key}
              style={[
                styles.filterChip,
                filter === f.key && styles.filterChipActive,
                filter === f.key && { borderColor: getModeColor(f.key as any) }
              ]}
              onPress={() => setFilter(f.key)}
            >
              <Ionicons 
                name={f.icon as any} 
                size={16} 
                color={filter === f.key ? getModeColor(f.key as any) : '#64748b'} 
              />
              <Text style={[
                styles.filterChipText,
                filter === f.key && { color: getModeColor(f.key as any) }
              ]}>
                {f.label}
              </Text>
              {f.key !== 'all' && (
                <Text style={styles.filterCount}>
                  {history.filter(s => s.mode === f.key).length}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* History List */}
        <View style={styles.historyList}>
          {filteredHistory.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="folder-open-outline" size={80} color="#27272a" />
              <Text style={styles.emptyTitle}>
                {filter === 'all' ? 'No history yet' : `No ${filters.find(f => f.key === filter)?.label} recordings`}
              </Text>
              <Text style={styles.emptyText}>
                {filter === 'all' 
                  ? 'Start identifying birds using Audio, Image, or Description tabs'
                  : 'Try a different filter or start a new identification'}
              </Text>
            </View>
          ) : (
            filteredHistory.map((session, index) => (
              <View key={session.id}>
                <TouchableOpacity
                  style={styles.sessionCard}
                  onPress={() => setExpandedSession(
                    expandedSession === session.id ? null : session.id
                  )}
                  onLongPress={() => handleDeleteSession(session)}
                  activeOpacity={0.7}
                >
                  {/* Session Header */}
                  <View style={styles.sessionHeader}>
                    <View style={[styles.modeIcon, { backgroundColor: `${getModeColor(session.mode)}20` }]}>
                      <Ionicons 
                        name={getModeIcon(session.mode) as any} 
                        size={22} 
                        color={getModeColor(session.mode)} 
                      />
                    </View>
                    <View style={styles.sessionInfo}>
                      <Text style={styles.sessionDate}>{formatDate(session.date)}</Text>
                      <View style={styles.sessionMeta}>
                        <View style={[styles.modeBadge, { backgroundColor: `${getModeColor(session.mode)}20` }]}>
                          <Text style={[styles.modeBadgeText, { color: getModeColor(session.mode) }]}>
                            {getModeLabel(session.mode)}
                          </Text>
                        </View>
                        {session.location && session.location !== 'Unknown' && (
                          <Text style={styles.sessionLocation}>📍 {session.location}</Text>
                        )}
                      </View>
                    </View>
                    <View style={styles.sessionStats}>
                      <Text style={styles.birdCount}>🐦 {session.birds.length}</Text>
                      <Ionicons 
                        name={expandedSession === session.id ? 'chevron-up' : 'chevron-down'} 
                        size={20} 
                        color="#64748b" 
                      />
                    </View>
                  </View>

                  {/* Bird Names Preview */}
                  {!expandedSession && session.birds.length > 0 && (
                    <View style={styles.birdPreview}>
                      <Text style={styles.birdPreviewText} numberOfLines={1}>
                        {session.birds.slice(0, 3).map(b => b.name).join(' • ')}
                        {session.birds.length > 3 && ` +${session.birds.length - 3} more`}
                      </Text>
                    </View>
                  )}

                  {/* Source Info */}
                  {session.source && (
                    <Text style={styles.sourceText} numberOfLines={1}>
                      {session.mode === 'description' ? `"${session.source}"` : session.source}
                    </Text>
                  )}
                </TouchableOpacity>

                {/* Expanded Bird Cards */}
                {expandedSession === session.id && session.birds.length > 0 && (
                  <View style={styles.expandedBirds}>
                    {session.birds.map((bird, birdIndex) => (
                      <BirdCard
                        key={`${bird.name}-${birdIndex}`}
                        bird={bird}
                        index={birdIndex + 1}
                        expanded={birdIndex === 0}
                      />
                    ))}
                  </View>
                )}
              </View>
            ))
          )}
        </View>

        {/* Clear History Button */}
        {history.length > 0 && (
          <TouchableOpacity style={styles.clearButton} onPress={handleClearHistory}>
            <Ionicons name="trash-outline" size={20} color="#ef4444" />
            <Text style={styles.clearButtonText}>Clear All History</Text>
          </TouchableOpacity>
        )}

        <View style={{ height: 100 }} />
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#64748b',
  },
  filterContainer: {
    marginBottom: 16,
  },
  filterContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'transparent',
    marginRight: 8,
    gap: 6,
  },
  filterChipActive: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  filterChipText: {
    fontSize: 14,
    color: '#64748b',
    fontWeight: '600',
  },
  filterCount: {
    fontSize: 12,
    color: '#52525b',
    marginLeft: 2,
  },
  historyList: {
    paddingHorizontal: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#52525b',
    marginTop: 20,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 15,
    color: '#3f3f46',
    textAlign: 'center',
    lineHeight: 22,
  },
  sessionCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  sessionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modeIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  sessionInfo: {
    flex: 1,
  },
  sessionDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  sessionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  modeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 8,
  },
  modeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  sessionLocation: {
    fontSize: 13,
    color: '#94a3b8',
  },
  sessionStats: {
    alignItems: 'flex-end',
    gap: 4,
  },
  birdCount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
  },
  birdPreview: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  birdPreviewText: {
    fontSize: 14,
    color: '#94a3b8',
    fontStyle: 'italic',
  },
  sourceText: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 8,
  },
  expandedBirds: {
    marginTop: -4,
    marginBottom: 8,
    paddingLeft: 8,
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 16,
    marginTop: 20,
    paddingVertical: 16,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    gap: 10,
  },
  clearButtonText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
  },
});


