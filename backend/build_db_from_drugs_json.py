"""
Build Medication Vector Database from drugs.json

This script loads drugs from drugs.json and creates the FAISS vector database.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_database_from_drugs_json():
    """Build vector database from drugs.json file."""
    from medication_vector_db import MedicationVectorDB
    
    # Paths
    backend_dir = Path(__file__).parent
    drugs_json_path = backend_dir / "drugs.json"
    db_path = backend_dir / "medication_db"
    
    if not drugs_json_path.exists():
        logger.error(f"drugs.json not found at: {drugs_json_path}")
        return None
    
    # Load drugs.json
    logger.info(f"Loading drugs from: {drugs_json_path}")
    with open(drugs_json_path, 'r', encoding='utf-8') as f:
        drugs_data = json.load(f)
    
    logger.info(f"Loaded {len(drugs_data)} drugs from JSON")
    
    # Convert to vector DB format
    medications = []
    for drug in drugs_data:
        med = {
            "name": drug.get("name", ""),
            "generic": drug.get("generic", drug.get("name", "")),
            "dosage": "",  # Not in source, but required field
            "forme": "",   # Not in source, but required field
            "usage": "ESSENTIAL" if drug.get("listed_in_tunisia_neml") else "RECOMMENDED",
            "category": drug.get("class", "Unknown"),
            "description": ", ".join(drug.get("common_uses", [])),
            "common_uses": drug.get("common_uses", []),
            "side_effects": drug.get("common_side_effects", []),
            "precautions": drug.get("precautions_contraindications", []),
            "alternatives": []
        }
        medications.append(med)
    
    # Delete old database files
    import os
    index_path = db_path / "faiss_index.bin"
    metadata_path = db_path / "metadata.json"
    
    if index_path.exists():
        os.remove(index_path)
        logger.info(f"Deleted old index: {index_path}")
    if metadata_path.exists():
        os.remove(metadata_path)
        logger.info(f"Deleted old metadata: {metadata_path}")
    
    # Create new database
    logger.info(f"Creating vector database at: {db_path}")
    db = MedicationVectorDB(str(db_path))
    db.add_medications(medications)
    
    # Show statistics
    stats = db.get_stats()
    logger.info("\n" + "="*60)
    logger.info("DATABASE STATISTICS")
    logger.info("="*60)
    logger.info(f"Total medications: {stats['total_medications']}")
    
    if stats.get('categories'):
        logger.info("\nTop Categories:")
        for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {cat}: {count}")
    
    # Test search
    logger.info("\n" + "="*60)
    logger.info("TESTING DATABASE - Sample Searches")
    logger.info("="*60)
    
    test_queries = ["paracetamol", "antibiotic", "diabetes", "hypertension", "ibuprofen"]
    for query in test_queries:
        logger.info(f"\nSearch: '{query}'")
        results = db.search(query, top_k=3)
        for r in results[:3]:
            score = r.get('similarity_score', 0)
            logger.info(f"  - {r['name']} ({r.get('category', 'N/A')}) - Score: {score:.3f}")
    
    logger.info("\n" + "="*60)
    logger.info("✓ Database created successfully!")
    logger.info(f"✓ Total medications: {len(db.metadata)}")
    logger.info("="*60)
    
    return db


if __name__ == "__main__":
    build_database_from_drugs_json()
