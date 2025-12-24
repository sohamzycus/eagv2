/**
 * 🧠 BirdSense Mobile - Analysis Trail Component
 * Developed by Soham
 * 
 * Shows the detailed analysis pipeline with:
 * - Step-by-step analysis trail
 * - Acoustic/Image features
 * - Confidence backing data
 * - Sources used
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

// Types matching API response
interface AnalysisStep {
  step: string;
  status: string;
  details?: string;
  duration_ms?: number;
}

interface AudioFeatures {
  duration: number;
  min_freq: number;
  max_freq: number;
  peak_freq: number;
  freq_range: number;
  pattern: string;
  complexity: string;
  syllables: number;
  rhythm: string;
  quality: string;
}

interface ImageFeatures {
  size_estimate?: string;
  primary_colors?: string[];
  beak_description?: string;
  distinctive_features?: string[];
  pose?: string;
}

export interface AnalysisTrailData {
  pipeline: string;
  steps: AnalysisStep[];
  audio_features?: AudioFeatures;
  image_features?: ImageFeatures;
  sources_used: string[];
  enhancement_applied: boolean;
}

interface AnalysisTrailProps {
  trail: AnalysisTrailData;
  processingTimeMs: number;
  modelUsed: string;
}

export default function AnalysisTrail({ trail, processingTimeMs, modelUsed }: AnalysisTrailProps) {
  const [expanded, setExpanded] = useState(true);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return { name: 'checkmark-circle', color: '#22c55e' };
      case 'warning':
        return { name: 'alert-circle', color: '#f59e0b' };
      case 'error':
        return { name: 'close-circle', color: '#ef4444' };
      default:
        return { name: 'ellipse', color: '#64748b' };
    }
  };

  const renderAudioFeatures = () => {
    if (!trail.audio_features) return null;
    const f = trail.audio_features;

    return (
      <View style={styles.featuresCard}>
        <View style={styles.featuresHeader}>
          <Ionicons name="musical-notes" size={18} color="#3b82f6" />
          <Text style={styles.featuresTitle}>Acoustic Features</Text>
        </View>
        
        <View style={styles.featureGrid}>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Frequency</Text>
            <Text style={styles.featureValue}>{f.min_freq}-{f.max_freq} Hz</Text>
          </View>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Peak</Text>
            <Text style={styles.featureValue}>{f.peak_freq} Hz</Text>
          </View>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Pattern</Text>
            <Text style={styles.featureValue}>{f.pattern}</Text>
          </View>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Complexity</Text>
            <Text style={styles.featureValue}>{f.complexity}</Text>
          </View>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Syllables</Text>
            <Text style={styles.featureValue}>{f.syllables}</Text>
          </View>
          <View style={styles.featureItem}>
            <Text style={styles.featureLabel}>Rhythm</Text>
            <Text style={styles.featureValue}>{f.rhythm}</Text>
          </View>
        </View>

        <View style={styles.featureRow}>
          <Ionicons name="time" size={14} color="#64748b" />
          <Text style={styles.featureText}>Duration: {f.duration.toFixed(2)}s</Text>
        </View>
        <View style={styles.featureRow}>
          <Ionicons name="cellular" size={14} color="#64748b" />
          <Text style={styles.featureText}>Signal Quality: {f.quality}</Text>
        </View>
      </View>
    );
  };

  const renderImageFeatures = () => {
    if (!trail.image_features) return null;
    const f = trail.image_features;

    return (
      <View style={styles.featuresCard}>
        <View style={styles.featuresHeader}>
          <Ionicons name="image" size={18} color="#8b5cf6" />
          <Text style={styles.featuresTitle}>Visual Features</Text>
        </View>
        
        {f.size_estimate && (
          <View style={styles.featureRow}>
            <Ionicons name="resize" size={14} color="#64748b" />
            <Text style={styles.featureText}>Size: {f.size_estimate}</Text>
          </View>
        )}
        {f.beak_description && (
          <View style={styles.featureRow}>
            <Ionicons name="eye" size={14} color="#64748b" />
            <Text style={styles.featureText}>Beak: {f.beak_description}</Text>
          </View>
        )}
        {f.primary_colors && f.primary_colors.length > 0 && (
          <View style={styles.featureRow}>
            <Ionicons name="color-palette" size={14} color="#64748b" />
            <Text style={styles.featureText}>Colors: {f.primary_colors.join(', ')}</Text>
          </View>
        )}
        {f.pose && (
          <View style={styles.featureRow}>
            <Ionicons name="body" size={14} color="#64748b" />
            <Text style={styles.featureText}>Pose: {f.pose}</Text>
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <TouchableOpacity 
        style={styles.header} 
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={['rgba(59, 130, 246, 0.15)', 'rgba(139, 92, 246, 0.15)']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.headerGradient}
        >
          <View style={styles.headerLeft}>
            <Ionicons name="analytics" size={20} color="#3b82f6" />
            <Text style={styles.headerTitle}>🧠 BirdSense Analysis Trail</Text>
          </View>
          <Ionicons 
            name={expanded ? 'chevron-up' : 'chevron-down'} 
            size={20} 
            color="#64748b" 
          />
        </LinearGradient>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.content}>
          {/* Model Info */}
          <View style={styles.modelInfo}>
            <View style={styles.modelBadge}>
              <Ionicons name="hardware-chip" size={14} color="#60a5fa" />
              <Text style={styles.modelText}>{modelUsed}</Text>
            </View>
            <Text style={styles.timeText}>{processingTimeMs}ms</Text>
          </View>

          {/* SAM-Audio Enhancement Badge */}
          {trail.enhancement_applied && (
            <View style={styles.enhancementBadge}>
              <Ionicons name="volume-high" size={14} color="#22c55e" />
              <Text style={styles.enhancementText}>META SAM-Audio Enhancement Applied</Text>
            </View>
          )}

          {/* Analysis Steps */}
          <View style={styles.stepsContainer}>
            <Text style={styles.sectionTitle}>Analysis Pipeline</Text>
            {trail.steps.map((step, index) => {
              const icon = getStatusIcon(step.status);
              return (
                <View key={index} style={styles.stepRow}>
                  <View style={styles.stepLeft}>
                    <Ionicons name={icon.name as any} size={16} color={icon.color} />
                    <View style={styles.stepContent}>
                      <Text style={styles.stepName}>{step.step}</Text>
                      {step.details && (
                        <Text style={styles.stepDetails}>{step.details}</Text>
                      )}
                    </View>
                  </View>
                  {step.duration_ms && (
                    <Text style={styles.stepDuration}>{step.duration_ms}ms</Text>
                  )}
                </View>
              );
            })}
          </View>

          {/* Features */}
          {renderAudioFeatures()}
          {renderImageFeatures()}

          {/* Sources Used */}
          {trail.sources_used.length > 0 && (
            <View style={styles.sourcesContainer}>
              <Text style={styles.sourcesLabel}>Sources:</Text>
              <View style={styles.sourcesList}>
                {trail.sources_used.map((source, index) => (
                  <View key={index} style={styles.sourceBadge}>
                    <Text style={styles.sourceText}>{source}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.3)',
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
    gap: 10,
  },
  headerTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#e2e8f0',
  },
  content: {
    padding: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(59, 130, 246, 0.2)',
  },
  modelInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  modelBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 6,
  },
  modelText: {
    fontSize: 12,
    color: '#60a5fa',
    fontWeight: '500',
  },
  timeText: {
    fontSize: 12,
    color: '#64748b',
  },
  enhancementBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginBottom: 12,
    gap: 6,
  },
  enhancementText: {
    fontSize: 12,
    color: '#22c55e',
    fontWeight: '500',
  },
  stepsContainer: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 8,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  stepLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
    gap: 10,
  },
  stepContent: {
    flex: 1,
  },
  stepName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#e2e8f0',
  },
  stepDetails: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
    lineHeight: 18,
  },
  stepDuration: {
    fontSize: 11,
    color: '#64748b',
  },
  featuresCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  featuresHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  featuresTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e2e8f0',
  },
  featureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  featureItem: {
    width: '50%',
    marginBottom: 8,
  },
  featureLabel: {
    fontSize: 11,
    color: '#64748b',
  },
  featureValue: {
    fontSize: 13,
    color: '#e2e8f0',
    fontWeight: '500',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  featureText: {
    fontSize: 12,
    color: '#94a3b8',
  },
  sourcesContainer: {
    marginTop: 8,
  },
  sourcesLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 6,
  },
  sourcesList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  sourceBadge: {
    backgroundColor: 'rgba(139, 92, 246, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  sourceText: {
    fontSize: 11,
    color: '#a78bfa',
    fontWeight: '500',
  },
});


