"""
Bird Reasoning Engine for BirdSense.

Uses LLM to enhance bird species identification through:
- Multi-evidence reasoning (audio, visual, description)
- Habitat and range validation
- Confidence calibration
- Natural language explanation generation
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import json

try:
    from .ollama_client import OllamaClient, OllamaConfig, SyncOllamaClient
    from ..data.species_db import IndiaSpeciesDatabase, SpeciesInfo
except ImportError:
    from llm.ollama_client import OllamaClient, OllamaConfig, SyncOllamaClient
    from data.species_db import IndiaSpeciesDatabase, SpeciesInfo


@dataclass
class ReasoningContext:
    """Context for species reasoning."""
    # Audio analysis results
    audio_predictions: List[Tuple[int, float]] = None  # [(species_id, confidence), ...]
    audio_quality: str = "unknown"
    
    # Location context
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    
    # Temporal context
    month: Optional[int] = None
    time_of_day: Optional[str] = None  # morning, afternoon, evening, night
    
    # Habitat context
    habitat: Optional[str] = None
    elevation: Optional[int] = None
    
    # User description (if any)
    user_description: Optional[str] = None


@dataclass
class ReasoningResult:
    """Result of species reasoning."""
    species_id: int
    species_name: str
    confidence: float
    reasoning: str
    alternative_species: List[Tuple[str, float]]
    novelty_flag: bool
    novelty_explanation: Optional[str]


SYSTEM_PROMPT = """You are an expert ornithologist specializing in Indian birds. Your role is to:
1. Analyze bird identification evidence from audio, visual, and contextual clues
2. Consider habitat, range, season, and time of day to validate identifications
3. Flag unusual or out-of-range sightings that could be scientifically significant
4. Provide clear, educational explanations

When analyzing bird identifications:
- Consider the probability of the species being present at the given location and time
- Note if the species is commonly confused with similar species
- Be aware of seasonal migration patterns
- Flag any sightings that would be unusual or noteworthy

Respond in a structured format with your reasoning and final assessment."""


class BirdReasoningEngine:
    """
    LLM-powered reasoning engine for bird identification.
    
    Combines audio classifier predictions with contextual information
    to produce calibrated, explainable species identifications.
    """
    
    def __init__(
        self,
        ollama_config: Optional[OllamaConfig] = None,
        species_db: Optional[IndiaSpeciesDatabase] = None
    ):
        self.ollama_config = ollama_config or OllamaConfig()
        self.species_db = species_db or IndiaSpeciesDatabase()
        self.sync_client = SyncOllamaClient(self.ollama_config)
    
    def _build_reasoning_prompt(
        self,
        context: ReasoningContext
    ) -> str:
        """Build prompt for species reasoning."""
        prompt_parts = []
        
        # Audio predictions
        if context.audio_predictions:
            prompt_parts.append("## Audio Analysis Results")
            for species_id, confidence in context.audio_predictions[:5]:
                species = self.species_db.get_species(species_id)
                if species:
                    prompt_parts.append(
                        f"- {species.common_name} ({species.scientific_name}): "
                        f"{confidence:.1%} confidence"
                    )
                    prompt_parts.append(f"  Call: {species.call_description}")
            prompt_parts.append(f"Audio Quality: {context.audio_quality}")
            prompt_parts.append("")
        
        # Location context
        if context.location_name or (context.latitude and context.longitude):
            prompt_parts.append("## Location")
            if context.location_name:
                prompt_parts.append(f"- Location: {context.location_name}")
            if context.latitude and context.longitude:
                prompt_parts.append(f"- Coordinates: {context.latitude:.4f}°N, {context.longitude:.4f}°E")
            if context.elevation:
                prompt_parts.append(f"- Elevation: {context.elevation}m")
            prompt_parts.append("")
        
        # Temporal context
        if context.month or context.time_of_day:
            prompt_parts.append("## Time")
            if context.month:
                months = ["January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
                prompt_parts.append(f"- Month: {months[context.month - 1]}")
            if context.time_of_day:
                prompt_parts.append(f"- Time of Day: {context.time_of_day}")
            prompt_parts.append("")
        
        # Habitat
        if context.habitat:
            prompt_parts.append(f"## Habitat: {context.habitat}")
            prompt_parts.append("")
        
        # User description
        if context.user_description:
            prompt_parts.append("## Observer Description")
            prompt_parts.append(context.user_description)
            prompt_parts.append("")
        
        prompt_parts.append("""## Task
Based on the above evidence, provide:
1. Your assessment of the most likely species
2. Confidence level (high/medium/low) with reasoning
3. Alternative species to consider
4. Whether this sighting is unusual or noteworthy for research
5. Any identifying features that would help confirm the identification

Format your response as:
ASSESSMENT: [Species name]
CONFIDENCE: [high/medium/low]
REASONING: [Your detailed reasoning]
ALTERNATIVES: [List of alternative species with brief notes]
NOTABLE: [yes/no] - [Explanation if yes]
""")
        
        return "\n".join(prompt_parts)
    
    def reason(
        self,
        context: ReasoningContext
    ) -> ReasoningResult:
        """
        Perform species reasoning using LLM.
        
        Args:
            context: Reasoning context with all available evidence
            
        Returns:
            ReasoningResult with final species assessment
        """
        prompt = self._build_reasoning_prompt(context)
        
        try:
            response = self.sync_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            # Parse response
            return self._parse_response(response, context)
            
        except Exception as e:
            # Fallback to audio-only prediction if LLM fails
            if context.audio_predictions:
                top_pred = context.audio_predictions[0]
                species = self.species_db.get_species(top_pred[0])
                return ReasoningResult(
                    species_id=top_pred[0],
                    species_name=species.common_name if species else "Unknown",
                    confidence=top_pred[1],
                    reasoning=f"LLM reasoning unavailable ({str(e)}). Using audio prediction only.",
                    alternative_species=[],
                    novelty_flag=False,
                    novelty_explanation=None
                )
            raise
    
    def _parse_response(
        self,
        response: str,
        context: ReasoningContext
    ) -> ReasoningResult:
        """Parse LLM response into structured result."""
        lines = response.strip().split('\n')
        
        assessment = ""
        confidence = 0.5
        reasoning = ""
        alternatives = []
        notable = False
        notable_explanation = None
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("ASSESSMENT:"):
                assessment = line.split(":", 1)[1].strip()
                current_section = "assessment"
            elif line.startswith("CONFIDENCE:"):
                conf_text = line.split(":", 1)[1].strip().lower()
                if "high" in conf_text:
                    confidence = 0.85
                elif "medium" in conf_text:
                    confidence = 0.6
                elif "low" in conf_text:
                    confidence = 0.35
                current_section = "confidence"
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
                current_section = "reasoning"
            elif line.startswith("ALTERNATIVES:"):
                alt_text = line.split(":", 1)[1].strip()
                if alt_text:
                    alternatives = [(a.strip(), 0.0) for a in alt_text.split(",")]
                current_section = "alternatives"
            elif line.startswith("NOTABLE:"):
                notable_text = line.split(":", 1)[1].strip().lower()
                notable = "yes" in notable_text.split("-")[0]
                if notable and "-" in notable_text:
                    notable_explanation = notable_text.split("-", 1)[1].strip()
                current_section = "notable"
            elif current_section == "reasoning" and line:
                reasoning += " " + line
            elif current_section == "alternatives" and line and line.startswith("-"):
                alternatives.append((line[1:].strip(), 0.0))
        
        # Find species ID
        species_id = -1
        species = self.species_db.get_by_name(assessment)
        if species:
            species_id = species.id
        elif context.audio_predictions:
            species_id = context.audio_predictions[0][0]
            species = self.species_db.get_species(species_id)
            if species:
                assessment = species.common_name
        
        return ReasoningResult(
            species_id=species_id,
            species_name=assessment,
            confidence=confidence,
            reasoning=reasoning,
            alternative_species=alternatives,
            novelty_flag=notable,
            novelty_explanation=notable_explanation
        )
    
    async def reason_async(
        self,
        context: ReasoningContext
    ) -> ReasoningResult:
        """Async version of reason()."""
        prompt = self._build_reasoning_prompt(context)
        
        async with OllamaClient(self.ollama_config) as client:
            response = await client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT
            )
            return self._parse_response(response, context)
    
    def generate_description(
        self,
        species_id: int,
        include_calls: bool = True,
        include_habitat: bool = True
    ) -> str:
        """
        Generate natural language description of a species.
        
        Useful for educational purposes and matching user descriptions.
        """
        species = self.species_db.get_species(species_id)
        if not species:
            return "Species not found."
        
        prompt = f"""Generate a brief, informative description of the {species.common_name} 
({species.scientific_name}) for birdwatchers in India.

Species information:
{self.species_db.get_species_for_llm_context(species_id)}

Include:
- Key identifying features
{"- Distinctive calls and songs" if include_calls else ""}
{"- Typical habitat and where to find it" if include_habitat else ""}
- Interesting facts

Keep it concise (2-3 paragraphs)."""

        try:
            return self.sync_client.generate(prompt=prompt)
        except Exception as e:
            # Fallback to database info
            return self.species_db.get_species_for_llm_context(species_id)
    
    def match_description(
        self,
        user_description: str,
        candidates: Optional[List[int]] = None
    ) -> List[Tuple[int, float, str]]:
        """
        Match user description to species.
        
        Args:
            user_description: User's description of the bird
            candidates: Optional list of species IDs to consider
            
        Returns:
            List of (species_id, match_score, explanation)
        """
        if candidates is None:
            candidates = list(self.species_db.species.keys())
        
        # Build context for matching
        species_info = []
        for species_id in candidates[:20]:  # Limit for efficiency
            species = self.species_db.get_species(species_id)
            if species:
                species_info.append(f"- {species.common_name}: {species.call_description}")
        
        prompt = f"""Match this bird description to the most likely species:

User Description: "{user_description}"

Candidate Species:
{chr(10).join(species_info)}

List the top 3 matches with confidence (0-100%) and brief explanation:
Format: [Species Name] - [confidence]% - [reason]"""

        try:
            response = self.sync_client.generate(prompt=prompt)
            
            # Parse matches from response
            matches = []
            for line in response.split('\n'):
                if '-' in line and '%' in line:
                    parts = line.split('-')
                    if len(parts) >= 2:
                        name = parts[0].strip().lstrip('0123456789. ')
                        species = self.species_db.get_by_name(name)
                        if species:
                            # Extract confidence
                            conf_part = parts[1] if len(parts) > 1 else ""
                            try:
                                conf = float(''.join(c for c in conf_part if c.isdigit())) / 100
                            except ValueError:
                                conf = 0.5
                            explanation = parts[2].strip() if len(parts) > 2 else ""
                            matches.append((species.id, min(1.0, conf), explanation))
            
            return matches
            
        except Exception:
            return []
    
    def check_ollama_status(self) -> Dict[str, any]:
        """Check Ollama server and model status."""
        try:
            is_healthy = self.sync_client.health_check()
            is_model_available = self.sync_client.is_model_available()
            
            return {
                "server_running": is_healthy,
                "model_available": is_model_available,
                "model_name": self.ollama_config.model,
                "status": "ready" if (is_healthy and is_model_available) else "not_ready"
            }
        except Exception as e:
            return {
                "server_running": False,
                "model_available": False,
                "model_name": self.ollama_config.model,
                "status": "error",
                "error": str(e)
            }

