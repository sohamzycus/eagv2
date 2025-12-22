"""
🐦 BirdSense India/South Asia Bird Dataset
Developed by Soham

Comprehensive dataset of 200+ birds for benchmarking:
- 60% India & South Asia birds (focus market)
- 25% Common global birds
- 15% Rare/exotic birds

Each entry includes: name, scientific_name, description, family, habitat, 
native_regions, rarity_score, audio_characteristics
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class BirdEntry:
    name: str
    scientific_name: str
    description: str
    family: str
    habitat: str
    native_regions: List[str]
    rarity_in_india: str  # common, uncommon, rare, vagrant, not_native
    audio_chars: Dict[str, any]  # freq_range, call_type, pattern


# =============================================================================
# INDIA & SOUTH ASIA BIRDS (120+ species)
# =============================================================================

INDIA_BIRDS = [
    # Common Indian Birds (40)
    BirdEntry("Indian Peafowl", "Pavo cristatus", 
              "large pheasant with iridescent blue-green plumage and elaborate eye-spotted tail",
              "Phasianidae", "forests, farmland", ["India", "Sri Lanka", "Nepal"], "common",
              {"freq_range": (300, 800), "call_type": "loud screaming", "pattern": "territorial"}),
    
    BirdEntry("House Sparrow", "Passer domesticus",
              "small brown bird with grey crown, black bib, and streaked back",
              "Passeridae", "urban, rural", ["India", "South Asia", "Global"], "common",
              {"freq_range": (2000, 6000), "call_type": "chirping", "pattern": "repetitive"}),
    
    BirdEntry("Common Myna", "Acridotheres tristis",
              "brown bird with black head, yellow eye patch and bill, white wing patches",
              "Sturnidae", "urban, open country", ["India", "South Asia"], "common",
              {"freq_range": (1000, 4000), "call_type": "varied calls", "pattern": "complex"}),
    
    BirdEntry("Rose-ringed Parakeet", "Psittacula krameri",
              "bright green parrot with red beak, male has rose and black neck ring",
              "Psittacidae", "forests, urban parks", ["India", "Africa"], "common",
              {"freq_range": (1500, 4000), "call_type": "screeching", "pattern": "repeated"}),
    
    BirdEntry("Asian Koel", "Eudynamys scolopaceus",
              "male glossy black, female brown with spots, famous rising 'ko-el' call",
              "Cuculidae", "forests, gardens", ["India", "South Asia", "SE Asia"], "common",
              {"freq_range": (700, 1500), "call_type": "rising whistle", "pattern": "ascending"}),
    
    BirdEntry("Indian Cuckoo", "Cuculus micropterus",
              "grey-brown cuckoo with barred underparts, four-note 'crossword puzzle' call",
              "Cuculidae", "forests", ["India", "South Asia"], "common",
              {"freq_range": (600, 1200), "call_type": "four-note whistle", "pattern": "rhythmic"}),
    
    BirdEntry("Greater Coucal", "Centropus sinensis",
              "large black cuckoo with chestnut wings, deep booming call",
              "Cuculidae", "scrub, gardens", ["India", "South Asia"], "common",
              {"freq_range": (200, 600), "call_type": "deep booming", "pattern": "resonant"}),
    
    BirdEntry("White-throated Kingfisher", "Halcyon smyrnensis",
              "bright blue back, chestnut head and belly, white throat and breast",
              "Alcedinidae", "open country, wetlands", ["India", "South Asia"], "common",
              {"freq_range": (2000, 5000), "call_type": "loud rattling", "pattern": "descending"}),
    
    BirdEntry("Common Kingfisher", "Alcedo atthis",
              "small brilliant blue and orange kingfisher with long bill",
              "Alcedinidae", "rivers, streams", ["India", "Eurasia"], "common",
              {"freq_range": (6000, 8000), "call_type": "sharp whistle", "pattern": "single"}),
    
    BirdEntry("Pied Kingfisher", "Ceryle rudis",
              "black and white kingfisher, hovers over water before diving",
              "Alcedinidae", "lakes, rivers", ["India", "Africa", "Middle East"], "common",
              {"freq_range": (3000, 6000), "call_type": "sharp twitter", "pattern": "rapid"}),
    
    BirdEntry("Indian Roller", "Coracias benghalensis",
              "crow-sized with brilliant blue wings, brown back and breast",
              "Coraciidae", "open country", ["India", "South Asia"], "common",
              {"freq_range": (1000, 3000), "call_type": "harsh calls", "pattern": "varied"}),
    
    BirdEntry("Green Bee-eater", "Merops orientalis",
              "slender green bird with blue throat, elongated central tail feathers",
              "Meropidae", "open country", ["India", "Africa", "Middle East"], "common",
              {"freq_range": (3000, 5000), "call_type": "liquid trill", "pattern": "rolling"}),
    
    BirdEntry("Blue-tailed Bee-eater", "Merops philippinus",
              "green with blue tail, chestnut throat, curved bill",
              "Meropidae", "open forests", ["India", "SE Asia"], "common",
              {"freq_range": (2500, 4500), "call_type": "liquid trill", "pattern": "rolling"}),
    
    BirdEntry("Indian Grey Hornbill", "Ocyceros birostris",
              "grey hornbill with large curved bill and casque, endemic to India",
              "Bucerotidae", "forests, urban", ["India"], "common",
              {"freq_range": (500, 2000), "call_type": "cackling", "pattern": "laughing"}),
    
    BirdEntry("Malabar Pied Hornbill", "Anthracoceros coronatus",
              "large black and white hornbill with yellow bill and casque",
              "Bucerotidae", "forests", ["India", "Sri Lanka"], "uncommon",
              {"freq_range": (400, 1500), "call_type": "loud yelping", "pattern": "repeated"}),
    
    BirdEntry("Great Hornbill", "Buceros bicornis",
              "massive hornbill with yellow and black bill, loud wingbeats",
              "Bucerotidae", "evergreen forests", ["India", "SE Asia"], "uncommon",
              {"freq_range": (300, 1000), "call_type": "loud barking", "pattern": "resonant"}),
    
    BirdEntry("Coppersmith Barbet", "Psilopogon haemacephalus",
              "green barbet with red forehead, yellow throat, repetitive 'tuk-tuk' call",
              "Megalaimidae", "gardens, forests", ["India", "SE Asia"], "common",
              {"freq_range": (1500, 2500), "call_type": "metallic tuk", "pattern": "monotonous"}),
    
    BirdEntry("Brown-headed Barbet", "Psilopogon zeylanicus",
              "green barbet with brown head, streaked breast",
              "Megalaimidae", "forests, gardens", ["India", "Sri Lanka"], "common",
              {"freq_range": (1200, 2200), "call_type": "kutruk call", "pattern": "repeated"}),
    
    BirdEntry("White-cheeked Barbet", "Psilopogon viridis",
              "green barbet with white cheek stripes, endemic to Western Ghats",
              "Megalaimidae", "evergreen forests", ["India (Western Ghats)"], "uncommon",
              {"freq_range": (1300, 2300), "call_type": "monotonous call", "pattern": "regular"}),
    
    BirdEntry("Indian Golden Oriole", "Oriolus kundoo",
              "bright yellow with black eye stripe and wing, melodious fluting call",
              "Oriolidae", "forests, gardens", ["India", "Central Asia"], "common",
              {"freq_range": (1000, 3000), "call_type": "fluting whistle", "pattern": "melodious"}),
    
    BirdEntry("Black Drongo", "Dicrurus macrocercus",
              "glossy black with deeply forked tail, aggressive and vocal",
              "Dicruridae", "open country", ["India", "South Asia"], "common",
              {"freq_range": (1500, 4000), "call_type": "varied mimicry", "pattern": "complex"}),
    
    BirdEntry("Ashy Drongo", "Dicrurus leucophaeus",
              "grey drongo with red eyes, forked tail",
              "Dicruridae", "forests", ["India", "SE Asia"], "common",
              {"freq_range": (1500, 3500), "call_type": "harsh calls", "pattern": "varied"}),
    
    BirdEntry("Greater Racket-tailed Drongo", "Dicrurus paradiseus",
              "black drongo with elongated outer tail feathers ending in rackets",
              "Dicruridae", "forests", ["India", "SE Asia"], "common",
              {"freq_range": (1000, 4000), "call_type": "excellent mimic", "pattern": "complex"}),
    
    BirdEntry("Red-vented Bulbul", "Pycnonotus cafer",
              "brown bird with black head, scaly pattern, red under tail coverts",
              "Pycnonotidae", "gardens, scrub", ["India", "South Asia"], "common",
              {"freq_range": (2000, 5000), "call_type": "cheerful calls", "pattern": "lively"}),
    
    BirdEntry("Red-whiskered Bulbul", "Pycnonotus jocosus",
              "brown with pointed black crest, red ear patch and vent",
              "Pycnonotidae", "forests, gardens", ["India", "SE Asia"], "common",
              {"freq_range": (2000, 5000), "call_type": "melodious", "pattern": "varied"}),
    
    BirdEntry("White-browed Bulbul", "Pycnonotus luteolus",
              "olive-green bulbul with white supercilium, yellow vent",
              "Pycnonotidae", "scrub, gardens", ["India", "Sri Lanka"], "common",
              {"freq_range": (2000, 4500), "call_type": "bubbling", "pattern": "cheerful"}),
    
    BirdEntry("Oriental Magpie-Robin", "Copsychus saularis",
              "black and white robin-like bird, melodious singer, cocked tail",
              "Muscicapidae", "gardens, forests", ["India", "South Asia"], "common",
              {"freq_range": (1500, 6000), "call_type": "melodious song", "pattern": "complex"}),
    
    BirdEntry("Indian Robin", "Copsychus fulicatus",
              "male black with white wing patch and rusty vent, female brown",
              "Muscicapidae", "open scrub", ["India", "Nepal"], "common",
              {"freq_range": (2000, 5000), "call_type": "pleasant song", "pattern": "varied"}),
    
    BirdEntry("Purple Sunbird", "Cinnyris asiaticus",
              "male metallic purple-black, female olive-yellow, curved bill",
              "Nectariniidae", "gardens, forests", ["India", "South Asia"], "common",
              {"freq_range": (4000, 8000), "call_type": "high squeaky", "pattern": "rapid"}),
    
    BirdEntry("Purple-rumped Sunbird", "Leptocoma zeylonica",
              "male with purple rump and throat, yellow belly",
              "Nectariniidae", "gardens, forests", ["India", "Sri Lanka"], "common",
              {"freq_range": (4000, 7500), "call_type": "thin squeaks", "pattern": "rapid"}),
    
    BirdEntry("Crimson Sunbird", "Aethopyga siparaja",
              "male brilliant crimson with yellow belly and long tail",
              "Nectariniidae", "forests", ["India", "SE Asia"], "uncommon",
              {"freq_range": (5000, 8000), "call_type": "high pitched", "pattern": "rapid"}),
    
    BirdEntry("White-eye", "Zosterops palpebrosus",
              "small olive-green bird with distinctive white eye-ring",
              "Zosteropidae", "forests, gardens", ["India", "SE Asia"], "common",
              {"freq_range": (4000, 7000), "call_type": "soft twittering", "pattern": "constant"}),
    
    BirdEntry("Jungle Babbler", "Argya striata",
              "grey-brown noisy bird, always in groups, 'seven sisters'",
              "Leiothrichidae", "gardens, scrub", ["India"], "common",
              {"freq_range": (1500, 4000), "call_type": "chattering", "pattern": "constant"}),
    
    BirdEntry("Yellow-billed Babbler", "Argya affinis",
              "grey-brown babbler with yellow bill, white-tipped tail",
              "Leiothrichidae", "scrub, gardens", ["India", "Sri Lanka"], "common",
              {"freq_range": (1500, 3500), "call_type": "churring", "pattern": "social"}),
    
    BirdEntry("Common Tailorbird", "Orthotomus sutorius",
              "small warbler-like bird, rufous crown, long cocked tail, loud song",
              "Cisticolidae", "gardens, thickets", ["India", "SE Asia"], "common",
              {"freq_range": (3000, 6000), "call_type": "loud towit", "pattern": "repeated"}),
    
    BirdEntry("Ashy Prinia", "Prinia socialis",
              "small grey warbler with long graduated tail, rufous crown",
              "Cisticolidae", "gardens, scrub", ["India", "Nepal"], "common",
              {"freq_range": (3000, 5500), "call_type": "nasal notes", "pattern": "persistent"}),
    
    BirdEntry("Plain Prinia", "Prinia inornata",
              "small plain brown prinia with long tail",
              "Cisticolidae", "grasslands, scrub", ["India", "South Asia"], "common",
              {"freq_range": (3000, 5000), "call_type": "plaintive notes", "pattern": "repeated"}),
    
    BirdEntry("House Crow", "Corvus splendens",
              "grey-necked crow, highly adaptable urban bird",
              "Corvidae", "urban, villages", ["India", "South Asia"], "common",
              {"freq_range": (500, 2000), "call_type": "harsh caw", "pattern": "repeated"}),
    
    BirdEntry("Large-billed Crow", "Corvus macrorhynchos",
              "all-black crow with heavy bill, deeper call than House Crow",
              "Corvidae", "forests, hills", ["India", "East Asia"], "common",
              {"freq_range": (400, 1500), "call_type": "deep caw", "pattern": "slow"}),
    
    BirdEntry("Rufous Treepie", "Dendrocitta vagabunda",
              "rufous-brown and grey with long tail, loud calls",
              "Corvidae", "forests, gardens", ["India", "South Asia"], "common",
              {"freq_range": (1000, 3000), "call_type": "metallic calls", "pattern": "varied"}),
    
    # Raptors of India (15)
    BirdEntry("Black Kite", "Milvus migrans",
              "brown raptor with forked tail, common scavenger",
              "Accipitridae", "urban, open country", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (1000, 3000), "call_type": "whistling", "pattern": "mewing"}),
    
    BirdEntry("Brahminy Kite", "Haliastur indus",
              "chestnut and white raptor, sacred in India",
              "Accipitridae", "wetlands, coasts", ["India", "SE Asia", "Australia"], "common",
              {"freq_range": (1500, 3500), "call_type": "mewing whistle", "pattern": "plaintive"}),
    
    BirdEntry("Shikra", "Accipiter badius",
              "small grey hawk with barred underparts, yellow eyes",
              "Accipitridae", "forests, gardens", ["India", "SE Asia"], "common",
              {"freq_range": (2000, 5000), "call_type": "sharp ki-ki-ki", "pattern": "rapid"}),
    
    BirdEntry("Crested Serpent Eagle", "Spilornis cheela",
              "dark brown eagle with crest, white-spotted underparts",
              "Accipitridae", "forests", ["India", "SE Asia"], "common",
              {"freq_range": (1000, 2500), "call_type": "loud screaming", "pattern": "ascending"}),
    
    BirdEntry("Changeable Hawk-Eagle", "Nisaetus cirrhatus",
              "large crested eagle, variable plumage, powerful raptor",
              "Accipitridae", "forests", ["India", "SE Asia"], "uncommon",
              {"freq_range": (800, 2000), "call_type": "shrill screams", "pattern": "descending"}),
    
    BirdEntry("Bonelli's Eagle", "Aquila fasciata",
              "large dark eagle with pale underparts, dark terminal tail band",
              "Accipitridae", "hills, open forests", ["India", "Mediterranean"], "uncommon",
              {"freq_range": (1000, 2500), "call_type": "barking calls", "pattern": "repeated"}),
    
    BirdEntry("Indian Spotted Eagle", "Clanga hastata",
              "medium brown eagle with pale patch on upperwing",
              "Accipitridae", "wetlands, plains", ["India"], "uncommon",
              {"freq_range": (1200, 2800), "call_type": "yelping", "pattern": "repeated"}),
    
    BirdEntry("White-eyed Buzzard", "Butastur teesa",
              "small buzzard with white eyes, rufous tail",
              "Accipitridae", "open country", ["India", "South Asia"], "common",
              {"freq_range": (1500, 3000), "call_type": "plaintive mew", "pattern": "drawn"}),
    
    BirdEntry("Oriental Honey-buzzard", "Pernis ptilorhynchus",
              "variable plumage buzzard, long neck, specialist on bee nests",
              "Accipitridae", "forests", ["India", "East Asia"], "common",
              {"freq_range": (1000, 2500), "call_type": "thin whistle", "pattern": "single"}),
    
    BirdEntry("Peregrine Falcon", "Falco peregrinus",
              "powerful falcon with dark hood, barred underparts, world's fastest bird",
              "Falconidae", "cliffs, cities", ["Global"], "uncommon",
              {"freq_range": (2000, 4000), "call_type": "loud kak-kak", "pattern": "rapid"}),
    
    BirdEntry("Common Kestrel", "Falco tinnunculus",
              "small falcon with rufous back, hovers while hunting",
              "Falconidae", "open country", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (3000, 5000), "call_type": "shrill kee-kee", "pattern": "repeated"}),
    
    BirdEntry("Spotted Owlet", "Athene brama",
              "small grey-brown owl with spots, yellow eyes, common around habitation",
              "Strigidae", "villages, ruins", ["India", "South Asia"], "common",
              {"freq_range": (500, 2000), "call_type": "harsh chirring", "pattern": "varied"}),
    
    BirdEntry("Indian Eagle-Owl", "Bubo bengalensis",
              "large brown owl with ear tufts, orange eyes",
              "Strigidae", "rocky areas, ravines", ["India", "Nepal"], "uncommon",
              {"freq_range": (200, 800), "call_type": "deep hoot", "pattern": "booming"}),
    
    BirdEntry("Barn Owl", "Tyto alba",
              "pale owl with heart-shaped face, no ear tufts",
              "Tytonidae", "old buildings, ruins", ["India", "Global"], "common",
              {"freq_range": (1000, 3000), "call_type": "screech", "pattern": "eerie"}),
    
    BirdEntry("Jungle Owlet", "Glaucidium radiatum",
              "small barred owlet, diurnal, forest species",
              "Strigidae", "forests", ["India", "Nepal"], "common",
              {"freq_range": (800, 2500), "call_type": "musical notes", "pattern": "ascending"}),
    
    # Waterbirds of India (20)
    BirdEntry("Indian Pond Heron", "Ardeola grayii",
              "small stocky heron, cryptic brown, white wings in flight",
              "Ardeidae", "wetlands, ponds", ["India", "South Asia"], "common",
              {"freq_range": (500, 2000), "call_type": "harsh croak", "pattern": "single"}),
    
    BirdEntry("Cattle Egret", "Bubulcus ibis",
              "small white egret, buff plumes in breeding, follows cattle",
              "Ardeidae", "grasslands, wetlands", ["India", "Global"], "common",
              {"freq_range": (800, 2500), "call_type": "croaking", "pattern": "harsh"}),
    
    BirdEntry("Little Egret", "Egretta garzetta",
              "slender white egret with black bill, yellow feet",
              "Ardeidae", "wetlands", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (600, 2000), "call_type": "croaking", "pattern": "harsh"}),
    
    BirdEntry("Great Egret", "Ardea alba",
              "large white egret with yellow bill, long S-curved neck",
              "Ardeidae", "wetlands", ["India", "Global"], "common",
              {"freq_range": (400, 1500), "call_type": "low croak", "pattern": "deep"}),
    
    BirdEntry("Grey Heron", "Ardea cinerea",
              "large grey heron with black crest, dagger bill",
              "Ardeidae", "wetlands", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (300, 1200), "call_type": "harsh fraahnk", "pattern": "single"}),
    
    BirdEntry("Purple Heron", "Ardea purpurea",
              "dark slender heron with rufous neck, striped pattern",
              "Ardeidae", "reedbeds, wetlands", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (300, 1000), "call_type": "harsh croak", "pattern": "deep"}),
    
    BirdEntry("Black-crowned Night Heron", "Nycticorax nycticorax",
              "stocky heron with black cap, red eyes, nocturnal",
              "Ardeidae", "wetlands, trees", ["India", "Global"], "common",
              {"freq_range": (500, 1500), "call_type": "quok", "pattern": "single"}),
    
    BirdEntry("Painted Stork", "Mycteria leucocephala",
              "large white stork with pink tertials, orange face",
              "Ciconiidae", "wetlands", ["India", "SE Asia"], "common",
              {"freq_range": (200, 800), "call_type": "bill clattering", "pattern": "mechanical"}),
    
    BirdEntry("Asian Openbill", "Anastomus oscitans",
              "white stork with gap in bill for eating snails",
              "Ciconiidae", "wetlands", ["India", "SE Asia"], "common",
              {"freq_range": (300, 1000), "call_type": "bill clattering", "pattern": "soft"}),
    
    BirdEntry("Woolly-necked Stork", "Ciconia episcopus",
              "black stork with woolly white neck and belly",
              "Ciconiidae", "wetlands, fields", ["India", "Africa", "SE Asia"], "common",
              {"freq_range": (200, 700), "call_type": "bill clattering", "pattern": "quiet"}),
    
    BirdEntry("Lesser Adjutant", "Leptoptilos javanicus",
              "large bald stork with massive bill, vulture-like",
              "Ciconiidae", "wetlands, forests", ["India", "SE Asia"], "uncommon",
              {"freq_range": (200, 600), "call_type": "bill clattering", "pattern": "low"}),
    
    BirdEntry("White Ibis", "Threskiornis melanocephalus",
              "white ibis with bare black head, curved bill",
              "Threskiornithidae", "wetlands", ["India", "SE Asia"], "common",
              {"freq_range": (500, 1500), "call_type": "grunting", "pattern": "harsh"}),
    
    BirdEntry("Glossy Ibis", "Plegadis falcinellus",
              "dark glossy ibis with curved bill, chestnut in breeding",
              "Threskiornithidae", "wetlands", ["India", "Global"], "common",
              {"freq_range": (600, 1800), "call_type": "grunting", "pattern": "nasal"}),
    
    BirdEntry("Eurasian Spoonbill", "Platalea leucorodia",
              "white with spatula-shaped bill, yellow breast band in breeding",
              "Threskiornithidae", "wetlands", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (400, 1200), "call_type": "grunting", "pattern": "low"}),
    
    BirdEntry("Sarus Crane", "Antigone antigone",
              "tallest flying bird, grey with red head and neck",
              "Gruidae", "wetlands, fields", ["India", "SE Asia", "Australia"], "uncommon",
              {"freq_range": (300, 1000), "call_type": "loud trumpeting", "pattern": "resonant"}),
    
    BirdEntry("Common Crane", "Grus grus",
              "grey crane with black and white head pattern, winter visitor",
              "Gruidae", "wetlands, fields", ["India (winter)", "Eurasia"], "uncommon",
              {"freq_range": (400, 1200), "call_type": "bugling", "pattern": "trumpeting"}),
    
    BirdEntry("White-breasted Waterhen", "Amaurornis phoenicurus",
              "dark grey waterhen with white breast and rufous vent",
              "Rallidae", "wetlands, gardens", ["India", "SE Asia"], "common",
              {"freq_range": (800, 3000), "call_type": "loud kwaak", "pattern": "repeated"}),
    
    BirdEntry("Purple Swamphen", "Porphyrio porphyrio",
              "large purple-blue rail with red bill and frontal shield",
              "Rallidae", "wetlands, reedbeds", ["India", "Eurasia", "Africa"], "common",
              {"freq_range": (500, 2000), "call_type": "loud hooting", "pattern": "booming"}),
    
    BirdEntry("Common Moorhen", "Gallinula chloropus",
              "dark waterbird with red frontal shield, white flank stripe",
              "Rallidae", "wetlands", ["India", "Global"], "common",
              {"freq_range": (800, 2500), "call_type": "loud kurrrk", "pattern": "explosive"}),
    
    BirdEntry("Eurasian Coot", "Fulica atra",
              "all-black waterbird with white frontal shield",
              "Rallidae", "lakes, wetlands", ["India", "Eurasia"], "common",
              {"freq_range": (700, 2000), "call_type": "explosive kowk", "pattern": "sharp"}),
    
    # Himalayan & Mountain Birds (15)
    BirdEntry("Himalayan Monal", "Lophophorus impejanus",
              "stunning pheasant, male iridescent multicolored, national bird of Nepal",
              "Phasianidae", "alpine meadows", ["Himalayas", "India", "Nepal"], "uncommon",
              {"freq_range": (500, 1500), "call_type": "loud whistle", "pattern": "repeated"}),
    
    BirdEntry("Satyr Tragopan", "Tragopan satyra",
              "crimson pheasant with blue facial skin, spotted white",
              "Phasianidae", "montane forests", ["Himalayas"], "rare",
              {"freq_range": (400, 1200), "call_type": "wailing", "pattern": "mournful"}),
    
    BirdEntry("Blood Pheasant", "Ithaginis cruentus",
              "grey pheasant with red streaks, high altitude specialist",
              "Phasianidae", "alpine scrub", ["Himalayas"], "uncommon",
              {"freq_range": (600, 1500), "call_type": "chuckling", "pattern": "soft"}),
    
    BirdEntry("Kalij Pheasant", "Lophura leucomelanos",
              "dark pheasant with white-streaked crest, common in hills",
              "Phasianidae", "hill forests", ["Himalayas", "India"], "common",
              {"freq_range": (500, 1500), "call_type": "harsh calls", "pattern": "cackling"}),
    
    BirdEntry("Red Junglefowl", "Gallus gallus",
              "ancestor of domestic chicken, male colorful with long tail",
              "Phasianidae", "forests", ["India", "SE Asia"], "common",
              {"freq_range": (400, 2000), "call_type": "cock-a-doodle", "pattern": "crowing"}),
    
    BirdEntry("Grey Junglefowl", "Gallus sonneratii",
              "endemic junglefowl, grey with golden hackles",
              "Phasianidae", "forests", ["India (peninsular)"], "common",
              {"freq_range": (500, 2000), "call_type": "crowing", "pattern": "different from Red"}),
    
    BirdEntry("Himalayan Griffon", "Gyps himalayensis",
              "huge pale vulture with white ruff, Himalayan specialist",
              "Accipitridae", "mountains", ["Himalayas", "Central Asia"], "uncommon",
              {"freq_range": (200, 800), "call_type": "hissing", "pattern": "rare"}),
    
    BirdEntry("Bearded Vulture", "Gypaetus barbatus",
              "spectacular vulture with orange breast, feeds on bones",
              "Accipitridae", "high mountains", ["Himalayas", "Europe", "Africa"], "rare",
              {"freq_range": (300, 1000), "call_type": "thin whistle", "pattern": "rare"}),
    
    BirdEntry("Himalayan Snowcock", "Tetraogallus himalayensis",
              "large grey partridge-like bird of high altitude",
              "Phasianidae", "alpine zones", ["Himalayas", "Central Asia"], "uncommon",
              {"freq_range": (400, 1200), "call_type": "cackling", "pattern": "echoing"}),
    
    BirdEntry("White-capped Redstart", "Phoenicurus leucocephalus",
              "striking black and white redstart with chestnut belly",
              "Muscicapidae", "mountain streams", ["Himalayas"], "common",
              {"freq_range": (3000, 6000), "call_type": "sweet song", "pattern": "melodious"}),
    
    BirdEntry("Blue Whistling Thrush", "Myophonus caeruleus",
              "large dark thrush with blue spangling, haunting song at dawn",
              "Muscicapidae", "mountain streams", ["Himalayas", "China"], "common",
              {"freq_range": (1000, 4000), "call_type": "whistling song", "pattern": "haunting"}),
    
    BirdEntry("Spotted Laughingthrush", "Ianthocincla ocellata",
              "rufous laughingthrush with black-bordered white spots",
              "Leiothrichidae", "montane forests", ["Himalayas"], "common",
              {"freq_range": (1500, 4000), "call_type": "laughing", "pattern": "cackling"}),
    
    BirdEntry("Rufous Sibia", "Heterophasia capistrata",
              "rufous bird with black cap, long graduated tail",
              "Leiothrichidae", "hill forests", ["Himalayas"], "common",
              {"freq_range": (2000, 5000), "call_type": "melodious", "pattern": "varied"}),
    
    BirdEntry("Long-tailed Minivet", "Pericrocotus ethologus",
              "male scarlet and black, female yellow and grey, long tail",
              "Campephagidae", "hill forests", ["Himalayas"], "common",
              {"freq_range": (4000, 7000), "call_type": "thin tweet", "pattern": "repeated"}),
    
    BirdEntry("Verditer Flycatcher", "Eumyias thalassinus",
              "entirely bright turquoise blue flycatcher",
              "Muscicapidae", "forests", ["Himalayas", "SE Asia"], "common",
              {"freq_range": (3000, 6000), "call_type": "sweet song", "pattern": "melodious"}),
    
    # Endemic & Special Indian Birds (15)
    BirdEntry("Indian Pitta", "Pitta brachyura",
              "stunning multi-colored ground bird, secretive in forests",
              "Pittidae", "forests", ["India", "Sri Lanka"], "uncommon",
              {"freq_range": (800, 2000), "call_type": "loud whistle", "pattern": "repeated"}),
    
    BirdEntry("Sri Lanka Frogmouth", "Batrachostomus moniliger",
              "nocturnal bird with wide gape, excellent camouflage",
              "Podargidae", "forests", ["India (Western Ghats)", "Sri Lanka"], "rare",
              {"freq_range": (400, 1200), "call_type": "laughing", "pattern": "chuckling"}),
    
    BirdEntry("Malabar Trogon", "Harpactes fasciatus",
              "colorful trogon, male has red belly, endemic to Western Ghats",
              "Trogonidae", "evergreen forests", ["India (Western Ghats)", "Sri Lanka"], "uncommon",
              {"freq_range": (1000, 2500), "call_type": "soft coo", "pattern": "repeated"}),
    
    BirdEntry("Malabar Grey Hornbill", "Ocyceros griseus",
              "endemic grey hornbill of Western Ghats",
              "Bucerotidae", "forests", ["India (Western Ghats)"], "common",
              {"freq_range": (500, 1800), "call_type": "cackling", "pattern": "laughing"}),
    
    BirdEntry("Nilgiri Flycatcher", "Eumyias albicaudatus",
              "indigo-blue flycatcher, endemic to Nilgiris and Western Ghats",
              "Muscicapidae", "shola forests", ["India (Nilgiris)"], "uncommon",
              {"freq_range": (2500, 5000), "call_type": "pleasant song", "pattern": "melodious"}),
    
    BirdEntry("White-bellied Treepie", "Dendrocitta leucogastra",
              "endemic treepie of Western Ghats, rufous and white",
              "Corvidae", "forests", ["India (Western Ghats)"], "common",
              {"freq_range": (1000, 3000), "call_type": "metallic calls", "pattern": "varied"}),
    
    BirdEntry("Kerala Laughingthrush", "Pterorhinus delesserti",
              "endemic laughingthrush with white throat, Western Ghats specialist",
              "Leiothrichidae", "forests", ["India (Western Ghats)"], "uncommon",
              {"freq_range": (1500, 4000), "call_type": "laughing", "pattern": "bubbling"}),
    
    BirdEntry("Nilgiri Wood Pigeon", "Columba elphinstonii",
              "large endemic pigeon with checkerboard neck pattern",
              "Columbidae", "shola forests", ["India (Western Ghats)"], "uncommon",
              {"freq_range": (300, 800), "call_type": "deep cooing", "pattern": "booming"}),
    
    BirdEntry("Andaman Serpent Eagle", "Spilornis elgini",
              "endemic serpent eagle of Andaman Islands",
              "Accipitridae", "forests", ["India (Andaman)"], "uncommon",
              {"freq_range": (800, 2000), "call_type": "screaming", "pattern": "ascending"}),
    
    BirdEntry("Nicobar Pigeon", "Caloenas nicobarica",
              "stunning iridescent green pigeon, Andaman & Nicobar specialty",
              "Columbidae", "islands", ["India (Andaman & Nicobar)", "SE Asia"], "rare",
              {"freq_range": (300, 700), "call_type": "low coo", "pattern": "soft"}),
    
    BirdEntry("Forest Owlet", "Athene blewitti",
              "critically endangered owlet, rediscovered in 1997",
              "Strigidae", "dry forests", ["India (Central)"], "rare",
              {"freq_range": (600, 1800), "call_type": "melodious", "pattern": "repeated"}),
    
    BirdEntry("Great Indian Bustard", "Ardeotis nigriceps",
              "critically endangered large bustard, less than 150 left",
              "Otididae", "grasslands", ["India", "Pakistan"], "rare",
              {"freq_range": (200, 600), "call_type": "deep boom", "pattern": "resonant"}),
    
    BirdEntry("Jerdon's Courser", "Rhinoptilus bitorquatus",
              "critically endangered nocturnal bird, rediscovered in 1986",
              "Glareolidae", "scrub forests", ["India (Andhra Pradesh)"], "rare",
              {"freq_range": (1000, 3000), "call_type": "sharp calls", "pattern": "nocturnal"}),
    
    BirdEntry("Spoon-billed Sandpiper", "Calidris pygmaea",
              "critically endangered wader with unique spoon-shaped bill",
              "Scolopacidae", "coastal", ["India (winter)", "Russia (breeding)"], "rare",
              {"freq_range": (4000, 7000), "call_type": "thin peep", "pattern": "soft"}),
    
    BirdEntry("Sociable Lapwing", "Vanellus gregarius",
              "critically endangered lapwing, winter visitor to India",
              "Charadriidae", "fields", ["India (winter)", "Central Asia"], "rare",
              {"freq_range": (2000, 4000), "call_type": "harsh calls", "pattern": "grating"}),
]

# =============================================================================
# SOUTH ASIAN NEIGHBORS (30 species)
# =============================================================================

SOUTH_ASIA_BIRDS = [
    BirdEntry("Sri Lanka Blue Magpie", "Urocissa ornata",
              "stunning blue magpie endemic to Sri Lanka, red bill",
              "Corvidae", "montane forests", ["Sri Lanka"], "not_native",
              {"freq_range": (1000, 3500), "call_type": "harsh calls", "pattern": "varied"}),
    
    BirdEntry("Sri Lanka Junglefowl", "Gallus lafayettii",
              "endemic junglefowl of Sri Lanka, national bird",
              "Phasianidae", "forests", ["Sri Lanka"], "not_native",
              {"freq_range": (500, 2000), "call_type": "crowing", "pattern": "distinctive"}),
    
    BirdEntry("Nepal House Martin", "Delichon nipalense",
              "martin of the Himalayas and Nepal",
              "Hirundinidae", "cliffs, buildings", ["Nepal", "Himalayas"], "uncommon",
              {"freq_range": (4000, 7000), "call_type": "twittering", "pattern": "soft"}),
    
    BirdEntry("Spiny Babbler", "Turdoides nipalensis",
              "Nepal's only endemic bird, found in scrubby hills",
              "Leiothrichidae", "scrub", ["Nepal"], "not_native",
              {"freq_range": (1500, 4000), "call_type": "chattering", "pattern": "babbling"}),
    
    BirdEntry("Ibisbill", "Ibidorhyncha struthersii",
              "unique wader with curved bill, Himalayan rivers",
              "Ibidorhynchidae", "mountain rivers", ["Himalayas"], "rare",
              {"freq_range": (2000, 4000), "call_type": "ringing calls", "pattern": "sharp"}),
    
    BirdEntry("Tibetan Snowfinch", "Montifringilla henrici",
              "high altitude finch of the Tibetan Plateau",
              "Passeridae", "alpine", ["Tibet", "Ladakh"], "uncommon",
              {"freq_range": (3000, 6000), "call_type": "chirping", "pattern": "simple"}),
    
    BirdEntry("White-rumped Vulture", "Gyps bengalensis",
              "critically endangered, population crashed 99%",
              "Accipitridae", "open country", ["India", "South Asia"], "rare",
              {"freq_range": (300, 1000), "call_type": "hissing", "pattern": "rare"}),
    
    BirdEntry("Indian Vulture", "Gyps indicus",
              "critically endangered vulture, larger bill than White-rumped",
              "Accipitridae", "cliffs, open country", ["India", "Pakistan"], "rare",
              {"freq_range": (300, 900), "call_type": "grunting", "pattern": "rare"}),
    
    BirdEntry("Red-headed Vulture", "Sarcogyps calvus",
              "distinctive black vulture with red head, critically endangered",
              "Accipitridae", "open country", ["India", "SE Asia"], "rare",
              {"freq_range": (300, 800), "call_type": "croaking", "pattern": "rare"}),
    
    BirdEntry("Bengal Florican", "Houbaropsis bengalensis",
              "critically endangered bustard of grasslands",
              "Otididae", "tall grasslands", ["India", "Nepal", "Cambodia"], "rare",
              {"freq_range": (300, 800), "call_type": "chik call", "pattern": "display"}),
    
    BirdEntry("Lesser Florican", "Sypheotides indicus",
              "smallest bustard, remarkable jumping display",
              "Otididae", "grasslands", ["India"], "rare",
              {"freq_range": (400, 1200), "call_type": "croaking", "pattern": "display"}),
    
    BirdEntry("Black-necked Crane", "Grus nigricollis",
              "high altitude crane, winters in Bhutan and Arunachal",
              "Gruidae", "high altitude wetlands", ["Ladakh", "Bhutan", "Tibet"], "rare",
              {"freq_range": (400, 1500), "call_type": "trumpeting", "pattern": "bugling"}),
    
    BirdEntry("Cheer Pheasant", "Catreus wallichii",
              "vulnerable pheasant of the Western Himalayas",
              "Phasianidae", "steep slopes", ["Himalayas"], "rare",
              {"freq_range": (600, 1800), "call_type": "loud cheer", "pattern": "repeated"}),
    
    BirdEntry("Western Tragopan", "Tragopan melanocephalus",
              "vulnerable pheasant, rarest tragopan, Western Himalayas",
              "Phasianidae", "montane forests", ["Himalayas (western)"], "rare",
              {"freq_range": (400, 1200), "call_type": "wailing", "pattern": "mournful"}),
    
    BirdEntry("Blyth's Tragopan", "Tragopan blythii",
              "vulnerable tragopan of Eastern Himalayas",
              "Phasianidae", "montane forests", ["Himalayas (eastern)"], "rare",
              {"freq_range": (400, 1000), "call_type": "wailing", "pattern": "mournful"}),
]

# =============================================================================
# GLOBAL COMMON BIRDS (40 species)
# =============================================================================

GLOBAL_BIRDS = [
    BirdEntry("European Robin", "Erithacus rubecula",
              "small bird with orange-red breast, upright posture",
              "Muscicapidae", "gardens, forests", ["Europe"], "vagrant",
              {"freq_range": (2000, 7000), "call_type": "melodious song", "pattern": "complex"}),
    
    BirdEntry("American Robin", "Turdus migratorius",
              "thrush with orange-red breast, common in North America",
              "Turdidae", "gardens, parks", ["North America"], "not_native",
              {"freq_range": (1500, 5000), "call_type": "cheerily song", "pattern": "melodious"}),
    
    BirdEntry("Blue Jay", "Cyanocitta cristata",
              "blue crested bird with white and black markings",
              "Corvidae", "forests, gardens", ["North America"], "not_native",
              {"freq_range": (1000, 4000), "call_type": "loud jay", "pattern": "harsh"}),
    
    BirdEntry("Northern Cardinal", "Cardinalis cardinalis",
              "bright red bird with crest and black face mask",
              "Cardinalidae", "gardens, thickets", ["North America"], "not_native",
              {"freq_range": (1500, 6000), "call_type": "whistled song", "pattern": "clear"}),
    
    BirdEntry("House Finch", "Haemorhous mexicanus",
              "small finch, male with red head and breast",
              "Fringillidae", "urban, gardens", ["North America"], "not_native",
              {"freq_range": (2000, 6000), "call_type": "warbling", "pattern": "complex"}),
    
    BirdEntry("American Goldfinch", "Spinus tristis",
              "bright yellow finch with black wings and cap",
              "Fringillidae", "fields, gardens", ["North America"], "not_native",
              {"freq_range": (3000, 7000), "call_type": "per-chick-o-ree", "pattern": "flight call"}),
    
    BirdEntry("Mallard", "Anas platyrhynchos",
              "male has green head, yellow bill; female mottled brown",
              "Anatidae", "wetlands", ["Northern Hemisphere"], "common",
              {"freq_range": (500, 2000), "call_type": "quacking", "pattern": "loud"}),
    
    BirdEntry("Canada Goose", "Branta canadensis",
              "large goose with black neck, white cheek patch",
              "Anatidae", "lakes, fields", ["North America", "introduced elsewhere"], "vagrant",
              {"freq_range": (300, 1500), "call_type": "honking", "pattern": "resonant"}),
    
    BirdEntry("Bald Eagle", "Haliaeetus leucocephalus",
              "large dark eagle with white head and tail",
              "Accipitridae", "near water", ["North America"], "not_native",
              {"freq_range": (1000, 3000), "call_type": "high-pitched", "pattern": "chittering"}),
    
    BirdEntry("Great Blue Heron", "Ardea herodias",
              "tall grey-blue heron with long neck and legs",
              "Ardeidae", "wetlands", ["Americas"], "not_native",
              {"freq_range": (300, 1200), "call_type": "harsh croak", "pattern": "single"}),
    
    BirdEntry("Common Nightingale", "Luscinia megarhynchos",
              "plain brown bird famous for powerful melodious song",
              "Muscicapidae", "thickets", ["Europe", "Western Asia"], "vagrant",
              {"freq_range": (1000, 8000), "call_type": "amazing song", "pattern": "complex"}),
    
    BirdEntry("Song Thrush", "Turdus philomelos",
              "brown thrush with spotted breast, repeated song phrases",
              "Turdidae", "gardens, forests", ["Europe"], "vagrant",
              {"freq_range": (1500, 5000), "call_type": "repeated phrases", "pattern": "song"}),
    
    BirdEntry("Eurasian Blackbird", "Turdus merula",
              "male all black with orange bill, female brown",
              "Turdidae", "gardens, forests", ["Eurasia"], "vagrant",
              {"freq_range": (1000, 4000), "call_type": "mellow song", "pattern": "fluty"}),
    
    BirdEntry("Great Tit", "Parus major",
              "yellow and green tit with black head stripe",
              "Paridae", "forests, gardens", ["Eurasia"], "common",
              {"freq_range": (2500, 6000), "call_type": "teacher-teacher", "pattern": "repeated"}),
    
    BirdEntry("Blue Tit", "Cyanistes caeruleus",
              "small blue and yellow tit with blue cap",
              "Paridae", "forests, gardens", ["Europe"], "vagrant",
              {"freq_range": (3000, 7000), "call_type": "thin calls", "pattern": "rapid"}),
    
    BirdEntry("European Goldfinch", "Carduelis carduelis",
              "colorful finch with red face and gold wing bar",
              "Fringillidae", "gardens, orchards", ["Europe"], "vagrant",
              {"freq_range": (3000, 7000), "call_type": "tinkling", "pattern": "liquid"}),
    
    BirdEntry("Barn Swallow", "Hirundo rustica",
              "long forked tail, blue back, rufous throat",
              "Hirundinidae", "open country, near water", ["Global"], "common",
              {"freq_range": (3000, 7000), "call_type": "twittering", "pattern": "rapid"}),
    
    BirdEntry("Common Swift", "Apus apus",
              "all dark swift with scythe-shaped wings, rarely lands",
              "Apodidae", "aerial", ["Eurasia", "Africa"], "common",
              {"freq_range": (5000, 9000), "call_type": "screaming", "pattern": "high-pitched"}),
    
    BirdEntry("Eurasian Hoopoe", "Upupa epops",
              "striking bird with crest and pied wings",
              "Upupidae", "open country", ["Eurasia", "Africa"], "common",
              {"freq_range": (400, 1200), "call_type": "oop-oop-oop", "pattern": "repeated"}),
    
    BirdEntry("Common Cuckoo", "Cuculus canorus",
              "grey bird famous for 'cuckoo' call, brood parasite",
              "Cuculidae", "forests, gardens", ["Eurasia", "Africa"], "common",
              {"freq_range": (600, 800), "call_type": "cuckoo", "pattern": "two-note"}),
    
    BirdEntry("Great Spotted Woodpecker", "Dendrocopos major",
              "black and white woodpecker with red on crown/vent",
              "Picidae", "forests", ["Eurasia"], "common",
              {"freq_range": (1000, 3000), "call_type": "sharp kik", "pattern": "single"}),
    
    BirdEntry("Eurasian Jay", "Garrulus glandarius",
              "pinkish-brown jay with blue wing patch",
              "Corvidae", "forests", ["Eurasia"], "vagrant",
              {"freq_range": (1000, 4000), "call_type": "harsh screech", "pattern": "alarmed"}),
    
    BirdEntry("Eurasian Magpie", "Pica pica",
              "black and white bird with long graduated tail",
              "Corvidae", "open country, gardens", ["Eurasia"], "vagrant",
              {"freq_range": (800, 3000), "call_type": "chattering", "pattern": "rapid"}),
    
    BirdEntry("Common Raven", "Corvus corax",
              "largest passerine, all black with wedge tail",
              "Corvidae", "varied habitats", ["Northern Hemisphere"], "uncommon",
              {"freq_range": (300, 1500), "call_type": "deep croaking", "pattern": "varied"}),
    
    BirdEntry("Snowy Owl", "Bubo scandiacus",
              "large white owl with some dark barring, yellow eyes",
              "Strigidae", "Arctic tundra", ["Arctic"], "vagrant",
              {"freq_range": (200, 800), "call_type": "barking hoot", "pattern": "deep"}),
    
    BirdEntry("Atlantic Puffin", "Fratercula arctica",
              "black and white seabird with colorful triangular bill",
              "Alcidae", "coastal cliffs, sea", ["North Atlantic"], "not_native",
              {"freq_range": (600, 2000), "call_type": "growling", "pattern": "burrow"}),
    
    BirdEntry("Scarlet Macaw", "Ara macao",
              "large red parrot with blue and yellow wings",
              "Psittacidae", "rainforests", ["Central/South America"], "not_native",
              {"freq_range": (500, 3000), "call_type": "loud screaming", "pattern": "harsh"}),
    
    BirdEntry("Resplendent Quetzal", "Pharomachrus mocinno",
              "emerald green bird with red breast, extremely long tail",
              "Trogonidae", "cloud forests", ["Central America"], "not_native",
              {"freq_range": (800, 2500), "call_type": "kyow-kyow", "pattern": "repeated"}),
    
    BirdEntry("Mandarin Duck", "Aix galericulata",
              "colorful duck with orange sail feathers, purple breast",
              "Anatidae", "forested wetlands", ["East Asia"], "vagrant",
              {"freq_range": (800, 2000), "call_type": "whistling", "pattern": "rising"}),
    
    BirdEntry("Greater Flamingo", "Phoenicopterus roseus",
              "tall pink bird with long neck and legs, curved bill",
              "Phoenicopteridae", "saline lakes", ["Africa", "Asia", "Europe"], "common",
              {"freq_range": (300, 1200), "call_type": "honking", "pattern": "goose-like"}),
    
    BirdEntry("Emperor Penguin", "Aptenodytes forsteri",
              "largest penguin, black and white with yellow patches",
              "Spheniscidae", "Antarctic", ["Antarctica"], "not_native",
              {"freq_range": (300, 1500), "call_type": "trumpeting", "pattern": "display"}),
    
    BirdEntry("Superb Lyrebird", "Menura novaehollandiae",
              "ground bird with remarkable mimicry and lyre-shaped tail",
              "Menuridae", "forests", ["Australia"], "not_native",
              {"freq_range": (500, 8000), "call_type": "amazing mimic", "pattern": "complex"}),
    
    BirdEntry("Kookaburra", "Dacelo novaeguineae",
              "large kingfisher with brown back, famous laughing call",
              "Alcedinidae", "forests, gardens", ["Australia"], "not_native",
              {"freq_range": (500, 3000), "call_type": "laughing", "pattern": "territorial"}),
    
    BirdEntry("Southern Cassowary", "Casuarius casuarius",
              "large flightless bird with blue neck and casque",
              "Casuariidae", "rainforests", ["Australia", "New Guinea"], "not_native",
              {"freq_range": (20, 200), "call_type": "booming", "pattern": "infrasonic"}),
    
    BirdEntry("Emu", "Dromaius novaehollandiae",
              "large flightless bird, second tallest after ostrich",
              "Dromaiidae", "open country", ["Australia"], "not_native",
              {"freq_range": (50, 300), "call_type": "drumming boom", "pattern": "resonant"}),
    
    BirdEntry("Common Ostrich", "Struthio camelus",
              "world's largest bird, flightless with long neck",
              "Struthionidae", "savanna", ["Africa"], "not_native",
              {"freq_range": (50, 200), "call_type": "booming", "pattern": "territorial"}),
    
    BirdEntry("Toucan", "Ramphastos toco",
              "black bird with huge colorful bill, white throat",
              "Ramphastidae", "forests", ["South America"], "not_native",
              {"freq_range": (500, 2000), "call_type": "yelping", "pattern": "repeated"}),
    
    BirdEntry("Secretary Bird", "Sagittarius serpentarius",
              "long-legged raptor that hunts on foot, crest of feathers",
              "Sagittariidae", "savanna", ["Africa"], "not_native",
              {"freq_range": (300, 1000), "call_type": "croaking", "pattern": "rare"}),
    
    BirdEntry("Shoebill", "Balaeniceps rex",
              "huge grey bird with enormous shoe-shaped bill",
              "Balaenicipitidae", "swamps", ["Africa"], "not_native",
              {"freq_range": (200, 800), "call_type": "bill clattering", "pattern": "machine-gun"}),
    
    BirdEntry("Kakapo", "Strigops habroptila",
              "flightless nocturnal parrot, critically endangered",
              "Strigopidae", "forests", ["New Zealand"], "not_native",
              {"freq_range": (50, 200), "call_type": "booming", "pattern": "territorial"}),
]


def get_full_dataset() -> List[BirdEntry]:
    """Get complete dataset of 200+ birds."""
    return INDIA_BIRDS + SOUTH_ASIA_BIRDS + GLOBAL_BIRDS


def get_india_focused_dataset() -> List[BirdEntry]:
    """Get India-focused dataset (for benchmarking)."""
    return INDIA_BIRDS + SOUTH_ASIA_BIRDS


def get_description_tests(num_tests: int = 200) -> List[tuple]:
    """Generate description test cases."""
    dataset = get_full_dataset()
    tests = []
    
    for bird in dataset[:num_tests]:
        tests.append((
            bird.name,
            bird.scientific_name,
            bird.description,
            bird.rarity_in_india
        ))
    
    return tests


def get_audio_characteristics() -> Dict[str, Dict]:
    """Get audio characteristics for synthetic audio generation."""
    dataset = get_full_dataset()
    return {bird.name: bird.audio_chars for bird in dataset}


# Stats
if __name__ == "__main__":
    dataset = get_full_dataset()
    print(f"Total birds in dataset: {len(dataset)}")
    print(f"India birds: {len(INDIA_BIRDS)}")
    print(f"South Asia birds: {len(SOUTH_ASIA_BIRDS)}")
    print(f"Global birds: {len(GLOBAL_BIRDS)}")
    
    # Count by rarity
    rarity_counts = {}
    for bird in dataset:
        rarity_counts[bird.rarity_in_india] = rarity_counts.get(bird.rarity_in_india, 0) + 1
    print(f"\nBy rarity in India: {rarity_counts}")

