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


# Combined prompt function for audio
def get_audio_prompt(backend: str = "auto") -> str:
    """Get audio prompt optimized for the backend."""
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


def get_image_prompt(backend: str = "auto") -> str:
    """Get image prompt optimized for the backend."""
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
