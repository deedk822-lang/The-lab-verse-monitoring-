import os
import sys
from datetime import datetime

# Adjust path to import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from services.african_manuscript_transcriber import AfricanManuscriptTranscriber
    from services.metadata_manager import MetadataManager
except ImportError as e:
    print("Error: Could not import necessary services.")
    print(f"Details: {e}")
    sys.exit(1)

def ingest_document(image_path: str, language: str, metadata: dict):
    """
    Simulates a complete document ingestion pipeline.
    """
    print(f"--- Starting Ingestion for {image_path} ---")
<<<<<<< HEAD

    # 1. Initialize services
    transcriber = AfricanManuscriptTranscriber()
    metadata_manager = MetadataManager()

=======

    # 1. Initialize services
    transcriber = AfricanManuscriptTranscriber()
    metadata_manager = MetadataManager()

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    # 2. Transcribe the document
    print(f"Step 1: Transcribing document in {language}...")
    transcribed_text = transcriber.transcribe(image_path, language=language)
    print("   Transcription complete (placeholder).")
<<<<<<< HEAD

    # 3. Add transcription to metadata
    metadata["transcribed_text"] = transcribed_text
    metadata["ingestion_date"] = datetime.now().isoformat()

=======

    # 3. Add transcription to metadata
    metadata["transcribed_text"] = transcribed_text
    metadata["ingestion_date"] = datetime.now().isoformat()

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    # 4. Add metadata to the metadata store
    document_id = os.path.splitext(os.path.basename(image_path))[0]
    print(f"Step 2: Adding metadata for document ID '{document_id}'...")
    metadata_manager.add_metadata(document_id, metadata)
    print("   Metadata added successfully.")
<<<<<<< HEAD

    print(f"--- Ingestion Complete for {document_id} ---")

=======

    print(f"--- Ingestion Complete for {document_id} ---")

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    # Verify by searching for the new document
    print("\nVerifying ingestion by searching for the document...")
    results = metadata_manager.search_metadata(query="ANC", language="en")
    if any(r["document_id"] == document_id for r in results):
        print("✅ Verification successful: Document is searchable.")
    else:
        print("❌ Verification failed: Document not found in search results.")


if __name__ == "__main__":
    # Example usage of the ingestion pipeline
    sample_image_path = "path/to/archives/mbeki_letter_001.jpg"
    sample_metadata = {
        "title": {
            "en": "Letter from Nelson Mandela to Thabo Mbeki",
            "zu": "Incwadi evela kuNelson Mandela iya kuThabo Mbeki"
        },
        "description": {
            "en": "A handwritten letter discussing the future of the ANC.",
            "zu": "Incwadi ebhalwe ngesandla exoxa ngekusasa le-ANC."
        },
        "author": "Nelson Mandela",
        "date": "1995-05-10",
        "tags": ["anc", "correspondence", "1990s"]
    }
    sample_language = "zulu"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    ingest_document(sample_image_path, sample_language, sample_metadata)
