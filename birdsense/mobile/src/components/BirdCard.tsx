/**
 * 🐦 BirdSense Mobile - Bird Result Card Component
 * Developed by Soham
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BirdResult } from '../services/api';

interface BirdCardProps {
  bird: BirdResult;
  index: number;
  expanded?: boolean;
}

export default function BirdCard({ bird, index, expanded = true }: BirdCardProps) {
  const [isExpanded, setIsExpanded] = useState(expanded);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return '#22c55e';
    if (confidence >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const getConservationColor = (status?: string) => {
    if (!status) return '#64748b';
    const code = status.toUpperCase().substring(0, 2);
    const colors: Record<string, string> = {
      LC: '#22c55e',
      NT: '#84cc16',
      VU: '#f59e0b',
      EN: '#f97316',
      CR: '#ef4444',
    };
    return colors[code] || '#64748b';
  };

  return (
    <View style={styles.container}>
      {/* Header - Always visible */}
      <TouchableOpacity
        style={styles.header}
        onPress={() => setIsExpanded(!isExpanded)}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          {bird.image_url ? (
            <Image source={{ uri: bird.image_url }} style={styles.thumbnail} />
          ) : (
            <View style={styles.placeholderThumb}>
              <Text style={styles.placeholderEmoji}>🐦</Text>
            </View>
          )}
          <View style={styles.headerText}>
            <Text style={styles.birdName}>#{index} {bird.name}</Text>
            <Text style={styles.scientificName}>{bird.scientific_name}</Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <View style={[styles.confidenceBadge, { backgroundColor: getConfidenceColor(bird.confidence) }]}>
            <Text style={styles.confidenceText}>{bird.confidence}%</Text>
          </View>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color="#64748b"
          />
        </View>
      </TouchableOpacity>

      {/* Expanded Content */}
      {isExpanded && (
        <View style={styles.content}>
          {/* Large Image */}
          {bird.image_url && (
            <Image source={{ uri: bird.image_url }} style={styles.mainImage} />
          )}

          {/* Summary */}
          {bird.summary && (
            <View style={styles.section}>
              <Text style={styles.summaryText}>{bird.summary}</Text>
            </View>
          )}

          {/* Quick Facts */}
          <View style={styles.factsRow}>
            {bird.habitat && (
              <View style={styles.factBadge}>
                <Text style={styles.factText}>🏠 {bird.habitat.substring(0, 50)}</Text>
              </View>
            )}
            {bird.diet && (
              <View style={[styles.factBadge, { backgroundColor: '#fef3c7' }]}>
                <Text style={[styles.factText, { color: '#92400e' }]}>
                  🍽️ {bird.diet.substring(0, 40)}
                </Text>
              </View>
            )}
            {bird.conservation && (
              <View style={[styles.factBadge, { backgroundColor: getConservationColor(bird.conservation) }]}>
                <Text style={[styles.factText, { color: '#fff' }]}>
                  🛡️ {bird.conservation}
                </Text>
              </View>
            )}
          </View>

          {/* Fun Facts */}
          {bird.fun_facts && bird.fun_facts.length > 0 && (
            <View style={styles.funFactsSection}>
              <Text style={styles.sectionTitle}>💡 Fun Facts</Text>
              {bird.fun_facts.slice(0, 2).map((fact, i) => (
                <Text key={i} style={styles.funFact}>• {fact}</Text>
              ))}
            </View>
          )}

          {/* India Info */}
          {bird.india_info?.found_in_india && (
            <View style={styles.indiaSection}>
              <Text style={styles.indiaTitle}>🇮🇳 India</Text>
              {bird.india_info.local_names && (
                <Text style={styles.indiaText}>
                  {Object.entries(bird.india_info.local_names)
                    .filter(([_, v]) => v)
                    .map(([lang, name]) => `${lang}: ${name}`)
                    .join(' | ')}
                </Text>
              )}
              {bird.india_info.regions && (
                <Text style={styles.indiaText}>📍 {bird.india_info.regions}</Text>
              )}
              {bird.india_info.best_season && (
                <Text style={styles.indiaText}>📅 {bird.india_info.best_season}</Text>
              )}
            </View>
          )}

          {/* Reasoning */}
          {bird.reason && (
            <View style={styles.reasonSection}>
              <Text style={styles.reasonTitle}>🔍 Reasoning</Text>
              <Text style={styles.reasonText}>{bird.reason}</Text>
            </View>
          )}

          {/* Source Badge */}
          <View style={styles.sourceRow}>
            <Text style={styles.sourceText}>📊 {bird.source}</Text>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    backgroundColor: '#f8fafc',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  thumbnail: {
    width: 50,
    height: 50,
    borderRadius: 8,
  },
  placeholderThumb: {
    width: 50,
    height: 50,
    borderRadius: 8,
    backgroundColor: '#dbeafe',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderEmoji: {
    fontSize: 24,
  },
  headerText: {
    marginLeft: 12,
    flex: 1,
  },
  birdName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  scientificName: {
    fontSize: 13,
    color: '#64748b',
    fontStyle: 'italic',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  confidenceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    padding: 16,
  },
  mainImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 12,
  },
  section: {
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 20,
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#3b82f6',
  },
  factsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  factBadge: {
    backgroundColor: '#ecfdf5',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  factText: {
    fontSize: 12,
    color: '#065f46',
  },
  funFactsSection: {
    backgroundColor: '#fefce8',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#854d0e',
    marginBottom: 8,
  },
  funFact: {
    fontSize: 13,
    color: '#475569',
    marginBottom: 4,
  },
  indiaSection: {
    backgroundColor: '#fff7ed',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#f97316',
    marginBottom: 12,
  },
  indiaTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#c2410c',
    marginBottom: 8,
  },
  indiaText: {
    fontSize: 13,
    color: '#7c2d12',
    marginBottom: 4,
  },
  reasonSection: {
    marginBottom: 12,
  },
  reasonTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
    marginBottom: 4,
  },
  reasonText: {
    fontSize: 13,
    color: '#64748b',
  },
  sourceRow: {
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
    paddingTop: 8,
  },
  sourceText: {
    fontSize: 12,
    color: '#94a3b8',
  },
});

