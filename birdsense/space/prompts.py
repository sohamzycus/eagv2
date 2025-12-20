"""
🐦 BirdSense Prompts - External prompt configuration

All LLM prompts are defined here to:
1. Avoid hardcoding in main app
2. Make prompts easily editable
3. Prevent bias toward specific species

NOTE: For production-quality bird identification, use specialized models like:
- Audio: BirdNET (Cornell Lab) - requires TensorFlow
- Images: Fine-tuned bird classification models
"""

# ============ AUDIO IDENTIFICATION ============

AUDIO_IDENTIFICATION_PROMPT = """You are an expert ornithologist analyzing bird vocalizations.

ACOUSTIC ANALYSIS:
- Frequency Range: {min_freq}-{max_freq} Hz
- Peak Frequency: {peak_freq} Hz  
- Frequency Span: {freq_range} Hz
- Pattern: {pattern}
- Complexity: {complexity}
- Syllables: {syllables}
- Rhythm: {rhythm}
- Duration: {duration}s
- Quality: {quality}
{location_info}
{season_info}

CRITICAL FREQUENCY-TO-BIRD-SIZE CORRELATION:
- 100-500 Hz: VERY LARGE birds - Owls (hooting), Bitterns, Large Herons
- 500-1000 Hz: LARGE birds - Crows, Ravens, Doves, Pigeons, Owls (screeching)
- 1000-2000 Hz: MEDIUM-LARGE - Thrushes, Cuckoos, Woodpeckers
- 2000-4000 Hz: MEDIUM - Robins, Blackbirds, Mynas, Starlings
- 4000-6000 Hz: SMALL - Finches, Sparrows, Warblers
- 6000-10000 Hz: VERY SMALL - Goldcrests, Treecreepers, high-pitched warblers

PATTERN CLUES:
- "Hoo-hoo" or deep resonant: OWL family
- Harsh cawing: Crows, Ravens
- Melodious varied phrases: Thrushes, Mockingbirds
- Repetitive chirps: Sparrows, Finches
- Complex trills: Warblers, Wrens

⚠️ IMPORTANT: Low frequency (under 1000 Hz) with slow rhythm strongly suggests OWL, not a songbird!

Be conservative with confidence (50-75%) since this is acoustic feature analysis, not spectral matching.

Respond ONLY with JSON:
{{"birds": [{{"name": "Species Name", "scientific_name": "Genus species", "confidence": 55, "reason": "Specific features: frequency suggests X-sized bird, pattern indicates Y"}}]}}
"""


# ============ IMAGE IDENTIFICATION ============

IMAGE_IDENTIFICATION_PROMPT = """You are an expert ornithologist. Identify this bird by carefully examining its FEATURES.

📋 SYSTEMATIC FEATURE ANALYSIS:

**1. BEAK (most diagnostic):**
- Color: Red? Orange? Yellow? Pink? Black? Grey?
- Shape: Conical (seed-eater)? Thin (insectivore)? Hooked (raptor)?

**2. HEAD PATTERN:**
- Crown/cap color?
- Eye ring or stripe?
- Any cheek patches? What color?

**3. BODY:**
- Primary color(s)?
- Breast: Plain, streaked, spotted?
- Wing bars present?

**4. SIZE & SHAPE:**
- Sparrow-sized? Robin-sized? Larger?

🔍 KEY DIAGNOSTIC FEATURES:

| Feature Combination | Strong Indicator For |
|---------------------|---------------------|
| Red/orange beak + orange cheek | Zebra Finch |
| Yellow body + wing bars | Goldfinch species |
| Grey crown + black bib (male) | House Sparrow |
| Red forehead/breast (male) | House Finch |
| Entire head solid red | Red-headed Woodpecker |

⚠️ NOTE: Many birds are brown (sparrows, female finches, wrens, thrushes).
Don't assume species based on color alone - check ALL features!

COUNT ONLY birds you can CLEARLY see.

Respond with JSON ONLY:
{"birds": [{"name": "Species Name", "scientific_name": "Genus species", "confidence": 70, "reason": "BEAK: [color/shape], HEAD: [pattern], BODY: [color/pattern]"}]}
"""


# ============ DESCRIPTION IDENTIFICATION ============

DESCRIPTION_IDENTIFICATION_PROMPT = """You are an expert ornithologist. Based on the description below, identify the most likely bird species.

DESCRIPTION:
"{description}"

Analyze the described features and match them to known bird species. Consider:
- Colors and patterns mentioned
- Size descriptions
- Behavior described
- Habitat or location hints
- Sounds or calls described

Respond with JSON only:
{{"birds": [{{"name": "Species Name", "scientific_name": "Genus species", "confidence": 75, "reason": "Features from description that match"}}]}}
"""


# ============ FREQUENCY BAND GUIDELINES ============
# These are general guidelines, not hardcoded species

FREQUENCY_GUIDELINES = """
Frequency bands correlate with bird size:
- 200-800 Hz: Very large birds (owls, crows, pigeons)
- 800-2000 Hz: Large songbirds (thrushes, mynas)
- 2000-4000 Hz: Medium songbirds (robins, blackbirds)
- 4000-8000 Hz: Small songbirds (warblers, finches)
- 8000-12000 Hz: Very small birds, high-pitched calls
"""

