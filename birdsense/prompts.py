"""
🐦 BirdSense Prompts - Model-Specific Prompt Configuration

All LLM prompts are defined here with variants for:
1. Ollama models (LLaVA, phi4) - Concise, structured prompts
2. GPT models (GPT-4o, GPT-5.2) - Detailed, conversational prompts

NOTE: For production-quality bird identification, use specialized models like:
- Audio: BirdNET (Cornell Lab) - requires TensorFlow
- Images: Fine-tuned bird classification models
"""


# ============ MODEL INFO ============
# Used for dynamic analysis trail

MODEL_INFO = {
    "ollama": {
        "vision": {"name": "LLaVA 7B", "provider": "Ollama (Local)", "type": "Vision-Language"},
        "text": {"name": "phi4 14B", "provider": "Ollama (Local)", "type": "Text Reasoning"},
        "audio": {"name": "BirdNET + phi4", "provider": "Cornell + Ollama", "type": "Hybrid Audio"}
    },
    "litellm": {
        "vision": {"name": "GPT-4o", "provider": "LiteLLM (Enterprise)", "type": "Vision-Language"},
        "text": {"name": "GPT-5.2", "provider": "LiteLLM (Enterprise)", "type": "Text Reasoning"},
        "audio": {"name": "BirdNET + GPT-5.2", "provider": "Cornell + LiteLLM", "type": "Hybrid Audio"}
    }
}


# ============ AUDIO IDENTIFICATION ============
# P1 Priority - Most important identification type

AUDIO_PROMPT_OLLAMA = """Expert ornithologist: analyze bird audio features.

ACOUSTIC DATA:
- Freq: {min_freq}-{max_freq} Hz (peak: {peak_freq} Hz)
- Pattern: {pattern}, Complexity: {complexity}
- Syllables: {syllables}, Rhythm: {rhythm}
- Duration: {duration}s
{location_info}
{season_info}

SIZE-FREQUENCY RULE:
100-500Hz=owl/heron, 500-1500Hz=crow/dove, 1500-3000Hz=thrush/myna, 3000-6000Hz=finch/sparrow, 6000+Hz=warbler

⚠️ Low freq (<1000Hz) + slow = OWL not songbird!

JSON only:
{{"birds": [{{"name": "Species", "scientific_name": "Genus species", "confidence": 60, "reason": "Freq X Hz suggests Y-size, pattern Z"}}]}}"""


AUDIO_PROMPT_GPT = """You are a world-class ornithologist with 30+ years of field experience analyzing bird vocalizations.

## ACOUSTIC ANALYSIS DATA:
- **Frequency Range**: {min_freq} - {max_freq} Hz
- **Peak Frequency**: {peak_freq} Hz  
- **Frequency Span**: {freq_range} Hz
- **Pattern**: {pattern}
- **Complexity**: {complexity}
- **Syllables**: {syllables}
- **Rhythm**: {rhythm}
- **Duration**: {duration}s
- **Signal Quality**: {quality}
{location_info}
{season_info}

## CRITICAL: FREQUENCY-TO-BIRD-SIZE CORRELATION

This is the most reliable indicator for audio identification:

| Frequency Range | Bird Size | Typical Species |
|-----------------|-----------|-----------------|
| 100-500 Hz | Very Large | Owls (hooting), Bitterns, Great Herons |
| 500-1000 Hz | Large | Crows, Ravens, Doves, Pigeons, Owl screeches |
| 1000-2000 Hz | Medium-Large | Thrushes, Cuckoos, Woodpeckers |
| 2000-4000 Hz | Medium | Robins, Blackbirds, Mynas, Starlings |
| 4000-6000 Hz | Small | Finches, Sparrows, Warblers |
| 6000-10000 Hz | Very Small | Goldcrests, Treecreepers |

## PATTERN DIAGNOSTICS:
- **"Hoo-hoo" deep resonant**: OWL family (always check this first!)
- **Harsh cawing**: Corvids (Crows, Ravens, Jays)
- **Cooing**: Doves, Pigeons
- **Complex melodic phrases**: Thrushes, Mockingbirds, Nightingales
- **Repetitive chirps**: Sparrows, Finches
- **Complex trills/warbles**: Warblers, Wrens

## ⚠️ IMPORTANT RULES:
1. Low frequency (<1000 Hz) with slow rhythm = OWL, not a songbird!
2. Don't confuse frequency with pitch perception
3. Be conservative (50-75% confidence) - this is acoustic analysis, not spectral matching

Respond ONLY with valid JSON:
```json
{{"birds": [{{"name": "Species Name", "scientific_name": "Genus species", "confidence": 65, "reason": "Peak freq {peak_freq}Hz indicates [size]-sized bird. Pattern '{pattern}' suggests [family]. {rhythm} rhythm typical of [species group]."}}]}}
```"""


# ============ ENHANCED AUDIO PROMPT (HIGH ACCURACY) ============
# Uses Chain-of-Thought + India context for better accuracy

AUDIO_PROMPT_ENHANCED = """You are Dr. Salim Ali, the legendary "Birdman of India", analyzing a bird vocalization.

## 🎵 ACOUSTIC MEASUREMENTS FROM RECORDING:
- **Duration**: ~{duration} seconds
- **Dominant Frequency**: {peak_freq} Hz
- **Frequency Range**: {min_freq} - {max_freq} Hz
- **Bandwidth**: {freq_range} Hz
- **Pattern Type**: {pattern}
- **Complexity Level**: {complexity}
- **Syllable Structure**: {syllables}
- **Rhythm Characteristic**: {rhythm}
{location_info}
{season_info}

## 🧠 STEP-BY-STEP REASONING (Chain of Thought):

### Step 1: SIZE FROM FREQUENCY
**CRITICAL RULE**: Lower frequency = Larger bird body resonance
| Frequency | Bird Size | Examples |
|-----------|-----------|----------|
| 100-500 Hz | Very Large | Owls, Bitterns, Peacock calls |
| 500-1000 Hz | Large | Crows, Doves, Cuckoos, Owl screeches |
| 1000-2500 Hz | Medium | Mynas, Drongos, Babblers, Kingfishers |
| 2500-4500 Hz | Small-Medium | Bulbuls, Orioles, Sunbirds |
| 4500-7000 Hz | Small | Warblers, White-eyes, Flowerpeckers |
| 7000+ Hz | Very Small | Extremely high-pitched calls |

**This recording at {peak_freq} Hz indicates a [SIZE] bird.**

### Step 2: PATTERN ANALYSIS
- **Rising whistle** (kooo-EEEL): Asian Koel (Eudynamys scolopaceus)
- **Two-note call** (brain-fever): Common Hawk-Cuckoo
- **Liquid bubbling**: Coucals (Centropus spp.)
- **Melodious song**: Magpie-Robin, Orioles
- **Harsh calls**: Drongos, Crows
- **Repetitive chip**: Tailorbirds, Prinias
- **Complex mimicry**: Greater Racket-tailed Drongo, Hill Myna

### Step 3: INDIA-SPECIFIC BIRDS BY CALL TYPE
**High-pitched whistles (3000+ Hz):**
- Indian Golden Oriole - fluting
- White-throated Kingfisher - loud kee-kee-kee
- Purple Sunbird - metallic chips

**Medium frequency songs (1500-3000 Hz):**
- Asian Koel - rising ko-el (VERY COMMON in India)
- Greater Coucal - deep booming
- Oriental Magpie-Robin - varied song
- Red-vented Bulbul - cheerful calls
- Common Myna - varied repertoire

**Low frequency (500-1500 Hz):**
- Spotted Owlet - churring, screeching
- Collared Scops Owl - single hoot
- Common Cuckoo - cu-coo
- Rose-ringed Parakeet - harsh screech

### Step 4: SEASONAL CONTEXT
- Summer (March-June): Breeding calls peak - Koel, Cuckoos very vocal
- Monsoon (July-Sept): Dawn chorus, many warblers
- Winter (Oct-Feb): Migratory birds arrive

### Step 5: FINAL IDENTIFICATION
Based on {peak_freq} Hz and {pattern} pattern, identify the most likely species.

## OUTPUT (JSON only):
```json
{{"birds": [
  {{"name": "Most Likely Species", "scientific_name": "Genus species", "confidence": 75, "reason": "At {peak_freq}Hz with {pattern} pattern suggests [SIZE]-sized [FAMILY]. The {rhythm} rhythm is characteristic of [SPECIES]."}}
]}}
```"""


# Combined prompt function for audio
def get_audio_prompt(backend: str = "auto", enhanced: bool = True) -> str:
    """Get audio prompt optimized for the backend."""
    if enhanced:
        return AUDIO_PROMPT_ENHANCED
    if backend == "litellm" or backend == "gpt":
        return AUDIO_PROMPT_GPT
    return AUDIO_PROMPT_OLLAMA


# ============ IMAGE IDENTIFICATION ============

IMAGE_PROMPT_OLLAMA = """Expert ornithologist: identify bird by features.

ANALYZE SYSTEMATICALLY:
1. BEAK: Color (red/orange/yellow/black), Shape (conical/thin/hooked)
2. HEAD: Crown color, Eye pattern, Cheek patches
3. BODY: Primary colors, Breast pattern (plain/streaked/spotted)
4. SIZE: Sparrow/robin/crow sized

KEY DIAGNOSTICS:
- Red/orange beak + orange cheek = Zebra Finch
- Yellow body + wing bars = Goldfinch
- Grey crown + black bib = House Sparrow (male)
- Solid red head = Red-headed Woodpecker

⚠️ Many birds are brown - check ALL features!

Count ONLY birds clearly visible.

JSON only:
{{"birds": [{{"name": "Species", "scientific_name": "Genus species", "confidence": 70, "reason": "BEAK: [x], HEAD: [y], BODY: [z]"}}]}}"""


IMAGE_PROMPT_GPT = """You are a world-class ornithologist with expertise in bird identification from photographs.

## SYSTEMATIC FEATURE ANALYSIS

Examine this image carefully and analyze these features IN ORDER:

### 1. BEAK (Most Diagnostic Feature)
- **Color**: Red? Orange? Yellow? Pink? Black? Grey? Multi-colored?
- **Shape**: 
  - Conical/thick = seed-eater (finches, sparrows, grosbeaks)
  - Thin/pointed = insectivore (warblers, wrens)
  - Hooked = raptor or shrike
  - Long/thin = nectar feeder or probing species

### 2. HEAD PATTERN
- **Crown/Cap**: What color? Any crest?
- **Eye Features**: Ring? Stripe? Line through eye?
- **Cheek Patches**: Present? What color?
- **Face Pattern**: Any distinctive markings?

### 3. BODY PLUMAGE
- **Primary Color(s)**: Main body color
- **Breast**: Plain? Streaked? Spotted? What color?
- **Wings**: Bars? Patches? Solid color?
- **Tail**: Shape? Pattern? White edges?

### 4. SIZE & SHAPE
- **Relative Size**: Sparrow-sized? Robin-sized? Crow-sized?
- **Body Shape**: Plump? Slender? Compact?

## 🔑 KEY DIAGNOSTIC COMBINATIONS

| Feature Combination | Strong Indicator |
|---------------------|-----------------|
| Red/orange beak + orange cheek patch | **Zebra Finch** |
| Bright yellow body + black wings with bars | **American Goldfinch** |
| Grey-brown + black bib (male) | **House Sparrow** |
| Red forehead + streaky breast | **House Finch** |
| Entirely solid red head | **Red-headed Woodpecker** |
| Black mask + yellow body | **Common Yellowthroat** |

## ⚠️ IMPORTANT NOTES:
- Many birds appear brown (female finches, sparrows, wrens, thrushes) - don't ID based on "brown" alone!
- Check BEAK COLOR first - it's often the clearest diagnostic
- If unsure between species, list both with appropriate confidence levels
- Count ONLY birds you can CLEARLY identify

## OUTPUT FORMAT
Respond with valid JSON only:
```json
{{"birds": [{{"name": "Species Name", "scientific_name": "Genus species", "confidence": 75, "reason": "BEAK: [color/shape], HEAD: [pattern observed], BODY: [colors/patterns]. These features are diagnostic for [species]."}}]}}
```"""


# ============ ENHANCED IMAGE PROMPT (HIGH ACCURACY) ============
# Uses systematic field marks + India context

IMAGE_PROMPT_ENHANCED = """You are Dr. Salim Ali analyzing a bird photograph with your expert eye.

## 🔍 SYSTEMATIC FIELD MARK ANALYSIS

Follow this EXACT sequence to identify the bird:

### 1️⃣ OVERALL SIZE & SHAPE (First Impression)
- **Size**: Sparrow (12-15cm), Bulbul (18-22cm), Myna (23-27cm), Crow (40-50cm), Eagle (60+cm)
- **Shape**: Compact, slender, plump, long-tailed, crested

### 2️⃣ BEAK (Most Diagnostic Feature!)
| Beak Type | Color | Indicates |
|-----------|-------|-----------|
| Heavy, conical | Pink/orange | Finches, Sparrows |
| Heavy, conical | Red/orange | Zebra Finch, Parrot-finch |
| Thin, pointed | Black | Warblers, Flycatchers |
| Curved down | Variable | Sunbirds, Flowerpeckers |
| Hooked | Yellow/black | Raptors, Shrikes |
| Large, colorful | Bright red/yellow | Hornbills, Barbets |
| Short, wide | Variable | Nightjars, Swifts |

### 3️⃣ HEAD PATTERN (Key Identifier)
- **Crown**: Color, crest present?
- **Supercilium**: Eyebrow stripe present?
- **Eye ring**: Present? Color?
- **Eye stripe**: Through eye?
- **Cheek patches**: Color, shape
- **Moustache/Malar**: Present?

### 4️⃣ BODY PLUMAGE
- **Throat**: Color, pattern
- **Breast**: Plain, streaked, spotted, barred
- **Belly**: Color
- **Back/Mantle**: Color, pattern
- **Rump**: Often distinctive

### 5️⃣ WINGS & TAIL
- **Wing bars**: Number, color
- **Wing patches**: White, colored
- **Tail**: Length, shape (forked, square, rounded, graduated)
- **Tail pattern**: White tips/edges

### 6️⃣ LEGS (Often Overlooked!)
- Pink/flesh = Many songbirds
- Yellow = Some raptors, wagtails
- Red/orange = Many waterbirds, some pigeons
- Black = Starlings, many others
- Blue-grey = Herons, kingfishers

## 🇮🇳 COMMON INDIAN BIRDS - QUICK REFERENCE

| Key Features | Bird |
|--------------|------|
| Green body, red beak, long tail | Rose-ringed Parakeet |
| Iridescent green/blue, rufous wings | Indian Roller |
| Brown, yellow eye patch, white wing flash | Common Myna |
| Black, long forked tail, red eyes | Black Drongo |
| Brown, red vent, slight crest | Red-vented Bulbul |
| Black head, red ear patch, crest | Red-whiskered Bulbul |
| Blue body, chestnut head, huge bill | White-throated Kingfisher |
| Bright yellow, black mask | Baya Weaver |
| Black body, brilliant orange | Orange-headed Thrush |
| Iridescent purple/green, long curved bill | Purple Sunbird |

## ⚠️ CRITICAL RULES
1. **Don't guess** - if unclear, say "cannot identify" with reason
2. **Check BEAK first** - it's the best diagnostic
3. **Count visible birds** - identify ONLY birds clearly visible
4. **Partial views** - lower confidence for obscured birds
5. **Similar species** - mention if multiple species possible

## OUTPUT FORMAT (JSON only):
```json
{{"birds": [
  {{
    "name": "Common Name",
    "scientific_name": "Genus species",
    "confidence": 80,
    "reason": "BEAK: [color/shape], HEAD: [pattern], BODY: [main features]. These field marks diagnostic for [species]."
  }}
]}}
```"""


def get_image_prompt(backend: str = "auto", enhanced: bool = True) -> str:
    """Get image prompt optimized for the backend."""
    if enhanced:
        return IMAGE_PROMPT_ENHANCED
    if backend == "litellm" or backend == "gpt":
        return IMAGE_PROMPT_GPT
    return IMAGE_PROMPT_OLLAMA


# ============ DESCRIPTION IDENTIFICATION ============

DESCRIPTION_PROMPT_OLLAMA = """Ornithologist: identify bird from description.

DESCRIPTION: "{description}"

Match features to known species:
- Colors/patterns mentioned
- Size descriptions  
- Behavior
- Habitat/location
- Sounds described

JSON only:
{{"birds": [{{"name": "Species", "scientific_name": "Genus species", "confidence": 70, "reason": "Matched features: [x]"}}]}}"""


DESCRIPTION_PROMPT_GPT = """You are a world-class ornithologist helping identify a bird from a user's description.

## USER'S DESCRIPTION:
"{description}"

## ANALYSIS APPROACH:
1. Extract all mentioned features (colors, patterns, size, behavior, sounds)
2. Consider the geographic and seasonal context if mentioned
3. Match against known species based on feature combinations
4. Consider both common and less common species that fit

## FEATURE ANALYSIS:
- **Colors mentioned**: List all colors from description
- **Size references**: Any size comparisons?
- **Behavior**: Flight pattern? Feeding? Singing?
- **Habitat**: Where was it seen?
- **Sounds**: Any vocalizations described?

## OUTPUT FORMAT:
Provide your best identification(s) as valid JSON:
```json
{{"birds": [{{"name": "Species Name", "scientific_name": "Genus species", "confidence": 75, "reason": "Description mentions [features] which match [species] because [explanation]."}}]}}
```"""


def get_description_prompt(backend: str = "auto") -> str:
    """Get description prompt optimized for the backend."""
    if backend == "litellm" or backend == "gpt":
        return DESCRIPTION_PROMPT_GPT
    return DESCRIPTION_PROMPT_OLLAMA


# ============ LEGACY EXPORTS (for backward compatibility) ============
# These are the default prompts used when backend isn't specified

AUDIO_IDENTIFICATION_PROMPT = AUDIO_PROMPT_GPT
IMAGE_IDENTIFICATION_PROMPT = IMAGE_PROMPT_GPT  
DESCRIPTION_IDENTIFICATION_PROMPT = DESCRIPTION_PROMPT_GPT


# ============ FREQUENCY BAND GUIDELINES ============

FREQUENCY_GUIDELINES = """
Frequency bands correlate with bird size (physics of sound production):
- 100-500 Hz: Very large birds (owls hooting, bitterns booming)
- 500-1500 Hz: Large birds (crows cawing, doves cooing, owls screeching)
- 1500-3000 Hz: Medium-large (thrushes, mynas, cuckoos)
- 3000-6000 Hz: Small-medium (finches, sparrows, most songbirds)
- 6000-10000 Hz: Very small (warblers, goldcrests, high-pitched calls)
"""


# ============ BIRD ENRICHMENT PROMPT ============

BIRD_ENRICHMENT_PROMPT = """Provide factual, research-quality information about the {bird_name} ({scientific_name}).

Return ONLY valid JSON with these fields:
{{
    "summary": "2-3 sentence scientific overview of the species",
    "habitat": "Primary habitat description (forests, grasslands, urban areas, etc.)",
    "diet": "What this bird eats (seeds, insects, nectar, etc.)",
    "fun_facts": [
        "Interesting scientific or behavioral fact 1",
        "Interesting scientific or behavioral fact 2"
    ],
    "conservation": "IUCN status: LC (Least Concern), NT (Near Threatened), VU (Vulnerable), EN (Endangered), or CR (Critically Endangered)",
    "range": "Geographic distribution",
    "breeding": "Brief breeding behavior note"
}}

Be scientifically accurate. No markdown, only JSON."""


BIRD_ENRICHMENT_PROMPT_INDIA = """Provide factual, research-quality information about the {bird_name} ({scientific_name}), with special focus on its presence in India.

Return ONLY valid JSON with these fields:
{{
    "summary": "2-3 sentence scientific overview",
    "habitat": "Habitat in India specifically (if found there) or general habitat",
    "diet": "What this bird eats",
    "fun_facts": [
        "Interesting fact about this bird",
        "India-specific fact if applicable (migration patterns to India, cultural significance, etc.)"
    ],
    "conservation": "IUCN status (LC/NT/VU/EN/CR)",
    "range": "Geographic range, emphasizing presence in India if applicable",
    "india_info": {{
        "found_in_india": true/false,
        "regions": "States/regions in India where found (if applicable)",
        "local_names": {{
            "hindi": "Hindi name if known",
            "tamil": "Tamil name if known", 
            "bengali": "Bengali name if known",
            "marathi": "Marathi name if known",
            "kannada": "Kannada name if known"
        }},
        "best_season": "Best time to spot in India",
        "notable_locations": "Famous birding spots in India for this species"
    }}
}}

For birds NOT found in India, set india_info.found_in_india to false and leave other india fields empty.
Be scientifically accurate. No markdown, only JSON."""


def get_enrichment_prompt(bird_name: str, scientific_name: str, location: str = "") -> str:
    """Get enrichment prompt, with India-specific version if location is India."""
    location_lower = location.lower() if location else ""
    is_india = any(term in location_lower for term in ["india", "mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "kerala", "goa", "rajasthan", "gujarat", "maharashtra", "tamil", "karnataka", "bengal"])
    
    if is_india:
        return BIRD_ENRICHMENT_PROMPT_INDIA.format(bird_name=bird_name, scientific_name=scientific_name)
    else:
        return BIRD_ENRICHMENT_PROMPT.format(bird_name=bird_name, scientific_name=scientific_name)
