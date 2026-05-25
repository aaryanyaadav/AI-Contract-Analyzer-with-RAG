import json
from pydantic import BaseModel
from typing import List, Dict, Any

class ContractChunk(BaseModel):
    chunk_id: str
    text: str
    parent_section: str
    risk_flag: str = "Low"
    needs_review: bool = False  # <-- Added
    is_table: bool = False      # <-- Added

class ContractDocument(BaseModel):
    document_id: str
    filename: str
    metadata: Dict[str, Any]
    chunks: List[ContractChunk]

class DocumentSerializer:
    def serialize_document(self, document_id: str, filename: str, metadata: dict, chunks: list) -> str:
        try:
            validated_doc = ContractDocument(
                document_id=document_id,
                filename=filename,
                metadata=metadata,
                chunks=chunks
            )
            return validated_doc.model_dump_json(indent=2)
            
        except ValueError as e:
            print(f"Serialization Failed for {document_id}: {e}")
            raise