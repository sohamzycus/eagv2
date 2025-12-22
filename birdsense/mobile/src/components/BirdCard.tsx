/**
 * 🐦 BirdSense Mobile - Bird Result Card Component
 * Developed by Soham
 * 
 * Uses same image URLs as web version (server-provided)
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { BirdResult } from '../services/api';

interface BirdCardProps {
  bird: BirdResult;
  index: number;
  expanded?: boolean;
}

export default function BirdCard({ bird, index, expanded = true }: BirdCardProps) {
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [imageLoading, setImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  
  // Animation
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 1,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return ['#22c55e', '#16a34a'];
    if (confidence >= 50) return ['#f59e0b', '#d97706'];
    return ['#ef4444', '#dc2626'];
  };

  const getConservationLabel = (status?: string) => {
    if (!status) return null;
    const labels: Record<string, { text: string; colors: string[] }> = {
      'LC': { text: 'Least Concern', colors: ['#22c55e', '#16a34a'] },
      'NT': { text: 'Near Threatened', colors: ['#84cc16', '#65a30d'] },
      'VU': { text: 'Vulnerable', colors: ['#f59e0b', '#d97706'] },
      'EN': { text: 'Endangered', colors: ['#f97316', '#ea580c'] },
      'CR': { text: 'Critically Endangered', colors: ['#ef4444', '#dc2626'] },
    };
    const code = status.toUpperCase().substring(0, 2);
    return labels[code] || { text: status, colors: ['#64748b', '#475569'] };
  };

  const searchBirdImages = () => {
    const query = encodeURIComponent(`${bird.name} ${bird.scientific_name || ''} bird`);
    Linking.openURL(`https://www.google.com/search?tbm=isch&q=${query}`);
  };

  const renderImage = () => {
    // If no image URL or error, show placeholder
    if (!bird.image_url || imageError) {
      return (
        <TouchableOpacity style={styles.placeholderImage} onPress={searchBirdImages}>
          <Text style={styles.placeholderEmoji}>🐦</Text>
          <Text style={styles.placeholderText}>Tap to search images</Text>
        </TouchableOpacity>
      );
    }

    return (
      <View style={styles.imageContainer}>
        {imageLoading && (
          <View style={styles.imageLoading}>
            <ActivityIndicator size="large" color="#3b82f6" />
          </View>
        )}
        <Image
          source={{ 
            uri: bird.image_url,
            headers: {
              'User-Agent': 'Mozilla/5.0 (compatible; BirdSense/1.0)'
            }
          }}
          style={[styles.mainImage, imageLoading && styles.imageHidden]}
          onLoadStart={() => setImageLoading(true)}
          onLoadEnd={() => setImageLoading(false)}
          onError={() => {
            console.log(`Image failed for ${bird.name}: ${bird.image_url}`);
            setImageLoading(false);
            setImageError(true);
          }}
          resizeMode="cover"
        />
      </View>
    );
  };

  const conservation = getConservationLabel(bird.conservation);
  const confidenceColors = getConfidenceColor(bird.confidence);

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [
            {
              translateY: slideAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [30, 0],
              }),
            },
          ],
        },
      ]}
    >
      {/* Header - Always visible */}
      <TouchableOpacity
        style={styles.header}
        onPress={() => setIsExpanded(!isExpanded)}
        activeOpacity={0.8}
      >
        <LinearGradient colors={['#1e3a5f', '#0f172a']} style={styles.headerGradient}>
          <View style={styles.headerLeft}>
            <View style={styles.indexBadge}>
              <Text style={styles.indexText}>{index}</Text>
            </View>
            <View style={styles.headerInfo}>
              <Text style={styles.birdName} numberOfLines={1}>{bird.name}</Text>
              {bird.scientific_name && (
                <Text style={styles.scientificName} numberOfLines={1}>
                  {bird.scientific_name}
                </Text>
              )}
            </View>
          </View>
          <View style={styles.headerRight}>
            <LinearGradient colors={confidenceColors as [string, string]} style={styles.confidenceBadge}>
              <Text style={styles.confidenceText}>{bird.confidence}%</Text>
            </LinearGradient>
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={24}
              color="#94a3b8"
            />
          </View>
        </LinearGradient>
      </TouchableOpacity>

      {/* Expanded Content */}
      {isExpanded && (
        <View style={styles.content}>
          {/* Image */}
          {renderImage()}

          {/* Summary */}
          {bird.summary && (
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <Ionicons name="document-text" size={16} color="#3b82f6" />
                <Text style={styles.sectionTitle}>Summary</Text>
              </View>
              <Text style={styles.sectionText}>{bird.summary}</Text>
            </View>
          )}

          {/* Habitat - Full Info */}
          {bird.habitat && (
            <View style={styles.fullInfoCard}>
              <View style={styles.fullInfoHeader}>
                <Ionicons name="leaf" size={18} color="#22c55e" />
                <Text style={styles.fullInfoLabel}>Habitat</Text>
              </View>
              <Text style={styles.fullInfoText}>{bird.habitat}</Text>
            </View>
          )}

          {/* Diet - Full Info */}
          {bird.diet && (
            <View style={styles.fullInfoCard}>
              <View style={styles.fullInfoHeader}>
                <Ionicons name="restaurant" size={18} color="#f59e0b" />
                <Text style={styles.fullInfoLabel}>Diet</Text>
              </View>
              <Text style={styles.fullInfoText}>{bird.diet}</Text>
            </View>
          )}

          {/* Conservation Status */}
          {conservation && (
            <View style={styles.conservationSection}>
              <LinearGradient colors={conservation.colors as [string, string]} style={styles.conservationBadge}>
                <Ionicons name="shield-checkmark" size={16} color="#fff" />
                <Text style={styles.conservationText}>{conservation.text}</Text>
              </LinearGradient>
            </View>
          )}

          {/* Fun Facts */}
          {bird.fun_facts && bird.fun_facts.length > 0 && (
            <View style={styles.funFactsSection}>
              <View style={styles.sectionHeader}>
                <Ionicons name="bulb" size={16} color="#fbbf24" />
                <Text style={styles.sectionTitle}>Fun Facts</Text>
              </View>
              {bird.fun_facts.map((fact, i) => (
                <View key={i} style={styles.funFactRow}>
                  <Text style={styles.funFactBullet}>•</Text>
                  <Text style={styles.funFact}>{fact}</Text>
                </View>
              ))}
            </View>
          )}

          {/* India Info */}
          {bird.india_info?.found_in_india && (
            <LinearGradient
              colors={['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.05)']}
              style={styles.indiaSection}
            >
              <View style={styles.indiaTitleRow}>
                <Text style={styles.indiaFlag}>🇮🇳</Text>
                <Text style={styles.indiaTitle}>Found in India</Text>
              </View>
              
              {bird.india_info.regions && (
                <View style={styles.indiaRow}>
                  <Ionicons name="location" size={14} color="#f97316" />
                  <Text style={styles.indiaValue}>{bird.india_info.regions}</Text>
                </View>
              )}
              
              {bird.india_info.best_season && (
                <View style={styles.indiaRow}>
                  <Ionicons name="calendar" size={14} color="#f97316" />
                  <Text style={styles.indiaValue}>{bird.india_info.best_season}</Text>
                </View>
              )}
              
              {bird.india_info.notable_locations && (
                <View style={styles.indiaRow}>
                  <Ionicons name="map" size={14} color="#f97316" />
                  <Text style={styles.indiaValue}>{bird.india_info.notable_locations}</Text>
                </View>
              )}
              
              {bird.india_info.local_names && Object.keys(bird.india_info.local_names).some(k => bird.india_info?.local_names?.[k]) && (
                <View style={styles.localNamesSection}>
                  <Text style={styles.localNamesLabel}>Local Names:</Text>
                  {Object.entries(bird.india_info.local_names)
                    .filter(([_, v]) => v)
                    .map(([lang, name]) => (
                      <Text key={lang} style={styles.localName}>
                        {lang.charAt(0).toUpperCase() + lang.slice(1)}: {name}
                      </Text>
                    ))
                  }
                </View>
              )}
            </LinearGradient>
          )}

          {/* Reasoning */}
          {bird.reason && (
            <View style={styles.reasonSection}>
              <View style={styles.sectionHeader}>
                <Ionicons name="search" size={16} color="#8b5cf6" />
                <Text style={styles.sectionTitle}>Identification Reasoning</Text>
              </View>
              <Text style={styles.reasonText}>{bird.reason}</Text>
            </View>
          )}

          {/* Source */}
          <View style={styles.sourceRow}>
            <Ionicons name="analytics" size={14} color="#64748b" />
            <Text style={styles.sourceText}>{bird.source}</Text>
          </View>
        </View>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    marginHorizontal: 16,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  header: {
    overflow: 'hidden',
  },
  headerGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  indexBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(59, 130, 246, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  indexText: {
    color: '#60a5fa',
    fontSize: 14,
    fontWeight: '700',
  },
  headerInfo: {
    flex: 1,
  },
  birdName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#fff',
  },
  scientificName: {
    fontSize: 13,
    color: '#94a3b8',
    fontStyle: 'italic',
    marginTop: 2,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  confidenceBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 10,
  },
  confidenceText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  content: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  imageContainer: {
    height: 200,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
    backgroundColor: '#0f172a',
  },
  mainImage: {
    width: '100%',
    height: '100%',
  },
  imageHidden: {
    opacity: 0,
  },
  imageLoading: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0f172a',
  },
  placeholderImage: {
    height: 150,
    borderRadius: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.3)',
    borderStyle: 'dashed',
  },
  placeholderEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  placeholderText: {
    color: '#60a5fa',
    fontSize: 14,
  },
  section: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e2e8f0',
  },
  sectionText: {
    fontSize: 14,
    color: '#cbd5e1',
    lineHeight: 22,
  },
  fullInfoCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 12,
  },
  fullInfoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  fullInfoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e2e8f0',
  },
  fullInfoText: {
    fontSize: 14,
    color: '#cbd5e1',
    lineHeight: 22,
  },
  conservationSection: {
    marginBottom: 16,
  },
  conservationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    gap: 8,
  },
  conservationText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  funFactsSection: {
    backgroundColor: 'rgba(251, 191, 36, 0.1)',
    padding: 14,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(251, 191, 36, 0.2)',
  },
  funFactRow: {
    flexDirection: 'row',
    marginTop: 6,
  },
  funFactBullet: {
    color: '#fbbf24',
    fontSize: 14,
    marginRight: 8,
  },
  funFact: {
    flex: 1,
    fontSize: 14,
    color: '#fde68a',
    lineHeight: 20,
  },
  indiaSection: {
    padding: 14,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(249, 115, 22, 0.3)',
  },
  indiaTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  indiaFlag: {
    fontSize: 20,
    marginRight: 8,
  },
  indiaTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#fed7aa',
  },
  indiaRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 8,
  },
  indiaValue: {
    flex: 1,
    fontSize: 14,
    color: '#fed7aa',
    lineHeight: 20,
  },
  localNamesSection: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(249, 115, 22, 0.2)',
  },
  localNamesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#fdba74',
    marginBottom: 6,
  },
  localName: {
    fontSize: 13,
    color: '#fed7aa',
    marginTop: 4,
  },
  reasonSection: {
    backgroundColor: 'rgba(139, 92, 246, 0.1)',
    padding: 14,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(139, 92, 246, 0.2)',
  },
  reasonText: {
    fontSize: 13,
    color: '#c4b5fd',
    lineHeight: 20,
  },
  sourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  sourceText: {
    fontSize: 12,
    color: '#64748b',
  },
});
