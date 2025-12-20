"""
🐦 BirdSense Feature-Based Validation

This module provides FEATURE-BASED validation, NOT hardcoded species rules.
The goal is to help the LLM focus on distinguishing features, not to make
rigid "brown = sparrow" type assumptions.

Key principle: Identify by FEATURES, not by color alone.
Many birds are brown (sparrows, wrens, female finches, thrushes, etc.)
"""

# ============ FEATURE IMPORTANCE WEIGHTS ============
# These guide the LLM on what features matter most for identification

FEATURE_PRIORITIES = {
    "beak_color": 0.95,       # Very diagnostic
    "beak_shape": 0.90,       # Conical vs thin vs hooked
    "face_pattern": 0.85,     # Cheek patches, eye rings, stripes
    "head_pattern": 0.85,     # Caps, crowns, crests
    "breast_pattern": 0.80,   # Streaking, spots, plain
    "wing_pattern": 0.75,     # Wing bars, patches
    "tail_pattern": 0.70,
    "overall_color": 0.65,    # Less reliable - many birds share colors
    "size": 0.60,
    "behavior": 0.55,
}

# ============ CRITICAL DIAGNOSTIC FEATURES ============
# These are features that STRONGLY indicate specific species
# NOT rigid rules, but strong indicators

DIAGNOSTIC_FEATURES = {
    # Finches
    "orange_cheek_patch": ["Zebra Finch"],
    "red_orange_beak_small_bird": ["Zebra Finch", "Orange-cheeked Waxbill"],
    "bright_yellow_body_black_cap": ["American Goldfinch (male)"],
    "olive_yellow_body_wing_bars": ["American Goldfinch (female)", "Lesser Goldfinch"],
    
    # Sparrows (many species are brown - don't assume House Sparrow!)
    "grey_crown_black_bib": ["House Sparrow (male)"],
    "brown_streaky_plain_face": ["House Sparrow (female)", "Song Sparrow", "multiple sparrow species"],
    "rufous_cap_grey_cheek": ["Chipping Sparrow"],
    "yellow_lores": ["White-throated Sparrow"],
    "black_cheek_spot": ["Eurasian Tree Sparrow"],
    
    # Woodpeckers
    "entire_head_red": ["Red-headed Woodpecker"],
    "red_nape_only_barred_back": ["Red-bellied Woodpecker"],
    "red_crown_black_white_face": ["Downy Woodpecker", "Hairy Woodpecker"],
}

# ============ COMMONLY CONFUSED PAIRS ============
# Educational info for users, NOT for automatic correction

CONFUSION_PAIRS = {
    "Zebra Finch vs American Goldfinch": {
        "key_difference": "Zebra Finch: RED/ORANGE beak + orange cheek. Goldfinch: YELLOW body + pale beak.",
        "common_error": "AI models confuse them because both are small finches.",
    },
    "House Sparrow vs Other Sparrows": {
        "key_difference": "House Sparrow male: grey crown, black bib. Female: plain face, no streaking on breast.",
        "common_error": "Many sparrows look similar. Don't assume all brown small birds are House Sparrows!",
    },
    "Red-headed vs Red-bellied Woodpecker": {
        "key_difference": "Red-headed: ENTIRE head solid red. Red-bellied: only red on NAPE.",
        "common_error": "Name is misleading - Red-bellied has barely visible red on belly.",
    },
}

# ============ HELPFUL HINTS FOR UI ============

def get_confusion_hint(bird_name: str) -> str:
    """Get educational hint about commonly confused species."""
    hints = {
        "Zebra Finch": "Key features: RED/ORANGE beak + orange cheek patch + grey body",
        "American Goldfinch": "Key features: YELLOW body (even females are olive-yellow) + pale beak",
        "House Sparrow": "Male: grey crown + black bib. Female: plain brown, unstreaked breast",
        "House Finch": "Male: red on head/breast. Female: brown with streaky breast",
        "Red-headed Woodpecker": "ENTIRE head solid red (not just crown or nape)",
        "Red-bellied Woodpecker": "Red on NAPE only, not entire head. Barred black-white back",
    }
    
    for key, hint in hints.items():
        if key.lower() in bird_name.lower():
            return hint
    return ""


# ============ FEATURE-BASED VALIDATION ============
# Instead of hardcoded rules, we validate based on feature consistency

def validate_features(predicted_name: str, observed_features: dict) -> dict:
    """
    Validate a prediction based on observed features.
    Returns warnings if features don't match expected pattern.
    
    This is ADVISORY, not automatic correction.
    """
    result = {
        "prediction": predicted_name,
        "warnings": [],
        "confidence_adjustment": 0,
        "suggestion": None
    }
    
    pred_lower = predicted_name.lower()
    
    # Check for American Goldfinch without yellow
    if "goldfinch" in pred_lower:
        body_color = observed_features.get("body_color", "").lower()
        has_yellow = "yellow" in body_color or "gold" in body_color or "olive" in body_color
        
        if not has_yellow and body_color:
            result["warnings"].append(
                f"⚠️ American Goldfinch typically has yellow/olive coloring. Observed: {body_color}"
            )
            result["confidence_adjustment"] = -15
            result["suggestion"] = "Double-check: Could this be a different species?"
    
    # Check for Zebra Finch without orange cheek
    if "zebra finch" in pred_lower:
        cheek = observed_features.get("cheek_pattern", "").lower()
        beak = observed_features.get("beak_color", "").lower()
        
        if cheek and "orange" not in cheek:
            result["warnings"].append(
                f"⚠️ Zebra Finch has distinctive orange cheek patch. Observed: {cheek}"
            )
            result["confidence_adjustment"] = -10
        
        if beak and "red" not in beak and "orange" not in beak:
            result["warnings"].append(
                f"⚠️ Zebra Finch has red/orange beak. Observed: {beak}"
            )
            result["confidence_adjustment"] = -10
    
    return result


# Legacy function for backward compatibility
def check_finch_confusion(predicted_name: str, description: str) -> dict:
    """
    Soft validation - returns suggestion if there might be confusion.
    Does NOT make rigid "brown = sparrow" assumptions.
    """
    # Return None - we don't make automatic corrections anymore
    # The improved prompts should guide the LLM to better identification
    return None


def validate_bird_identification(predicted_name: str, visual_features: dict) -> dict:
    """
    Feature-based validation (not species-based rules).
    """
    return {
        "validated": True,
        "original_prediction": predicted_name,
        "correction": None,
        "confidence_adjustment": 0,
        "warnings": []
    }


# Keep CONFUSION_HINTS for UI display
CONFUSION_HINTS = {
    "Zebra Finch": "Key ID: Red/orange beak + orange cheek patch + grey body with barred chest",
    "American Goldfinch": "Key ID: Yellow body (males bright, females olive-yellow) + pale beak + wing bars",
    "House Sparrow": "Key ID: Male has grey crown + black bib. Female is plain brown with unstreaked breast",
    "House Finch": "Key ID: Male has red on forehead/breast. Female has streaky breast (unlike House Sparrow)",
    "Red-headed Woodpecker": "Key ID: ENTIRE head solid red. Black back with white patches",
    "Red-bellied Woodpecker": "Key ID: Red on nape/back of head only. Barred black-white back",
}
