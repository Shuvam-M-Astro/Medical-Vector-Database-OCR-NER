"""
Named Entity Recognition service for medical documents.
"""

import spacy
from transformers import pipeline
from typing import List, Dict, Any, Optional
from loguru import logger

from ..config import settings
from ..models.document import Entity, EntityType


class NERService:
    """Named Entity Recognition service for medical documents."""
    
    def __init__(self):
        """Initialize NER service."""
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self._load_models()
    
    def _load_models(self):
        """Load NER models."""
        try:
            # Load spaCy models
            logger.info("Loading spaCy models...")
            self.nlp = spacy.load(settings.NER_MODEL)
            
            # Try to load medical model
            try:
                self.medical_nlp = spacy.load(settings.MEDICAL_NER_MODEL)
                logger.info(f"Loaded medical NER model: {settings.MEDICAL_NER_MODEL}")
            except OSError:
                logger.warning(f"Medical NER model {settings.MEDICAL_NER_MODEL} not found. Using default model.")
                self.medical_nlp = self.nlp
            
            # Load transformer-based NER for medical entities
            self.medical_ner = pipeline(
                "ner",
                model="dmis-lab/biobert-base-cased-v1.1",
                aggregation_strategy="simple"
            )
            
            logger.info("NER models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load NER models: {str(e)}")
            raise
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract medical entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        try:
            # Process with spaCy
            doc = self.nlp(text)
            medical_doc = self.medical_nlp(text)
            
            # Combine entities from both models
            all_entities = []
            
            # Add spaCy entities
            for ent in doc.ents:
                all_entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.8  # Default confidence for spaCy
                })
            
            # Add medical spaCy entities
            for ent in medical_doc.ents:
                all_entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.85  # Higher confidence for medical model
                })
            
            # Process with transformer model for medical entities
            medical_results = self.medical_ner(text)
            for result in medical_results:
                if result['score'] >= self.confidence_threshold:
                    all_entities.append({
                        'text': result['word'],
                        'label': result['entity_group'],
                        'start': result['start'],
                        'end': result['end'],
                        'confidence': result['score']
                    })
            
            # Remove duplicates and convert to Entity objects
            seen = set()
            for ent_data in all_entities:
                key = (ent_data['text'], ent_data['start'], ent_data['end'])
                if key not in seen:
                    seen.add(key)
                    
                    entity_type = self._map_entity_type(ent_data['label'])
                    if entity_type:
                        entity = Entity(
                            text=ent_data['text'],
                            entity_type=entity_type,
                            start=ent_data['start'],
                            end=ent_data['end'],
                            confidence=ent_data['confidence']
                        )
                        entities.append(entity)
            
            # Sort by start position
            entities.sort(key=lambda x: x.start)
            
            logger.info(f"Extracted {len(entities)} entities from text")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []
    
    def _map_entity_type(self, label: str) -> Optional[EntityType]:
        """
        Map spaCy/transformer labels to our entity types.
        
        Args:
            label: Original entity label
            
        Returns:
            Mapped EntityType or None
        """
        label_mapping = {
            # spaCy general entities
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,
            'DATE': EntityType.DATE,
            'MONEY': EntityType.MONEY,
            'QUANTITY': EntityType.QUANTITY,
            
            # Medical entities
            'DISEASE': EntityType.DIAGNOSIS,
            'CONDITION': EntityType.DIAGNOSIS,
            'SYMPTOM': EntityType.DIAGNOSIS,
            'MEDICATION': EntityType.MEDICATION,
            'DRUG': EntityType.MEDICATION,
            'PROCEDURE': EntityType.PROCEDURE,
            'TREATMENT': EntityType.PROCEDURE,
            'BODY_PART': EntityType.BODY_PART,
            'ANATOMY': EntityType.BODY_PART,
            
            # Transformer medical entities
            'CHEMICAL': EntityType.MEDICATION,
            'DISEASE_OR_SYNDROME': EntityType.DIAGNOSIS,
            'SIGN_OR_SYMPTOM': EntityType.DIAGNOSIS,
            'PROCEDURE': EntityType.PROCEDURE,
            'ANATOMICAL_SITE': EntityType.BODY_PART,
            'MEDICAL_DEVICE': EntityType.PROCEDURE,
            
            # Additional mappings
            'HOSPITAL': EntityType.ORGANIZATION,
            'CLINIC': EntityType.ORGANIZATION,
            'DOCTOR': EntityType.PERSON,
            'PATIENT': EntityType.PERSON,
            'NURSE': EntityType.PERSON,
        }
        
        return label_mapping.get(label.upper())
    
    def get_entity_statistics(self, entities: List[Entity]) -> Dict[str, int]:
        """
        Get statistics about extracted entities.
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with entity type counts
        """
        stats = {}
        for entity in entities:
            entity_type = entity.entity_type.value
            stats[entity_type] = stats.get(entity_type, 0) + 1
        return stats
    
    def filter_entities_by_confidence(self, entities: List[Entity]) -> List[Entity]:
        """
        Filter entities by confidence threshold.
        
        Args:
            entities: List of entities
            
        Returns:
            Filtered list of entities
        """
        return [entity for entity in entities if entity.confidence >= self.confidence_threshold]
    
    def get_medical_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Get only medical-related entities.
        
        Args:
            entities: List of entities
            
        Returns:
            List of medical entities
        """
        medical_types = {
            EntityType.MEDICATION,
            EntityType.PROCEDURE,
            EntityType.DIAGNOSIS,
            EntityType.BODY_PART
        }
        return [entity for entity in entities if entity.entity_type in medical_types]
    
    def validate_entity(self, entity: Entity) -> bool:
        """
        Validate an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            True if entity is valid
        """
        return (
            len(entity.text.strip()) > 0 and
            entity.start >= 0 and
            entity.end > entity.start and
            entity.confidence >= 0 and
            entity.confidence <= 1
        ) 