import os
import json
from datetime import datetime

class EvaluationExporter:
    """
    Evaluation artifact export module.
    Automatically saves chunking metadata and information to JSON files
    for downstream retrieval/generation evaluation and benchmarking.
    """
    def __init__(self, export_dir=None):
        if export_dir is None:
            # Resolved relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.export_dir = os.path.join(base_dir, "evaluation", "exports")
        else:
            self.export_dir = export_dir

        # Ensure directory structure exists: evaluation/exports/
        os.makedirs(self.export_dir, exist_ok=True)

    def export(self, document_id, filename, metadata, chunks):
        # Map metadata fields accurately
        doc_metadata = {
            "document_id": document_id,
            "filename": filename,
            "document_type": metadata.get("detected_type", "Unknown"),
            "total_chunks": len(chunks),
            "created_at": metadata.get("created_at", datetime.utcnow().isoformat()),
            "chunking_strategy": metadata.get("chunking_strategy", "RecursiveCharacterTextSplitter"),
            "embedding_model": metadata.get("embedding_model", "all-MiniLM-L6-v2")
        }

        # Build chunks array conforming to requirements
        chunk_list = []
        for idx, chunk in enumerate(chunks):
            page_numbers = chunk.get("page_numbers", [])
            page_number = chunk.get("page_number")
            if page_number is None and page_numbers:
                page_number = page_numbers[0]

            chunk_list.append({
                "chunk_index": idx,
                "chunk_id": chunk.get("chunk_id"),
                "page_number": page_number,
                "section_heading": chunk.get("section_heading") or chunk.get("parent_section", "General"),
                "parent_section": chunk.get("parent_section") or chunk.get("section_heading", "General"),
                "text": chunk.get("text", ""),
                "chunk_length": chunk.get("chunk_length") or len(chunk.get("text", "")),
                "average_confidence": chunk.get("average_confidence", 1.0),
                "needs_review": chunk.get("needs_review", False),
                "is_table": chunk.get("is_table", False)
            })

        export_data = {
            "document_metadata": doc_metadata,
            "chunks": chunk_list
        }

        # Export file path named using the document_id
        export_file_name = f"{document_id}.json"
        export_path = os.path.join(self.export_dir, export_file_name)

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"[EvaluationExporter] Exported evaluation metadata to {export_path}")
        return export_path
