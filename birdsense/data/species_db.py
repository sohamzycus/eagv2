"""
India Bird Species Database for BirdSense.

Contains information about Indian bird species including:
- Scientific and common names
- Habitat information
- Conservation status
- Geographic range
- Vocalization descriptions

Primary source: India Biodiversity Portal, eBird, IUCN
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class SpeciesInfo:
    """Information about a bird species."""
    id: int
    scientific_name: str
    common_name: str
    hindi_name: Optional[str] = None
    family: str = ""
    order: str = ""
    
    # Status
    conservation_status: str = "LC"  # LC, NT, VU, EN, CR
    endemic_to_india: bool = False
    migratory_status: str = "Resident"  # Resident, Winter Visitor, Summer Visitor, Passage Migrant
    
    # Habitat
    habitats: List[str] = field(default_factory=list)
    elevation_min: int = 0  # meters
    elevation_max: int = 5000
    
    # Range
    states: List[str] = field(default_factory=list)
    range_description: str = ""
    
    # Vocalization
    call_description: str = ""
    song_description: str = ""
    call_frequency_range: tuple = (0, 10000)  # Hz
    
    # For model
    class_index: int = 0


class IndiaSpeciesDatabase:
    """
    Database of Indian bird species.
    
    Provides species information for:
    - Model training (class labels)
    - LLM reasoning (species context)
    - Novelty detection (range checking)
    """
    
    def __init__(self):
        self.species: Dict[int, SpeciesInfo] = {}
        self.name_to_id: Dict[str, int] = {}
        self._init_species()
    
    def _init_species(self):
        """Initialize with common Indian bird species."""
        # This is a representative sample - full database would have 1300+ species
        species_data = [
            # Cuckoos
            SpeciesInfo(
                id=0, 
                scientific_name="Cuculus micropterus",
                common_name="Indian Cuckoo",
                hindi_name="कोयल",
                family="Cuculidae",
                order="Cuculiformes",
                conservation_status="LC",
                migratory_status="Summer Visitor",
                habitats=["Forest", "Woodland"],
                elevation_min=0, elevation_max=3000,
                states=["All India"],
                call_description="Four-note whistle 'cross-word puzzle' or 'one more bottle'",
                call_frequency_range=(1000, 3000),
                class_index=0
            ),
            SpeciesInfo(
                id=1,
                scientific_name="Eudynamys scolopaceus", 
                common_name="Asian Koel",
                hindi_name="कोयल",
                family="Cuculidae",
                order="Cuculiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Forest", "Urban", "Garden"],
                elevation_min=0, elevation_max=1800,
                states=["All India"],
                call_description="Loud 'kuil-kuil-kuil' rising whistle, very distinctive",
                call_frequency_range=(500, 4000),
                class_index=1
            ),
            
            # Robins and Thrushes
            SpeciesInfo(
                id=2,
                scientific_name="Copsychus saularis",
                common_name="Oriental Magpie-Robin", 
                hindi_name="दहियर",
                family="Muscicapidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Forest edge", "Urban"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Rich varied song with whistles and mimicry",
                call_frequency_range=(1500, 5000),
                class_index=2
            ),
            SpeciesInfo(
                id=3,
                scientific_name="Saxicoloides fulicatus",
                common_name="Indian Robin",
                hindi_name="काली चिड़ी",
                family="Muscicapidae", 
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                endemic_to_india=True,
                habitats=["Scrub", "Garden", "Rocky areas"],
                elevation_min=0, elevation_max=1500,
                states=["Peninsular India"],
                call_description="Pleasant whistling song, alarm 'chip-chip'",
                call_frequency_range=(2000, 6000),
                class_index=3
            ),
            
            # Kingfishers
            SpeciesInfo(
                id=4,
                scientific_name="Alcedo atthis",
                common_name="Common Kingfisher",
                hindi_name="छोटा किलकिला",
                family="Alcedinidae",
                order="Coraciiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Wetland", "River", "Stream"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Sharp high-pitched 'chee' or 'kik-kik'",
                call_frequency_range=(4000, 8000),
                class_index=4
            ),
            SpeciesInfo(
                id=5,
                scientific_name="Halcyon smyrnensis",
                common_name="White-throated Kingfisher",
                hindi_name="किलकिला",
                family="Alcedinidae",
                order="Coraciiformes", 
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Open country", "Wetland", "Garden"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Loud laughing 'ki-ki-ki-ki' call",
                call_frequency_range=(2000, 6000),
                class_index=5
            ),
            
            # Galliformes
            SpeciesInfo(
                id=6,
                scientific_name="Pavo cristatus",
                common_name="Indian Peafowl",
                hindi_name="मोर",
                family="Phasianidae",
                order="Galliformes",
                conservation_status="LC",
                migratory_status="Resident",
                endemic_to_india=True,
                habitats=["Forest", "Scrub", "Cultivation"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Loud 'may-awe' call, especially during monsoon",
                call_frequency_range=(500, 2000),
                class_index=6
            ),
            SpeciesInfo(
                id=7,
                scientific_name="Gallus gallus",
                common_name="Red Junglefowl",
                hindi_name="जंगली मुर्गा",
                family="Phasianidae",
                order="Galliformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Forest", "Scrub"],
                elevation_min=0, elevation_max=2000,
                states=["All India except desert"],
                call_description="Crowing like domestic rooster but shorter",
                call_frequency_range=(500, 3000),
                class_index=7
            ),
            
            # Common Urban Birds  
            SpeciesInfo(
                id=8,
                scientific_name="Passer domesticus",
                common_name="House Sparrow",
                hindi_name="गौरैया",
                family="Passeridae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Urban", "Village", "Cultivation"],
                elevation_min=0, elevation_max=4000,
                states=["All India"],
                call_description="Chirping 'chip-chip' and 'cheep' calls",
                call_frequency_range=(2000, 6000),
                class_index=8
            ),
            SpeciesInfo(
                id=9,
                scientific_name="Acridotheres tristis",
                common_name="Common Myna",
                hindi_name="मैना",
                family="Sturnidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Urban", "Open country", "Cultivation"],
                elevation_min=0, elevation_max=3000,
                states=["All India"],
                call_description="Loud varied calls, harsh 'krrr', whistles",
                call_frequency_range=(1000, 5000),
                class_index=9
            ),
            
            # Barbets
            SpeciesInfo(
                id=10,
                scientific_name="Psilopogon haemacephalus",
                common_name="Coppersmith Barbet",
                hindi_name="छोटा बसंता",
                family="Megalaimidae",
                order="Piciformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Forest", "Urban"],
                elevation_min=0, elevation_max=1500,
                states=["All India"],
                call_description="Monotonous 'tuk-tuk-tuk' like hammer on metal",
                call_frequency_range=(1500, 3000),
                class_index=10
            ),
            SpeciesInfo(
                id=11,
                scientific_name="Psilopogon zeylanicus",
                common_name="Brown-headed Barbet",
                hindi_name="बड़ा बसंता",
                family="Megalaimidae",
                order="Piciformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Forest", "Garden"],
                elevation_min=0, elevation_max=2000,
                states=["Peninsular India"],
                call_description="Loud 'kutroo-kutroo' repeated",
                call_frequency_range=(1000, 3000),
                class_index=11
            ),
            
            # Parakeets
            SpeciesInfo(
                id=12,
                scientific_name="Psittacula krameri",
                common_name="Rose-ringed Parakeet",
                hindi_name="तोता",
                family="Psittacidae",
                order="Psittaciformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Urban", "Cultivation", "Forest"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Loud screeching 'kee-ak' in flight",
                call_frequency_range=(2000, 5000),
                class_index=12
            ),
            
            # Doves
            SpeciesInfo(
                id=13,
                scientific_name="Streptopelia chinensis",
                common_name="Spotted Dove",
                hindi_name="चित्रोक फाख्ता",
                family="Columbidae",
                order="Columbiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Cultivation", "Forest edge"],
                elevation_min=0, elevation_max=3000,
                states=["All India"],
                call_description="Soft cooing 'coo-coo-coo'",
                call_frequency_range=(300, 1500),
                class_index=13
            ),
            SpeciesInfo(
                id=14,
                scientific_name="Streptopelia decaocto",
                common_name="Eurasian Collared Dove",
                hindi_name="धूसर फाख्ता",
                family="Columbidae",
                order="Columbiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Urban", "Cultivation"],
                elevation_min=0, elevation_max=2500,
                states=["All India"],
                call_description="Three-note 'coo-COO-coo' with emphasis on middle",
                call_frequency_range=(400, 1200),
                class_index=14
            ),
            
            # Bulbuls
            SpeciesInfo(
                id=15,
                scientific_name="Pycnonotus cafer",
                common_name="Red-vented Bulbul",
                hindi_name="बुलबुल",
                family="Pycnonotidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Scrub", "Forest edge"],
                elevation_min=0, elevation_max=2500,
                states=["All India"],
                call_description="Cheerful 'be-care-ful' and chattering",
                call_frequency_range=(1500, 5000),
                class_index=15
            ),
            SpeciesInfo(
                id=16,
                scientific_name="Pycnonotus jocosus",
                common_name="Red-whiskered Bulbul",
                hindi_name="सिपाही बुलबुल",
                family="Pycnonotidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Forest edge", "Hill forest"],
                elevation_min=0, elevation_max=2500,
                states=["Peninsular India", "Himalayan foothills"],
                call_description="Pleasant whistles, 'kick-pettigrew'",
                call_frequency_range=(2000, 6000),
                class_index=16
            ),
            
            # Sunbirds
            SpeciesInfo(
                id=17,
                scientific_name="Cinnyris asiaticus",
                common_name="Purple Sunbird",
                hindi_name="शक्कर खोरा",
                family="Nectariniidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Scrub", "Forest edge"],
                elevation_min=0, elevation_max=2500,
                states=["All India"],
                call_description="Sharp 'chwit' and fast trilling song",
                call_frequency_range=(3000, 8000),
                class_index=17
            ),
            
            # Tailorbird
            SpeciesInfo(
                id=18,
                scientific_name="Orthotomus sutorius",
                common_name="Common Tailorbird",
                hindi_name="दर्जी चिड़िया",
                family="Cisticolidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Garden", "Scrub", "Forest undergrowth"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Loud 'towit-towit-towit' repeated",
                call_frequency_range=(3000, 6000),
                class_index=18
            ),
            
            # Owls
            SpeciesInfo(
                id=19,
                scientific_name="Athene brama",
                common_name="Spotted Owlet",
                hindi_name="खूसट",
                family="Strigidae",
                order="Strigiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Open country", "Cultivation", "Urban"],
                elevation_min=0, elevation_max=1500,
                states=["All India except dense forest"],
                call_description="Harsh chattering 'chirurr-chirurr'",
                call_frequency_range=(1000, 4000),
                class_index=19
            ),
            
            # Adding more diverse species for robust testing
            SpeciesInfo(
                id=20,
                scientific_name="Corvus splendens",
                common_name="House Crow",
                hindi_name="कौआ",
                family="Corvidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Urban", "Village"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Harsh 'kaa-kaa' cawing",
                call_frequency_range=(800, 2500),
                class_index=20
            ),
            SpeciesInfo(
                id=21,
                scientific_name="Dicrurus macrocercus",
                common_name="Black Drongo",
                hindi_name="कोतवाल",
                family="Dicruridae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Open country", "Cultivation"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Varied metallic calls and mimicry",
                call_frequency_range=(2000, 6000),
                class_index=21
            ),
            SpeciesInfo(
                id=22,
                scientific_name="Oriolus kundoo",
                common_name="Indian Golden Oriole",
                hindi_name="पीलक",
                family="Oriolidae",
                order="Passeriformes",
                conservation_status="LC",
                migratory_status="Summer Visitor",
                habitats=["Forest", "Garden", "Mango groves"],
                elevation_min=0, elevation_max=2500,
                states=["All India"],
                call_description="Fluty 'pee-lo' whistle",
                call_frequency_range=(1500, 4000),
                class_index=22
            ),
            SpeciesInfo(
                id=23,
                scientific_name="Upupa epops",
                common_name="Common Hoopoe",
                hindi_name="हुदहुद",
                family="Upupidae",
                order="Bucerotiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Open country", "Cultivation", "Garden"],
                elevation_min=0, elevation_max=3000,
                states=["All India"],
                call_description="Soft 'hoo-po-po' or 'oop-oop-oop'",
                call_frequency_range=(500, 2000),
                class_index=23
            ),
            SpeciesInfo(
                id=24,
                scientific_name="Merops orientalis",
                common_name="Green Bee-eater",
                hindi_name="हरियल पतरंगा",
                family="Meropidae",
                order="Coraciiformes",
                conservation_status="LC",
                migratory_status="Resident",
                habitats=["Open country", "Cultivation"],
                elevation_min=0, elevation_max=2000,
                states=["All India"],
                call_description="Soft trilling 'tree-tree-tree'",
                call_frequency_range=(3000, 7000),
                class_index=24
            ),
        ]
        
        for species in species_data:
            self.species[species.id] = species
            self.name_to_id[species.common_name.lower()] = species.id
            self.name_to_id[species.scientific_name.lower()] = species.id
            if species.hindi_name:
                self.name_to_id[species.hindi_name] = species.id
    
    def get_species(self, species_id: int) -> Optional[SpeciesInfo]:
        """Get species by ID."""
        return self.species.get(species_id)
    
    def get_by_name(self, name: str) -> Optional[SpeciesInfo]:
        """Get species by common or scientific name."""
        species_id = self.name_to_id.get(name.lower())
        if species_id is not None:
            return self.species.get(species_id)
        return None
    
    def get_all_species(self) -> List[SpeciesInfo]:
        """Get all species."""
        return list(self.species.values())
    
    def get_species_names(self) -> List[str]:
        """Get list of all common names in order of class index."""
        sorted_species = sorted(self.species.values(), key=lambda s: s.class_index)
        return [s.common_name for s in sorted_species]
    
    def get_num_classes(self) -> int:
        """Get number of species classes."""
        return len(self.species)
    
    def get_endemic_species(self) -> List[SpeciesInfo]:
        """Get species endemic to India."""
        return [s for s in self.species.values() if s.endemic_to_india]
    
    def get_conservation_priority(self, status: str = "VU") -> List[SpeciesInfo]:
        """Get species with conservation status at or above specified level."""
        priority_order = {"LC": 0, "NT": 1, "VU": 2, "EN": 3, "CR": 4}
        threshold = priority_order.get(status, 2)
        return [s for s in self.species.values() 
                if priority_order.get(s.conservation_status, 0) >= threshold]
    
    def get_species_for_llm_context(self, species_id: int) -> str:
        """Get formatted species information for LLM reasoning."""
        species = self.get_species(species_id)
        if not species:
            return "Species not found."
        
        return f"""
Species: {species.common_name} ({species.scientific_name})
Hindi Name: {species.hindi_name or 'N/A'}
Family: {species.family}
Conservation Status: {species.conservation_status}
Migratory Status: {species.migratory_status}
Endemic to India: {'Yes' if species.endemic_to_india else 'No'}
Habitats: {', '.join(species.habitats)}
Elevation Range: {species.elevation_min}m - {species.elevation_max}m
Distribution: {', '.join(species.states)}
Call Description: {species.call_description}
"""

    def search_by_habitat(self, habitat: str) -> List[SpeciesInfo]:
        """Find species by habitat type."""
        habitat_lower = habitat.lower()
        return [s for s in self.species.values() 
                if any(habitat_lower in h.lower() for h in s.habitats)]
    
    def to_json(self) -> str:
        """Export database to JSON."""
        data = {s.id: {
            "scientific_name": s.scientific_name,
            "common_name": s.common_name,
            "hindi_name": s.hindi_name,
            "family": s.family,
            "conservation_status": s.conservation_status,
            "endemic_to_india": s.endemic_to_india,
            "migratory_status": s.migratory_status,
            "habitats": s.habitats,
            "call_description": s.call_description,
            "class_index": s.class_index
        } for s in self.species.values()}
        return json.dumps(data, indent=2)

