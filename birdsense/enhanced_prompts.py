"""
🐦 BirdSense Enhanced Prompts
Developed by Soham

Advanced prompting techniques for 95%+ accuracy:
1. Chain-of-Thought (CoT) prompting
2. Few-shot learning with Indian examples
3. Confusion matrix for similar species
4. Spectrogram analysis prompts
"""

from typing import Dict, List, Optional

# =============================================================================
# CHAIN-OF-THOUGHT DESCRIPTION PROMPT
# =============================================================================

COT_DESCRIPTION_PROMPT = """You are an expert ornithologist specializing in Indian and South Asian birds.

A birder describes a bird they saw: "{description}"
Location: {location}
Month: {month}

**STEP-BY-STEP ANALYSIS:**

**Step 1: SIZE ESTIMATION**
Based on the description, estimate the bird's size:
- Sparrow-sized (10-15 cm)
- Bulbul-sized (15-20 cm)
- Myna-sized (20-25 cm)
- Crow-sized (40-50 cm)
- Eagle-sized (60+ cm)

**Step 2: PRIMARY COLORS**
Identify the main colors mentioned:
- Head/crown color
- Body/back color
- Underparts color
- Wing patterns
- Tail features

**Step 3: DISTINCTIVE FEATURES**
Look for key field marks:
- Bill shape and color
- Eye features (ring, stripe, patch)
- Crest or crown patterns
- Tail shape (forked, long, graduated)
- Leg color

**Step 4: BEHAVIOR & HABITAT**
Consider the context:
- Where was it seen? (forest, wetland, urban, garden)
- What was it doing? (feeding, flying, perching, swimming)

**Step 5: REGIONAL FILTERING**
Birds likely in {location} during {month}:
- Filter by geographic range
- Consider seasonal presence (resident vs migrant)

**Step 6: TOP CANDIDATES**
Based on above analysis, list 3-5 most likely species.

**Step 7: DIFFERENTIATION**
For each candidate, note what would CONFIRM or RULE OUT this species.

**Step 8: FINAL IDENTIFICATION**
Provide your identification with confidence level.

Respond in JSON format:
```json
{{
  "analysis": {{
    "size": "estimated size",
    "colors": ["primary colors"],
    "distinctive_features": ["key features"],
    "habitat": "inferred habitat"
  }},
  "birds": [
    {{
      "name": "Common Name",
      "scientific_name": "Genus species",
      "confidence": 85,
      "reasoning": "Why this species matches - field marks, location, behavior"
    }}
  ]
}}
```
"""

# =============================================================================
# FEW-SHOT INDIAN BIRD EXAMPLES
# =============================================================================

FEW_SHOT_EXAMPLES = """
**EXAMPLES OF INDIAN BIRD IDENTIFICATION:**

Example 1:
Description: "Small green bird with red beak flying in my garden"
Analysis: Small size, green plumage, red bill → Parrot family
Answer: Rose-ringed Parakeet (Psittacula krameri) - Common garden bird in India

Example 2:
Description: "Blue bird with long tail and chestnut body sitting on wire"
Analysis: Blue + chestnut, long tail, perching behavior → Roller
Answer: Indian Roller (Coracias benghalensis) - State bird of many Indian states

Example 3:
Description: "Black bird with forked tail, very aggressive, chasing crows"
Analysis: Black, forked tail, aggressive behavior → Drongo
Answer: Black Drongo (Dicrurus macrocercus) - Known for mobbing larger birds

Example 4:
Description: "Small brown bird with black bib near my house"
Analysis: Brown, black bib, urban habitat → Sparrow
Answer: House Sparrow (Passer domesticus) - Common urban bird

Example 5:
Description: "Yellow and black bird with beautiful flute-like song"
Analysis: Yellow + black, melodious call → Oriole
Answer: Indian Golden Oriole (Oriolus kundoo) - Known for fluting call

Example 6:
Description: "Bird with red patch under tail, black head, making cheerful calls"
Analysis: Red vent, black head, vocal → Bulbul
Answer: Red-vented Bulbul (Pycnonotus cafer) - Very common garden bird

Now identify: "{description}"
Location: {location}, Month: {month}
"""

# =============================================================================
# CONFUSION MATRIX PROMPT - SIMILAR SPECIES
# =============================================================================

CONFUSION_SPECIES_MATRIX = {
    # Bee-eaters
    ("Green Bee-eater", "Blue-tailed Bee-eater"): """
DIFFERENTIATION: Green Bee-eater vs Blue-tailed Bee-eater
- Green Bee-eater: ENTIRELY green, blue throat patch, NO chestnut
- Blue-tailed Bee-eater: Blue tail, CHESTNUT throat, larger
Check: Does it have chestnut on throat? → Blue-tailed. All green? → Green.
""",
    
    # Hornbills
    ("Malabar Pied Hornbill", "Great Hornbill"): """
DIFFERENTIATION: Malabar Pied Hornbill vs Great Hornbill
- Malabar Pied: Black and WHITE, smaller casque, ENDEMIC to Western Ghats
- Great Hornbill: Black and YELLOW, massive casque, larger overall
Check: Yellow present? → Great. Pure white? → Malabar Pied.
""",
    
    # Bulbuls
    ("Red-vented Bulbul", "Red-whiskered Bulbul"): """
DIFFERENTIATION: Red-vented Bulbul vs Red-whiskered Bulbul
- Red-vented: NO crest, scaly breast, red ONLY under tail
- Red-whiskered: Pointed BLACK crest, red ear patch AND vent
Check: Crest present? → Red-whiskered. No crest? → Red-vented.
""",
    
    # Cuckoos
    ("Asian Koel", "Indian Cuckoo"): """
DIFFERENTIATION: Asian Koel vs Indian Cuckoo
- Asian Koel: Male ALL BLACK, red eye, rising "ko-EL" call
- Indian Cuckoo: Grey with barred underparts, 4-note "crossword puzzle" call
Check: All black? → Koel. Barred underparts? → Indian Cuckoo.
""",
    
    # Kingfishers
    ("White-throated Kingfisher", "Common Kingfisher"): """
DIFFERENTIATION: White-throated Kingfisher vs Common Kingfisher
- White-throated: LARGER, blue AND chestnut, WHITE throat and breast
- Common Kingfisher: SMALLER, all blue-orange, NO white on throat
Check: White throat visible? → White-throated. Small and all blue-orange? → Common.
""",
    
    # Prinias
    ("Ashy Prinia", "Plain Prinia"): """
DIFFERENTIATION: Ashy Prinia vs Plain Prinia
- Ashy Prinia: GREY overall, rufous crown, graduated tail
- Plain Prinia: BROWN overall, plain head, long tail
Check: Grey coloration? → Ashy. Plain brown? → Plain Prinia.
""",
    
    # Thrushes
    ("Orange-headed Thrush", "Blue Whistling Thrush"): """
DIFFERENTIATION: Orange-headed Thrush vs Blue Whistling Thrush
- Orange-headed: ORANGE head, blue-grey back, forest floor
- Blue Whistling: ALL dark blue with white spots, near streams
Check: Orange head visible? → Orange-headed. Dark blue all over? → Blue Whistling.
""",
    
    # Eagles
    ("Crested Serpent Eagle", "Changeable Hawk-Eagle"): """
DIFFERENTIATION: Crested Serpent Eagle vs Changeable Hawk-Eagle
- Crested Serpent: Rounded wings, loud "KLUEE-WHEET" call, snake specialist
- Changeable Hawk-Eagle: Longer wings, variable plumage, hunts mammals/birds
Check: Calling? Listen for difference. Eating snake? → Serpent Eagle.
""",
    
    # Herons
    ("Indian Pond Heron", "Chinese Pond Heron"): """
DIFFERENTIATION: Indian Pond Heron vs Chinese Pond Heron (winter)
- Indian Pond: Streaky brown, transforms in breeding with maroon back
- Chinese Pond: Similar but RARE in India, slightly different streaking
Check: In India, default to Indian Pond Heron (Chinese is rare vagrant).
""",
    
    # Junglefowl
    ("Red Junglefowl", "Grey Junglefowl"): """
DIFFERENTIATION: Red Junglefowl vs Grey Junglefowl
- Red Junglefowl: Red-orange hackles, eclipse plumage variable, ancestor of chicken
- Grey Junglefowl: GREY body, golden hackles, ENDEMIC to peninsular India
Check: Location in South India? → Could be Grey. Grey body with golden neck? → Grey.
"""
}

def get_confusion_prompt(candidates: List[str]) -> str:
    """Get confusion matrix prompt for similar species."""
    for (bird1, bird2), explanation in CONFUSION_SPECIES_MATRIX.items():
        if bird1 in candidates and bird2 in candidates:
            return f"\n**SIMILAR SPECIES ALERT:**\n{explanation}\n"
        if bird1.lower() in [c.lower() for c in candidates] or bird2.lower() in [c.lower() for c in candidates]:
            return f"\n**SIMILAR SPECIES ALERT:**\n{explanation}\n"
    return ""

# =============================================================================
# SPECTROGRAM ANALYSIS PROMPT (FOR VISION MODEL)
# =============================================================================

SPECTROGRAM_ANALYSIS_PROMPT = """You are an expert in bioacoustics analyzing a bird call spectrogram.

**ANALYZE THIS SPECTROGRAM:**

1. **FREQUENCY RANGE** (Y-axis in Hz):
   - Low frequency birds (<1000 Hz): Owls, cuckoos, doves
   - Medium frequency (1000-4000 Hz): Thrushes, babblers, crows
   - High frequency (>4000 Hz): Warblers, sunbirds, finches

2. **TEMPORAL PATTERN** (X-axis - time):
   - Single notes: Alarm calls
   - Repeated pattern: Territorial song
   - Complex varied: Full song

3. **HARMONIC STRUCTURE**:
   - Multiple parallel lines: Pure tone with harmonics (whistles)
   - Broad bands: Harsh calls (crows, jays)
   - Frequency modulation: Ascending/descending

4. **CALL TYPE CLASSIFICATION**:
   - Rising whistle → Koel, Cuckoo
   - Two-note call → Common Cuckoo, Nightjar
   - Rapid trill → Bee-eater, Barbet
   - Melodious song → Magpie-Robin, Oriole

Location: {location}
Month: {month}

Based on this spectrogram analysis, identify the bird species.

Respond in JSON:
```json
{{
  "spectrogram_analysis": {{
    "frequency_range": "low/medium/high",
    "dominant_frequency_hz": 2500,
    "temporal_pattern": "description",
    "harmonics": "present/absent",
    "call_type": "whistle/trill/song/call"
  }},
  "birds": [
    {{
      "name": "Common Name",
      "scientific_name": "Genus species",
      "confidence": 85,
      "acoustic_match": "Why the spectrogram matches this species"
    }}
  ]
}}
```
"""

# =============================================================================
# ENHANCED IMAGE PROMPT WITH FIELD MARKS
# =============================================================================

FIELD_MARKS_IMAGE_PROMPT = """You are an expert ornithologist identifying a bird from an image.

**SYSTEMATIC FIELD MARK ANALYSIS:**

**1. HEAD FEATURES:**
- Crown: Color, pattern (striped, plain, crested)
- Supercilium (eyebrow): Present/absent, color
- Eye: Color, eye-ring, eye-stripe
- Lores: Area between eye and bill
- Malar stripe: "Mustache" mark

**2. BILL:**
- Shape: Conical (finch), hooked (raptor), long (wader), curved (sunbird)
- Color: Base vs tip
- Size relative to head

**3. BODY:**
- Throat: Color, pattern
- Breast: Plain, streaked, spotted
- Belly: Color
- Back/mantle: Color, pattern
- Rump: Often distinctive color

**4. WINGS:**
- Wing bars: Number, color
- Wing patches: Position, color
- Primary projection

**5. TAIL:**
- Length: Short, medium, long
- Shape: Square, rounded, forked, graduated
- Color and pattern

**6. LEGS:**
- Color: Often diagnostic
- Length relative to body

**7. OVERALL IMPRESSION:**
- Size estimate
- Posture
- Behavior visible

Location: {location}
Month: {month}

Analyze ALL visible field marks and identify the bird.

Respond in JSON:
```json
{{
  "field_marks_observed": {{
    "head": "description",
    "bill": "shape and color",
    "body": "colors and patterns",
    "wings": "features visible",
    "tail": "shape and color",
    "legs": "color if visible"
  }},
  "birds": [
    {{
      "name": "Common Name",
      "scientific_name": "Genus species",
      "confidence": 90,
      "key_field_marks": "Which marks confirm this ID"
    }}
  ]
}}
```
"""

# =============================================================================
# REGIONAL BIRD LISTS FOR CONTEXT
# =============================================================================

INDIA_REGIONAL_BIRDS = {
    "North India": {
        "common": ["House Sparrow", "Common Myna", "Rock Pigeon", "Black Kite", "Rose-ringed Parakeet"],
        "winter": ["Rosy Starling", "Steppe Eagle", "Common Crane", "Bar-headed Goose"],
        "special": ["Sarus Crane", "Indian Skimmer", "Great Indian Bustard"]
    },
    "South India": {
        "common": ["House Crow", "Common Myna", "Red-vented Bulbul", "Purple Sunbird"],
        "endemic": ["Malabar Grey Hornbill", "White-cheeked Barbet", "Nilgiri Flycatcher"],
        "special": ["Malabar Trogon", "Sri Lanka Frogmouth", "Nilgiri Wood Pigeon"]
    },
    "Western Ghats": {
        "endemic": ["Malabar Grey Hornbill", "White-bellied Treepie", "Nilgiri Flycatcher", 
                   "White-cheeked Barbet", "Crimson-backed Sunbird"],
        "special": ["Great Hornbill", "Malabar Trogon", "Sri Lanka Frogmouth"]
    },
    "Himalayas": {
        "common": ["Himalayan Bulbul", "Blue Whistling Thrush", "Red-billed Blue Magpie"],
        "high_altitude": ["Himalayan Monal", "Blood Pheasant", "Snow Partridge"],
        "special": ["Satyr Tragopan", "Western Tragopan", "Himalayan Snowcock"]
    },
    "Northeast India": {
        "special": ["Beautiful Nuthatch", "Bugun Liocichla", "White-winged Duck"],
        "hornbills": ["Great Hornbill", "Wreathed Hornbill", "Rufous-necked Hornbill"]
    },
    "Coastal": {
        "common": ["Brahminy Kite", "White-bellied Sea Eagle", "Reef Egret"],
        "waders": ["Kentish Plover", "Lesser Sand Plover", "Sanderling"],
        "seabirds": ["Brown-headed Gull", "Caspian Tern", "Lesser Crested Tern"]
    }
}

def get_regional_context(location: str, month: str) -> str:
    """Get regional bird context for prompting."""
    context = "\n**BIRDS EXPECTED IN THIS REGION:**\n"
    
    location_lower = location.lower()
    
    if any(x in location_lower for x in ["kerala", "karnataka", "tamil", "western ghats", "nilgiri"]):
        region = "Western Ghats"
    elif any(x in location_lower for x in ["himalaya", "uttarakhand", "himachal", "sikkim", "ladakh"]):
        region = "Himalayas"
    elif any(x in location_lower for x in ["assam", "meghalaya", "arunachal", "nagaland", "northeast"]):
        region = "Northeast India"
    elif any(x in location_lower for x in ["coast", "goa", "mumbai", "chennai", "sea"]):
        region = "Coastal"
    elif any(x in location_lower for x in ["delhi", "rajasthan", "punjab", "uttar pradesh"]):
        region = "North India"
    else:
        region = "South India"
    
    birds = INDIA_REGIONAL_BIRDS.get(region, {})
    for category, species_list in birds.items():
        context += f"- {category.replace('_', ' ').title()}: {', '.join(species_list[:5])}\n"
    
    return context


# =============================================================================
# MASTER PROMPT BUILDER
# =============================================================================

def build_enhanced_description_prompt(description: str, location: str = "India", 
                                       month: str = "January") -> str:
    """Build enhanced prompt with all techniques."""
    prompt = COT_DESCRIPTION_PROMPT.format(
        description=description,
        location=location,
        month=month
    )
    
    # Add few-shot examples
    prompt += "\n\n" + FEW_SHOT_EXAMPLES.format(
        description=description,
        location=location,
        month=month
    )
    
    # Add regional context
    prompt += get_regional_context(location, month)
    
    return prompt


def build_enhanced_image_prompt(location: str = "India", month: str = "January") -> str:
    """Build enhanced image prompt with field marks."""
    prompt = FIELD_MARKS_IMAGE_PROMPT.format(
        location=location,
        month=month
    )
    prompt += get_regional_context(location, month)
    return prompt


def build_enhanced_audio_prompt(spectrogram: bool = False, 
                                 location: str = "India", 
                                 month: str = "January") -> str:
    """Build enhanced audio prompt."""
    if spectrogram:
        prompt = SPECTROGRAM_ANALYSIS_PROMPT.format(
            location=location,
            month=month
        )
    else:
        prompt = """Analyze the acoustic features and identify the bird."""
    
    prompt += get_regional_context(location, month)
    return prompt


# Test
if __name__ == "__main__":
    # Test enhanced prompt
    prompt = build_enhanced_description_prompt(
        "Small green bird with red beak in my garden",
        "Bangalore, Karnataka",
        "March"
    )
    print(prompt[:2000])
    print("...")
    print(f"\nTotal prompt length: {len(prompt)} characters")

