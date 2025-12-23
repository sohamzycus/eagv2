"""
🐦 BirdSense eBird Integration
Developed by Soham

Integration with eBird API for:
1. Recent sightings in an area
2. Species expected at a location
3. Regional bird lists
4. Rare bird alerts
"""

import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

# eBird API configuration
EBIRD_API_URL = "https://api.ebird.org/v2"
# Note: Users need to get their own API key from https://ebird.org/api/keygen
EBIRD_API_KEY = os.environ.get("EBIRD_API_KEY", "")


class EBirdClient:
    """
    Client for eBird API integration.
    
    Provides:
    - Recent sightings by location
    - Species lists for hotspots
    - Regional statistics
    - Rare bird alerts
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or EBIRD_API_KEY
        self.headers = {"X-eBirdApiToken": self.api_key} if self.api_key else {}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[List]:
        """Make API request to eBird."""
        if not self.api_key:
            print("Warning: eBird API key not configured")
            return None
        
        url = f"{EBIRD_API_URL}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"eBird API error: {e}")
            return None
    
    def get_recent_observations(self, lat: float, lon: float, 
                                 days: int = 14, max_results: int = 50) -> List[Dict]:
        """
        Get recent bird observations near a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days back to search (max 30)
            max_results: Maximum number of results
        
        Returns:
            List of recent observations with species info
        """
        endpoint = "/data/obs/geo/recent"
        params = {
            "lat": lat,
            "lng": lon,
            "back": min(days, 30),
            "maxResults": max_results,
            "includeProvisional": True
        }
        
        observations = self._make_request(endpoint, params)
        
        if not observations:
            return []
        
        # Format observations
        formatted = []
        for obs in observations:
            formatted.append({
                "common_name": obs.get("comName", ""),
                "scientific_name": obs.get("sciName", ""),
                "count": obs.get("howMany", 1),
                "date": obs.get("obsDt", ""),
                "location": obs.get("locName", ""),
                "lat": obs.get("lat"),
                "lon": obs.get("lng")
            })
        
        return formatted
    
    def get_recent_notable(self, region_code: str, days: int = 7) -> List[Dict]:
        """
        Get recent notable/rare observations in a region.
        
        Args:
            region_code: eBird region code (e.g., "IN" for India, "IN-KA" for Karnataka)
            days: Number of days back
        
        Returns:
            List of notable observations
        """
        endpoint = f"/data/obs/{region_code}/recent/notable"
        params = {"back": min(days, 30)}
        
        observations = self._make_request(endpoint, params)
        
        if not observations:
            return []
        
        formatted = []
        for obs in observations:
            formatted.append({
                "common_name": obs.get("comName", ""),
                "scientific_name": obs.get("sciName", ""),
                "date": obs.get("obsDt", ""),
                "location": obs.get("locName", ""),
                "is_rare": True
            })
        
        return formatted
    
    @lru_cache(maxsize=100)
    def get_region_species_list(self, region_code: str) -> List[str]:
        """
        Get list of species recorded in a region.
        
        Args:
            region_code: eBird region code
        
        Returns:
            List of species common names
        """
        endpoint = f"/product/spplist/{region_code}"
        
        species_codes = self._make_request(endpoint)
        
        if not species_codes:
            return []
        
        # Convert species codes to names (simplified)
        # In production, you'd use the taxonomy endpoint
        return species_codes[:200]  # Return top 200
    
    def get_hotspot_info(self, hotspot_id: str) -> Optional[Dict]:
        """Get information about a birding hotspot."""
        endpoint = f"/ref/hotspot/info/{hotspot_id}"
        return self._make_request(endpoint)
    
    def search_hotspots(self, lat: float, lon: float, 
                        radius_km: int = 25) -> List[Dict]:
        """
        Find birding hotspots near a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
        
        Returns:
            List of hotspots with details
        """
        endpoint = "/ref/hotspot/geo"
        params = {
            "lat": lat,
            "lng": lon,
            "dist": min(radius_km, 50),
            "fmt": "json"
        }
        
        hotspots = self._make_request(endpoint, params)
        
        if not hotspots:
            return []
        
        formatted = []
        for hs in hotspots[:20]:
            formatted.append({
                "name": hs.get("locName", ""),
                "id": hs.get("locId", ""),
                "lat": hs.get("lat"),
                "lon": hs.get("lng"),
                "species_count": hs.get("numSpeciesAllTime", 0)
            })
        
        return formatted


# ===============================================================================
# INDIA-SPECIFIC REGION CODES
# ===============================================================================

INDIA_REGION_CODES = {
    # States
    "Karnataka": "IN-KA",
    "Kerala": "IN-KL", 
    "Tamil Nadu": "IN-TN",
    "Andhra Pradesh": "IN-AP",
    "Telangana": "IN-TG",
    "Maharashtra": "IN-MH",
    "Gujarat": "IN-GJ",
    "Rajasthan": "IN-RJ",
    "Madhya Pradesh": "IN-MP",
    "Uttar Pradesh": "IN-UP",
    "Bihar": "IN-BR",
    "West Bengal": "IN-WB",
    "Odisha": "IN-OR",
    "Assam": "IN-AS",
    "Meghalaya": "IN-ML",
    "Arunachal Pradesh": "IN-AR",
    "Nagaland": "IN-NL",
    "Manipur": "IN-MN",
    "Mizoram": "IN-MZ",
    "Tripura": "IN-TR",
    "Sikkim": "IN-SK",
    "Himachal Pradesh": "IN-HP",
    "Uttarakhand": "IN-UT",
    "Punjab": "IN-PB",
    "Haryana": "IN-HR",
    "Delhi": "IN-DL",
    "Jammu and Kashmir": "IN-JK",
    "Ladakh": "IN-LA",
    "Goa": "IN-GA",
    "Jharkhand": "IN-JH",
    "Chhattisgarh": "IN-CT",
    
    # Cities (commonly used)
    "Bangalore": "IN-KA",
    "Bengaluru": "IN-KA",
    "Mumbai": "IN-MH",
    "Delhi": "IN-DL",
    "Chennai": "IN-TN",
    "Kolkata": "IN-WB",
    "Hyderabad": "IN-TG",
    "Pune": "IN-MH",
    "Ahmedabad": "IN-GJ",
    
    # Regions
    "Western Ghats": "IN-KA",
    "Himalayas": "IN-UT",
    "Northeast India": "IN-AS",
    "India": "IN"
}

# Famous birding hotspots in India
INDIA_HOTSPOTS = {
    "Bharatpur": {
        "id": "L745607",
        "name": "Keoladeo National Park",
        "state": "Rajasthan",
        "coordinates": (27.1591, 77.5225),
        "specialties": ["Siberian Crane", "Sarus Crane", "Painted Stork"]
    },
    "Ranganathittu": {
        "id": "L2353897",
        "name": "Ranganathittu Bird Sanctuary",
        "state": "Karnataka", 
        "coordinates": (12.4241, 76.6612),
        "specialties": ["River Tern", "Black-headed Ibis", "Painted Stork"]
    },
    "Thattekad": {
        "id": "L947377",
        "name": "Thattekad Bird Sanctuary",
        "state": "Kerala",
        "coordinates": (10.1199, 76.7372),
        "specialties": ["Malabar Grey Hornbill", "Sri Lanka Frogmouth", "Malabar Trogon"]
    },
    "Chilika": {
        "id": "L870449",
        "name": "Chilika Lake",
        "state": "Odisha",
        "coordinates": (19.8, 85.45),
        "specialties": ["Flamingos", "Irrawaddy Dolphin sightings", "Migratory waterfowl"]
    },
    "Corbett": {
        "id": "L2353925",
        "name": "Jim Corbett National Park",
        "state": "Uttarakhand",
        "coordinates": (29.5300, 78.7747),
        "specialties": ["Wallcreeper", "Great Hornbill", "Ibisbill"]
    },
    "Kaziranga": {
        "id": "L1041618",
        "name": "Kaziranga National Park",
        "state": "Assam",
        "coordinates": (26.5775, 93.1711),
        "specialties": ["Bengal Florican", "Swamp Francolin", "Greater Adjutant"]
    }
}


def get_region_code(location: str) -> str:
    """Get eBird region code from location string."""
    location_lower = location.lower()
    
    for name, code in INDIA_REGION_CODES.items():
        if name.lower() in location_lower:
            return code
    
    # Default to all of India
    return "IN"


def get_location_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """
    Get approximate coordinates for a location.
    
    In production, you'd use a geocoding service.
    """
    # Common Indian city coordinates
    CITY_COORDS = {
        "bangalore": (12.9716, 77.5946),
        "bengaluru": (12.9716, 77.5946),
        "mumbai": (19.0760, 72.8777),
        "delhi": (28.6139, 77.2090),
        "chennai": (13.0827, 80.2707),
        "kolkata": (22.5726, 88.3639),
        "hyderabad": (17.3850, 78.4867),
        "pune": (18.5204, 73.8567),
        "ahmedabad": (23.0225, 72.5714),
        "jaipur": (26.9124, 75.7873),
        "goa": (15.2993, 74.1240),
        "shimla": (31.1048, 77.1734),
        "darjeeling": (27.0410, 88.2663),
        "guwahati": (26.1445, 91.7362),
        "kochi": (9.9312, 76.2673),
        "mysore": (12.2958, 76.6394),
        "ooty": (11.4102, 76.6950)
    }
    
    location_lower = location.lower()
    
    for city, coords in CITY_COORDS.items():
        if city in location_lower:
            return coords
    
    # Check hotspots
    for name, info in INDIA_HOTSPOTS.items():
        if name.lower() in location_lower:
            return info["coordinates"]
    
    return None


class LocationAwareBirdContext:
    """
    Provides location-aware bird context for identification.
    
    Combines:
    - eBird recent sightings
    - Regional species lists
    - Seasonal expectations
    - Hotspot information
    """
    
    def __init__(self):
        self.ebird = EBirdClient()
    
    def get_context_for_location(self, location: str, month: str = None) -> Dict:
        """
        Get comprehensive bird context for a location.
        
        Returns:
            Dict with expected species, recent sightings, hotspots
        """
        context = {
            "location": location,
            "expected_species": [],
            "recent_sightings": [],
            "nearby_hotspots": [],
            "rare_alerts": []
        }
        
        # Get coordinates
        coords = get_location_coordinates(location)
        if coords:
            lat, lon = coords
            
            # Get recent observations
            recent = self.ebird.get_recent_observations(lat, lon, days=14)
            if recent:
                context["recent_sightings"] = recent[:20]
                context["expected_species"] = list(set(
                    obs["common_name"] for obs in recent
                ))
            
            # Get nearby hotspots
            hotspots = self.ebird.search_hotspots(lat, lon, radius_km=25)
            if hotspots:
                context["nearby_hotspots"] = hotspots[:10]
        
        # Get region code and notable sightings
        region_code = get_region_code(location)
        notable = self.ebird.get_recent_notable(region_code, days=7)
        if notable:
            context["rare_alerts"] = notable[:10]
        
        return context
    
    def build_prompt_context(self, location: str, month: str = None) -> str:
        """
        Build prompt context string for LLM.
        
        Returns formatted string with bird expectations.
        """
        context = self.get_context_for_location(location, month)
        
        prompt_parts = []
        
        # Add expected species
        if context["expected_species"]:
            species_list = ", ".join(context["expected_species"][:30])
            prompt_parts.append(f"**Birds recently seen in {location}:** {species_list}")
        
        # Add rare alerts
        if context["rare_alerts"]:
            rare_list = ", ".join(r["common_name"] for r in context["rare_alerts"][:5])
            prompt_parts.append(f"**Rare birds recently reported:** {rare_list}")
        
        # Add hotspot info
        if context["nearby_hotspots"]:
            hotspot_names = ", ".join(h["name"] for h in context["nearby_hotspots"][:5])
            prompt_parts.append(f"**Nearby birding hotspots:** {hotspot_names}")
        
        if prompt_parts:
            return "\n".join(prompt_parts) + "\n"
        
        return ""


# Fallback data when API is not available
def get_fallback_expected_species(location: str, month: int) -> List[str]:
    """Get expected species without API (using static data)."""
    from enhanced_prompts import INDIA_REGIONAL_BIRDS
    
    location_lower = location.lower()
    
    # Determine region
    if any(x in location_lower for x in ["kerala", "karnataka", "western ghats", "nilgiri"]):
        birds = INDIA_REGIONAL_BIRDS.get("Western Ghats", {})
    elif any(x in location_lower for x in ["himalaya", "uttarakhand", "himachal", "sikkim"]):
        birds = INDIA_REGIONAL_BIRDS.get("Himalayas", {})
    elif any(x in location_lower for x in ["assam", "meghalaya", "arunachal", "northeast"]):
        birds = INDIA_REGIONAL_BIRDS.get("Northeast India", {})
    else:
        birds = INDIA_REGIONAL_BIRDS.get("South India", {})
    
    # Flatten all species
    all_species = []
    for category_birds in birds.values():
        all_species.extend(category_birds)
    
    return all_species[:30]


# Test
if __name__ == "__main__":
    print("Testing eBird Integration...")
    
    # Test without API key
    context = LocationAwareBirdContext()
    
    # Test location parsing
    print("\nTesting location coordinates:")
    for loc in ["Bangalore", "Thattekad", "Darjeeling", "Unknown Place"]:
        coords = get_location_coordinates(loc)
        print(f"  {loc}: {coords}")
    
    print("\nTesting region codes:")
    for loc in ["Karnataka", "Mumbai", "Western Ghats", "Unknown"]:
        code = get_region_code(loc)
        print(f"  {loc}: {code}")
    
    print("\nTesting fallback species:")
    species = get_fallback_expected_species("Kerala", 3)
    print(f"  Kerala March: {species[:10]}")
    
    print("\n✅ eBird integration ready (API key needed for live data)")

