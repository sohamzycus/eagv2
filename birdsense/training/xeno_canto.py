"""
Xeno-Canto Dataset Downloader for BirdSense.

Downloads bird audio recordings from Xeno-Canto API
with focus on Indian bird species.

API Documentation: https://xeno-canto.org/explore/api
"""

import asyncio
import httpx
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging
from rich.progress import Progress, TaskID
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class XenoCantoRecording:
    """Single recording from Xeno-Canto."""
    id: str
    species: str
    scientific_name: str
    common_name: str
    country: str
    location: str
    latitude: Optional[float]
    longitude: Optional[float]
    quality: str  # A, B, C, D, E
    length: str
    file_url: str
    license: str
    recordist: str
    
    @classmethod
    def from_api(cls, data: dict) -> "XenoCantoRecording":
        return cls(
            id=data.get("id", ""),
            species=data.get("sp", ""),
            scientific_name=data.get("gen", "") + " " + data.get("sp", ""),
            common_name=data.get("en", ""),
            country=data.get("cnt", ""),
            location=data.get("loc", ""),
            latitude=float(data["lat"]) if data.get("lat") else None,
            longitude=float(data["lng"]) if data.get("lng") else None,
            quality=data.get("q", "E"),
            length=data.get("length", ""),
            file_url=data.get("file", ""),
            license=data.get("lic", ""),
            recordist=data.get("rec", "")
        )


@dataclass
class DownloadConfig:
    """Configuration for Xeno-Canto download."""
    output_dir: str = "data/xeno-canto"
    country: str = "India"
    quality_filter: List[str] = field(default_factory=lambda: ["A", "B"])
    min_recordings_per_species: int = 50
    max_recordings_per_species: int = 500
    concurrent_downloads: int = 5
    retry_attempts: int = 3
    timeout: int = 60


class XenoCantoDownloader:
    """
    Download bird recordings from Xeno-Canto.
    
    Focuses on Indian bird species for CSCR initiative.
    """
    
    API_BASE = "https://xeno-canto.org/api/2/recordings"
    
    def __init__(self, config: Optional[DownloadConfig] = None):
        self.config = config or DownloadConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata storage
        self.metadata_file = self.output_dir / "metadata.json"
        self.metadata: Dict[str, List[dict]] = {}
        
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                self.metadata = json.load(f)
    
    async def search_species(
        self,
        query: str,
        country: Optional[str] = None,
        quality: Optional[List[str]] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search Xeno-Canto for recordings.
        
        Args:
            query: Species name or search query
            country: Country filter
            quality: Quality filter (A, B, C, D, E)
            page: Page number
            
        Returns:
            API response with recordings
        """
        params = {
            "query": query
        }
        
        if country:
            params["query"] += f" cnt:{country}"
        
        if quality:
            quality_str = " ".join([f"q:{q}" for q in quality])
            params["query"] += f" {quality_str}"
        
        params["page"] = page
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.get(self.API_BASE, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_all_recordings(
        self,
        species_name: str,
        max_recordings: Optional[int] = None
    ) -> List[XenoCantoRecording]:
        """
        Get all recordings for a species.
        
        Args:
            species_name: Scientific or common name
            max_recordings: Maximum number to retrieve
            
        Returns:
            List of recording objects
        """
        max_recordings = max_recordings or self.config.max_recordings_per_species
        recordings = []
        page = 1
        
        while len(recordings) < max_recordings:
            try:
                result = await self.search_species(
                    query=species_name,
                    country=self.config.country,
                    quality=self.config.quality_filter,
                    page=page
                )
                
                if not result.get("recordings"):
                    break
                
                for rec_data in result["recordings"]:
                    rec = XenoCantoRecording.from_api(rec_data)
                    recordings.append(rec)
                    
                    if len(recordings) >= max_recordings:
                        break
                
                # Check if more pages
                num_pages = int(result.get("numPages", 1))
                if page >= num_pages:
                    break
                    
                page += 1
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching {species_name} page {page}: {e}")
                break
        
        return recordings
    
    async def download_recording(
        self,
        recording: XenoCantoRecording,
        species_dir: Path
    ) -> Optional[Path]:
        """
        Download a single recording.
        
        Args:
            recording: Recording to download
            species_dir: Directory to save to
            
        Returns:
            Path to downloaded file or None
        """
        if not recording.file_url:
            return None
        
        # Sanitize filename
        filename = f"{recording.id}.mp3"
        filepath = species_dir / filename
        
        if filepath.exists():
            return filepath
        
        for attempt in range(self.config.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout, follow_redirects=True) as client:
                    response = await client.get(recording.file_url)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    return filepath
                    
            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to download {recording.id}: {e}")
                    return None
        
        return None
    
    async def download_species(
        self,
        species_name: str,
        scientific_name: str,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> Dict[str, Any]:
        """
        Download all recordings for a species.
        
        Args:
            species_name: Common name
            scientific_name: Scientific name
            progress: Rich progress bar
            task_id: Task ID for progress
            
        Returns:
            Download statistics
        """
        # Create species directory
        safe_name = scientific_name.replace(" ", "_").lower()
        species_dir = self.output_dir / safe_name
        species_dir.mkdir(exist_ok=True)
        
        # Get recordings
        recordings = await self.get_all_recordings(scientific_name)
        
        if len(recordings) < self.config.min_recordings_per_species:
            logger.warning(
                f"{species_name}: Only {len(recordings)} recordings "
                f"(min: {self.config.min_recordings_per_species})"
            )
        
        # Download concurrently
        downloaded = 0
        failed = 0
        
        semaphore = asyncio.Semaphore(self.config.concurrent_downloads)
        
        async def download_with_semaphore(rec):
            async with semaphore:
                return await self.download_recording(rec, species_dir)
        
        tasks = [download_with_semaphore(rec) for rec in recordings]
        
        for i, result in enumerate(asyncio.as_completed(tasks)):
            path = await result
            if path:
                downloaded += 1
            else:
                failed += 1
            
            if progress and task_id:
                progress.update(task_id, advance=1)
        
        # Save metadata
        self.metadata[scientific_name] = [
            {
                "id": rec.id,
                "common_name": rec.common_name,
                "quality": rec.quality,
                "location": rec.location,
                "latitude": rec.latitude,
                "longitude": rec.longitude,
                "recordist": rec.recordist
            }
            for rec in recordings
        ]
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        return {
            "species": species_name,
            "scientific_name": scientific_name,
            "total": len(recordings),
            "downloaded": downloaded,
            "failed": failed
        }
    
    async def download_dataset(
        self,
        species_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Download entire dataset for multiple species.
        
        Args:
            species_list: List of {"common_name": ..., "scientific_name": ...}
            
        Returns:
            Download summary
        """
        console.print(f"\n[bold green]Downloading {len(species_list)} species from Xeno-Canto[/bold green]\n")
        
        results = []
        
        with Progress() as progress:
            overall = progress.add_task("[cyan]Overall Progress", total=len(species_list))
            
            for species in species_list:
                species_task = progress.add_task(
                    f"[yellow]{species['common_name']}", 
                    total=self.config.max_recordings_per_species
                )
                
                result = await self.download_species(
                    species['common_name'],
                    species['scientific_name'],
                    progress,
                    species_task
                )
                
                results.append(result)
                progress.update(overall, advance=1)
                
                # Remove completed species task
                progress.remove_task(species_task)
        
        # Summary
        total_downloaded = sum(r['downloaded'] for r in results)
        total_failed = sum(r['failed'] for r in results)
        
        console.print(f"\n[bold green]Download Complete![/bold green]")
        console.print(f"  Species: {len(species_list)}")
        console.print(f"  Downloaded: {total_downloaded}")
        console.print(f"  Failed: {total_failed}")
        console.print(f"  Location: {self.output_dir}")
        
        return {
            "species_count": len(species_list),
            "total_downloaded": total_downloaded,
            "total_failed": total_failed,
            "results": results
        }


# India bird species list for training
INDIA_BIRD_SPECIES = [
    {"common_name": "Indian Cuckoo", "scientific_name": "Cuculus micropterus"},
    {"common_name": "Asian Koel", "scientific_name": "Eudynamys scolopaceus"},
    {"common_name": "Greater Coucal", "scientific_name": "Centropus sinensis"},
    {"common_name": "Oriental Magpie-Robin", "scientific_name": "Copsychus saularis"},
    {"common_name": "Indian Robin", "scientific_name": "Saxicoloides fulicatus"},
    {"common_name": "Common Kingfisher", "scientific_name": "Alcedo atthis"},
    {"common_name": "White-throated Kingfisher", "scientific_name": "Halcyon smyrnensis"},
    {"common_name": "Pied Kingfisher", "scientific_name": "Ceryle rudis"},
    {"common_name": "Indian Peafowl", "scientific_name": "Pavo cristatus"},
    {"common_name": "Red Junglefowl", "scientific_name": "Gallus gallus"},
    {"common_name": "Grey Junglefowl", "scientific_name": "Gallus sonneratii"},
    {"common_name": "House Sparrow", "scientific_name": "Passer domesticus"},
    {"common_name": "Common Myna", "scientific_name": "Acridotheres tristis"},
    {"common_name": "Jungle Myna", "scientific_name": "Acridotheres fuscus"},
    {"common_name": "Coppersmith Barbet", "scientific_name": "Psilopogon haemacephalus"},
    {"common_name": "Brown-headed Barbet", "scientific_name": "Psilopogon zeylanicus"},
    {"common_name": "White-cheeked Barbet", "scientific_name": "Psilopogon viridis"},
    {"common_name": "Rose-ringed Parakeet", "scientific_name": "Psittacula krameri"},
    {"common_name": "Plum-headed Parakeet", "scientific_name": "Psittacula cyanocephala"},
    {"common_name": "Alexandrine Parakeet", "scientific_name": "Psittacula eupatria"},
    {"common_name": "Spotted Dove", "scientific_name": "Streptopelia chinensis"},
    {"common_name": "Eurasian Collared Dove", "scientific_name": "Streptopelia decaocto"},
    {"common_name": "Laughing Dove", "scientific_name": "Spilopelia senegalensis"},
    {"common_name": "Red-vented Bulbul", "scientific_name": "Pycnonotus cafer"},
    {"common_name": "Red-whiskered Bulbul", "scientific_name": "Pycnonotus jocosus"},
    {"common_name": "White-browed Bulbul", "scientific_name": "Pycnonotus luteolus"},
    {"common_name": "Purple Sunbird", "scientific_name": "Cinnyris asiaticus"},
    {"common_name": "Purple-rumped Sunbird", "scientific_name": "Leptocoma zeylonica"},
    {"common_name": "Common Tailorbird", "scientific_name": "Orthotomus sutorius"},
    {"common_name": "Spotted Owlet", "scientific_name": "Athene brama"},
    {"common_name": "Barn Owl", "scientific_name": "Tyto alba"},
    {"common_name": "Indian Scops Owl", "scientific_name": "Otus bakkamoena"},
    {"common_name": "House Crow", "scientific_name": "Corvus splendens"},
    {"common_name": "Large-billed Crow", "scientific_name": "Corvus macrorhynchos"},
    {"common_name": "Black Drongo", "scientific_name": "Dicrurus macrocercus"},
    {"common_name": "Ashy Drongo", "scientific_name": "Dicrurus leucophaeus"},
    {"common_name": "Indian Golden Oriole", "scientific_name": "Oriolus kundoo"},
    {"common_name": "Black-hooded Oriole", "scientific_name": "Oriolus xanthornus"},
    {"common_name": "Common Hoopoe", "scientific_name": "Upupa epops"},
    {"common_name": "Green Bee-eater", "scientific_name": "Merops orientalis"},
    {"common_name": "Blue-tailed Bee-eater", "scientific_name": "Merops philippinus"},
    {"common_name": "Indian Roller", "scientific_name": "Coracias benghalensis"},
    {"common_name": "Indian Grey Hornbill", "scientific_name": "Ocyceros birostris"},
    {"common_name": "Malabar Grey Hornbill", "scientific_name": "Ocyceros griseus"},
    {"common_name": "Asian Paradise Flycatcher", "scientific_name": "Terpsiphone paradisi"},
    {"common_name": "White-browed Fantail", "scientific_name": "Rhipidura aureola"},
    {"common_name": "Indian Pitta", "scientific_name": "Pitta brachyura"},
    {"common_name": "Common Iora", "scientific_name": "Aegithina tiphia"},
    {"common_name": "Black-headed Cuckooshrike", "scientific_name": "Lalage melanoptera"},
    {"common_name": "Small Minivet", "scientific_name": "Pericrocotus cinnamomeus"},
    {"common_name": "Scarlet Minivet", "scientific_name": "Pericrocotus speciosus"},
    {"common_name": "Ashy Woodswallow", "scientific_name": "Artamus fuscus"},
    {"common_name": "Bay-backed Shrike", "scientific_name": "Lanius vittatus"},
    {"common_name": "Long-tailed Shrike", "scientific_name": "Lanius schach"},
    {"common_name": "Brown Shrike", "scientific_name": "Lanius cristatus"},
    {"common_name": "Jungle Babbler", "scientific_name": "Argya striata"},
    {"common_name": "Yellow-billed Babbler", "scientific_name": "Argya affinis"},
    {"common_name": "Common Babbler", "scientific_name": "Argya caudata"},
    {"common_name": "Rufous Treepie", "scientific_name": "Dendrocitta vagabunda"},
    {"common_name": "Greater Racket-tailed Drongo", "scientific_name": "Dicrurus paradiseus"},
    {"common_name": "White-bellied Drongo", "scientific_name": "Dicrurus caerulescens"},
    {"common_name": "Indian Nuthatch", "scientific_name": "Sitta castanea"},
    {"common_name": "Velvet-fronted Nuthatch", "scientific_name": "Sitta frontalis"},
    {"common_name": "Great Tit", "scientific_name": "Parus major"},
    {"common_name": "Indian Pond Heron", "scientific_name": "Ardeola grayii"},
    {"common_name": "Cattle Egret", "scientific_name": "Bubulcus ibis"},
    {"common_name": "Little Egret", "scientific_name": "Egretta garzetta"},
    {"common_name": "Great Egret", "scientific_name": "Ardea alba"},
    {"common_name": "Grey Heron", "scientific_name": "Ardea cinerea"},
    {"common_name": "Purple Heron", "scientific_name": "Ardea purpurea"},
    {"common_name": "Black-crowned Night Heron", "scientific_name": "Nycticorax nycticorax"},
    {"common_name": "Indian Cormorant", "scientific_name": "Phalacrocorax fuscicollis"},
    {"common_name": "Little Cormorant", "scientific_name": "Microcarbo niger"},
    {"common_name": "Oriental Darter", "scientific_name": "Anhinga melanogaster"},
    {"common_name": "White-breasted Waterhen", "scientific_name": "Amaurornis phoenicurus"},
    {"common_name": "Purple Swamphen", "scientific_name": "Porphyrio porphyrio"},
    {"common_name": "Common Moorhen", "scientific_name": "Gallinula chloropus"},
    {"common_name": "Eurasian Coot", "scientific_name": "Fulica atra"},
    {"common_name": "Red-wattled Lapwing", "scientific_name": "Vanellus indicus"},
    {"common_name": "Yellow-wattled Lapwing", "scientific_name": "Vanellus malabaricus"},
    {"common_name": "River Tern", "scientific_name": "Sterna aurantia"},
    {"common_name": "Black Kite", "scientific_name": "Milvus migrans"},
    {"common_name": "Brahminy Kite", "scientific_name": "Haliastur indus"},
    {"common_name": "Shikra", "scientific_name": "Accipiter badius"},
    {"common_name": "Black-shouldered Kite", "scientific_name": "Elanus caeruleus"},
    {"common_name": "Oriental Honey Buzzard", "scientific_name": "Pernis ptilorhynchus"},
    {"common_name": "Crested Serpent Eagle", "scientific_name": "Spilornis cheela"},
    {"common_name": "Changeable Hawk-Eagle", "scientific_name": "Nisaetus cirrhatus"},
    {"common_name": "Indian Vulture", "scientific_name": "Gyps indicus"},
    {"common_name": "White-rumped Vulture", "scientific_name": "Gyps bengalensis"},
    {"common_name": "Lesser Whistling Duck", "scientific_name": "Dendrocygna javanica"},
    {"common_name": "Spot-billed Duck", "scientific_name": "Anas poecilorhyncha"},
    {"common_name": "Indian Spot-billed Duck", "scientific_name": "Anas poecilorhyncha"},
    {"common_name": "Cotton Pygmy Goose", "scientific_name": "Nettapus coromandelianus"},
    {"common_name": "Comb Duck", "scientific_name": "Sarkidiornis melanotos"},
    {"common_name": "Northern Shoveler", "scientific_name": "Spatula clypeata"},
    {"common_name": "Eurasian Teal", "scientific_name": "Anas crecca"},
    {"common_name": "Common Pochard", "scientific_name": "Aythya ferina"},
    {"common_name": "Painted Stork", "scientific_name": "Mycteria leucocephala"},
    {"common_name": "Asian Openbill", "scientific_name": "Anastomus oscitans"},
    {"common_name": "Black-necked Stork", "scientific_name": "Ephippiorhynchus asiaticus"},
    {"common_name": "Woolly-necked Stork", "scientific_name": "Ciconia episcopus"},
    {"common_name": "White-throated Needletail", "scientific_name": "Hirundapus caudacutus"},
    {"common_name": "Asian Palm Swift", "scientific_name": "Cypsiurus balasiensis"},
    {"common_name": "House Swift", "scientific_name": "Apus nipalensis"},
    {"common_name": "Crested Treeswift", "scientific_name": "Hemiprocne coronata"},
    {"common_name": "Greater Flamingo", "scientific_name": "Phoenicopterus roseus"},
    {"common_name": "Sarus Crane", "scientific_name": "Antigone antigone"},
    {"common_name": "Common Crane", "scientific_name": "Grus grus"},
    {"common_name": "Demoiselle Crane", "scientific_name": "Grus virgo"},
    {"common_name": "Great Indian Bustard", "scientific_name": "Ardeotis nigriceps"},
    {"common_name": "Indian Bustard", "scientific_name": "Ardeotis nigriceps"},
    {"common_name": "Bengal Florican", "scientific_name": "Houbaropsis bengalensis"},
    {"common_name": "Lesser Florican", "scientific_name": "Sypheotides indicus"},
    # Add more as needed...
]


async def download_india_birds(
    output_dir: str = "data/xeno-canto",
    max_species: Optional[int] = None
):
    """
    Download bird recordings for India species.
    
    Args:
        output_dir: Output directory
        max_species: Limit number of species (for testing)
    """
    config = DownloadConfig(output_dir=output_dir)
    downloader = XenoCantoDownloader(config)
    
    species_list = INDIA_BIRD_SPECIES[:max_species] if max_species else INDIA_BIRD_SPECIES
    
    result = await downloader.download_dataset(species_list)
    return result


if __name__ == "__main__":
    import sys
    
    max_species = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(download_india_birds(max_species=max_species))

