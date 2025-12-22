"""
🔬 BirdSense Research Tools
Developed by Soham

Advanced tools for:
1. Web Search Integration - Real-time knowledge enhancement via LLM tool calls
2. Rarity Detection - Flag unusual sightings outside native range
3. Research Citation Generator - For academic papers and publications

Vision: Enable researchers to discover rare sightings and publish in Nature, etc.
"""

import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os

from providers import provider_factory
from bird_dataset import get_full_dataset, BirdEntry


@dataclass
class RaritySighting:
    """Represents a potential rare/unusual bird sighting."""
    bird_name: str
    scientific_name: str
    location: str
    date: str
    rarity_level: str  # vagrant, first_record, rare, unusual
    native_range: List[str]
    significance: str
    citation_text: str
    confidence: float


@dataclass
class WebSearchResult:
    """Result from web search."""
    query: str
    summary: str
    sources: List[Dict[str, str]]
    timestamp: str


class BirdKnowledgeSearch:
    """
    Web search integration for real-time bird knowledge.
    Uses LLM's knowledge + simulated web search for accuracy boost.
    """
    
    def __init__(self):
        self.cache: Dict[str, WebSearchResult] = {}
        
    def search_bird_info(self, bird_name: str, query_type: str = "identification") -> WebSearchResult:
        """
        Search for bird information using LLM knowledge + web simulation.
        
        Query types:
        - identification: Features, similar species, distinguishing marks
        - distribution: Range, migration patterns, seasonal presence
        - vocalizations: Call/song descriptions, audio characteristics
        - behavior: Feeding, nesting, social behavior
        - conservation: Status, threats, population trends
        """
        cache_key = f"{bird_name}:{query_type}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Build search prompt for LLM
        prompts = {
            "identification": f"""Search for detailed identification features of {bird_name}:
- Key field marks and distinguishing features
- Similar species and how to differentiate
- Plumage variations (male/female/juvenile/seasonal)
- Size comparisons

Provide accurate, current ornithological information.""",
            
            "distribution": f"""Search for distribution and range of {bird_name}:
- Native range and countries
- Migration patterns if migratory
- Seasonal presence in different regions
- Recent range expansions or contractions
- Status in India and South Asia

Provide current distributional data.""",
            
            "vocalizations": f"""Search for vocalization details of {bird_name}:
- Primary song description
- Call types (alarm, contact, flight)
- Frequency range in Hz
- Temporal patterns (rhythmic, varied, etc.)
- When they vocalize (dawn, night, territorial)

Provide acoustic characteristics useful for audio identification.""",
            
            "behavior": f"""Search for behavioral information on {bird_name}:
- Feeding habits and diet
- Breeding behavior
- Social structure
- Habitat preferences
- Activity patterns

Provide behavioral ecology details.""",
            
            "conservation": f"""Search for conservation status of {bird_name}:
- IUCN Red List status
- Population trends
- Major threats
- Conservation efforts
- Protected areas where found

Provide current conservation data."""
        }
        
        prompt = prompts.get(query_type, prompts["identification"])
        
        # Use LLM to "search" (leveraging its training data as knowledge base)
        search_prompt = f"""You are a bird knowledge search engine. {prompt}

Respond in JSON format:
```json
{{
  "summary": "Comprehensive summary of findings",
  "key_facts": ["fact1", "fact2", "fact3"],
  "sources": [
    {{"name": "eBird", "info": "relevant data"}},
    {{"name": "IUCN", "info": "status info"}},
    {{"name": "Handbook of Birds", "info": "identification details"}}
  ],
  "confidence": 85
}}
```"""
        
        try:
            response = provider_factory.call_text(search_prompt)
            
            # Parse response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            result = WebSearchResult(
                query=f"{bird_name} - {query_type}",
                summary=data.get("summary", ""),
                sources=[{"name": s.get("name", ""), "info": s.get("info", "")} 
                        for s in data.get("sources", [])],
                timestamp=datetime.now().isoformat()
            )
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            return WebSearchResult(
                query=f"{bird_name} - {query_type}",
                summary=f"Search failed: {str(e)}",
                sources=[],
                timestamp=datetime.now().isoformat()
            )
    
    def enhance_identification(self, bird_candidates: List[Dict], 
                               audio_features: Dict = None,
                               location: str = "",
                               month: str = "") -> List[Dict]:
        """
        Enhance bird identification accuracy using web search knowledge.
        
        This is the key function that uses tool calls to improve accuracy.
        """
        if not bird_candidates:
            return []
        
        enhanced_results = []
        
        for candidate in bird_candidates[:5]:  # Process top 5 candidates
            bird_name = candidate.get("name", "")
            confidence = candidate.get("confidence", 50)
            
            # Search for distribution info
            dist_info = self.search_bird_info(bird_name, "distribution")
            
            # Check if bird is expected in the location
            location_match = self._check_location_match(bird_name, location, dist_info)
            
            # Search for vocalization info if audio features provided
            if audio_features:
                vocal_info = self.search_bird_info(bird_name, "vocalizations")
                audio_match = self._check_audio_match(audio_features, vocal_info)
            else:
                audio_match = 1.0
            
            # Adjust confidence based on search results
            adjusted_confidence = confidence * location_match * audio_match
            
            enhanced_results.append({
                **candidate,
                "confidence": min(95, adjusted_confidence),
                "location_verified": location_match > 0.7,
                "audio_verified": audio_match > 0.7 if audio_features else None,
                "knowledge_sources": dist_info.sources[:2]
            })
        
        # Re-sort by adjusted confidence
        enhanced_results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return enhanced_results
    
    def _check_location_match(self, bird_name: str, location: str, 
                               dist_info: WebSearchResult) -> float:
        """Check if bird is expected in the location."""
        if not location:
            return 1.0
        
        location_lower = location.lower()
        summary_lower = dist_info.summary.lower()
        
        # Check for location mentions
        india_terms = ["india", "indian", "south asia", "subcontinent"]
        if any(term in location_lower for term in india_terms):
            if any(term in summary_lower for term in india_terms):
                return 1.1  # Boost for India match
            elif "not found" in summary_lower or "vagrant" in summary_lower:
                return 0.6  # Reduce for unlikely location
        
        return 1.0
    
    def _check_audio_match(self, audio_features: Dict, 
                            vocal_info: WebSearchResult) -> float:
        """Check if audio features match expected vocalizations."""
        summary = vocal_info.summary.lower()
        
        dominant_freq = audio_features.get("dominant_freq", 0)
        
        # Simple heuristic matching
        if "high-pitched" in summary and dominant_freq > 4000:
            return 1.2
        elif "low" in summary and dominant_freq < 1000:
            return 1.2
        elif "medium" in summary and 1000 < dominant_freq < 4000:
            return 1.1
        
        return 1.0


class RarityDetector:
    """
    Detect rare or unusual bird sightings for research significance.
    
    Flags:
    - First records for a region
    - Vagrants (birds far from native range)
    - Unusual timing (out of season)
    - Range extensions
    """
    
    def __init__(self):
        self.dataset = {bird.name.lower(): bird for bird in get_full_dataset()}
        self.knowledge_search = BirdKnowledgeSearch()
        
        # India regions for detailed analysis
        self.india_regions = [
            "Western Ghats", "Eastern Ghats", "Himalayas", "Northeast",
            "Deccan Plateau", "Indo-Gangetic Plains", "Thar Desert",
            "Western India", "Southern India", "Northern India", "Central India",
            "Andaman", "Nicobar", "Lakshadweep", "Kerala", "Karnataka",
            "Tamil Nadu", "Andhra Pradesh", "Maharashtra", "Gujarat",
            "Rajasthan", "Punjab", "Uttarakhand", "Sikkim", "Assam",
            "Arunachal Pradesh", "West Bengal", "Odisha", "Bihar"
        ]
    
    def check_rarity(self, bird_name: str, location: str, 
                     date: str = None, month: str = None) -> Optional[RaritySighting]:
        """
        Check if a bird sighting is rare or unusual.
        
        Returns RaritySighting if significant, None otherwise.
        """
        bird_key = bird_name.lower()
        bird_entry = self.dataset.get(bird_key)
        
        if not bird_entry:
            # Unknown bird - could be very significant!
            return self._create_unknown_sighting(bird_name, location, date)
        
        # Check rarity level
        rarity = bird_entry.rarity_in_india
        
        if rarity == "not_native":
            # Bird not native to India - check if it's a vagrant
            return self._check_vagrant(bird_entry, location, date)
        
        elif rarity == "rare":
            # Known rare species - always significant
            return self._create_rare_sighting(bird_entry, location, date)
        
        elif rarity == "vagrant":
            # Known vagrant species
            return self._create_vagrant_sighting(bird_entry, location, date)
        
        elif rarity == "uncommon":
            # Check for unusual location within India
            return self._check_unusual_location(bird_entry, location, date)
        
        return None  # Common species, not particularly notable
    
    def _create_unknown_sighting(self, bird_name: str, location: str, 
                                  date: str) -> RaritySighting:
        """Create sighting for unknown/unrecorded species."""
        return RaritySighting(
            bird_name=bird_name,
            scientific_name="Unknown - requires verification",
            location=location or "India",
            date=date or datetime.now().strftime("%Y-%m-%d"),
            rarity_level="potential_first_record",
            native_range=["Unknown"],
            significance=f"Potential first record of {bird_name} for this region. "
                        "Requires photographic/audio documentation and expert verification.",
            citation_text=self._generate_citation(bird_name, location, date, "first_record"),
            confidence=50.0
        )
    
    def _check_vagrant(self, bird: BirdEntry, location: str, 
                       date: str) -> Optional[RaritySighting]:
        """Check if non-native bird is a vagrant sighting."""
        return RaritySighting(
            bird_name=bird.name,
            scientific_name=bird.scientific_name,
            location=location or "India",
            date=date or datetime.now().strftime("%Y-%m-%d"),
            rarity_level="vagrant",
            native_range=bird.native_regions,
            significance=f"{bird.name} is not native to India. Native range: {', '.join(bird.native_regions)}. "
                        f"This sighting may represent a vagrant, escapee, or significant range extension.",
            citation_text=self._generate_citation(bird.name, location, date, "vagrant"),
            confidence=75.0
        )
    
    def _create_rare_sighting(self, bird: BirdEntry, location: str,
                               date: str) -> RaritySighting:
        """Create sighting for known rare species."""
        # Search for conservation status
        conservation_info = self.knowledge_search.search_bird_info(
            bird.name, "conservation"
        )
        
        return RaritySighting(
            bird_name=bird.name,
            scientific_name=bird.scientific_name,
            location=location or "India",
            date=date or datetime.now().strftime("%Y-%m-%d"),
            rarity_level="rare",
            native_range=bird.native_regions,
            significance=f"{bird.name} ({bird.scientific_name}) is a rare species. "
                        f"Habitat: {bird.habitat}. {conservation_info.summary[:200]}",
            citation_text=self._generate_citation(bird.name, location, date, "rare"),
            confidence=85.0
        )
    
    def _create_vagrant_sighting(self, bird: BirdEntry, location: str,
                                  date: str) -> RaritySighting:
        """Create sighting for known vagrant species."""
        return RaritySighting(
            bird_name=bird.name,
            scientific_name=bird.scientific_name,
            location=location or "India",
            date=date or datetime.now().strftime("%Y-%m-%d"),
            rarity_level="vagrant",
            native_range=bird.native_regions,
            significance=f"{bird.name} is classified as a vagrant to India. "
                        f"Regular range: {', '.join(bird.native_regions)}.",
            citation_text=self._generate_citation(bird.name, location, date, "vagrant"),
            confidence=80.0
        )
    
    def _check_unusual_location(self, bird: BirdEntry, location: str,
                                 date: str) -> Optional[RaritySighting]:
        """Check if uncommon bird is in unusual location."""
        if not location:
            return None
        
        # Get distribution info
        dist_info = self.knowledge_search.search_bird_info(bird.name, "distribution")
        
        # Check for location mismatch
        location_lower = location.lower()
        summary_lower = dist_info.summary.lower()
        
        # Check for significant range extension
        if any(region.lower() in location_lower for region in self.india_regions):
            if "not recorded" in summary_lower or "first" in summary_lower:
                return RaritySighting(
                    bird_name=bird.name,
                    scientific_name=bird.scientific_name,
                    location=location,
                    date=date or datetime.now().strftime("%Y-%m-%d"),
                    rarity_level="unusual_location",
                    native_range=bird.native_regions,
                    significance=f"{bird.name} sighting in {location} may represent "
                                f"a range extension or unusual occurrence.",
                    citation_text=self._generate_citation(bird.name, location, date, "unusual"),
                    confidence=70.0
                )
        
        return None
    
    def _generate_citation(self, bird_name: str, location: str, 
                           date: str, record_type: str) -> str:
        """Generate academic citation text for the sighting."""
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        location_str = location or "India"
        
        citations = {
            "first_record": f"""**Potential First Record**

{bird_name} at {location_str}

Date: {date_str}
Recorded using: BirdSense AI (https://birdsense.app)

Suggested citation format:
Observer Name ({date_str[:4]}). First record of {bird_name} from {location_str}. 
*Indian Birds* XX(X): XX-XX.

Note: This record requires verification with photographs, audio recordings, 
and confirmation by regional bird records committee.""",
            
            "vagrant": f"""**Vagrant Sighting Record**

{bird_name} at {location_str}

Date: {date_str}
Identification method: BirdSense AI multimodal analysis

Suggested citation:
Observer ({date_str[:4]}). Vagrant {bird_name} recorded at {location_str}.
*Journal of the Bombay Natural History Society* XXX(X): XX-XX.

Documentation: Photographs and audio recordings recommended for 
acceptance by Indian Bird Records Committee.""",
            
            "rare": f"""**Rare Species Sighting**

{bird_name} at {location_str}

Date: {date_str}
Detected by: BirdSense AI

For publication in:
- Indian Birds
- Journal of the Bombay Natural History Society
- Newsletter for Birdwatchers
- eBird India

Record with photographs for citizen science databases.""",
            
            "unusual": f"""**Unusual Occurrence**

{bird_name} at {location_str}

Date: {date_str}

This sighting may represent a range extension. Consider reporting to:
- eBird India (ebird.org/india)
- Indian Bird Records Committee
- State bird atlas projects

BirdSense AI confidence in identification: High"""
        }
        
        return citations.get(record_type, citations["unusual"])
    
    def generate_research_report(self, sighting: RaritySighting) -> str:
        """Generate a detailed research report for significant sighting."""
        return f"""
╔══════════════════════════════════════════════════════════════════════╗
║  🔬 BIRDSENSE RESEARCH ALERT                                        ║
╚══════════════════════════════════════════════════════════════════════╝

SPECIES: {sighting.bird_name}
SCIENTIFIC NAME: {sighting.scientific_name}
LOCATION: {sighting.location}
DATE: {sighting.date}
RARITY LEVEL: {sighting.rarity_level.upper().replace('_', ' ')}

═══════════════════════════════════════════════════════════════════════
SIGNIFICANCE
═══════════════════════════════════════════════════════════════════════
{sighting.significance}

Native Range: {', '.join(sighting.native_range)}
Detection Confidence: {sighting.confidence:.1f}%

═══════════════════════════════════════════════════════════════════════
PUBLICATION GUIDANCE
═══════════════════════════════════════════════════════════════════════
{sighting.citation_text}

═══════════════════════════════════════════════════════════════════════
NEXT STEPS FOR RESEARCHERS
═══════════════════════════════════════════════════════════════════════
1. Document with high-quality photographs (multiple angles)
2. Record vocalizations if bird is calling
3. Note habitat, behavior, and associated species
4. Report to eBird India and regional WhatsApp groups
5. Contact state bird records committee
6. Consider writing up for Indian Birds journal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by BirdSense AI | Developed by Soham
Vision: Making every birder a potential contributor to ornithological science
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# Initialize global instances
knowledge_search = BirdKnowledgeSearch()
rarity_detector = RarityDetector()


def enhance_with_search(bird_candidates: List[Dict], 
                        audio_features: Dict = None,
                        location: str = "",
                        month: str = "") -> List[Dict]:
    """
    Main function to enhance identification with web search.
    Called as a tool by the LLM for improved accuracy.
    """
    return knowledge_search.enhance_identification(
        bird_candidates, audio_features, location, month
    )


def check_for_rare_sighting(bird_name: str, location: str = "",
                            date: str = None) -> Optional[Dict]:
    """
    Check if a bird sighting is rare/significant.
    Returns research report if significant.
    """
    sighting = rarity_detector.check_rarity(bird_name, location, date)
    
    if sighting:
        return {
            "is_rare": True,
            "rarity_level": sighting.rarity_level,
            "significance": sighting.significance,
            "citation": sighting.citation_text,
            "full_report": rarity_detector.generate_research_report(sighting)
        }
    
    return {"is_rare": False}


# Test
if __name__ == "__main__":
    # Test rarity detection
    print("Testing rarity detection...")
    
    # Test 1: Vagrant from America
    result = check_for_rare_sighting("Blue Jay", "Kerala, India")
    print(f"\nBlue Jay in Kerala: {result['rarity_level'] if result['is_rare'] else 'Common'}")
    
    # Test 2: Rare species
    result = check_for_rare_sighting("Great Indian Bustard", "Rajasthan")
    if result['is_rare']:
        print(f"\nGreat Indian Bustard: {result['rarity_level']}")
        print(result['full_report'][:500])
    
    # Test 3: Common species
    result = check_for_rare_sighting("House Sparrow", "Delhi")
    print(f"\nHouse Sparrow in Delhi: {'Rare' if result['is_rare'] else 'Common'}")

