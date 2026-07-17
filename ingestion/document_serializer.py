
import json
class DocumentSerializer:
    def serialize_document(
        self,
        document_id,
        filename,
        metadata,
        chunks
    ):
        final_document = {
            "document_id": document_id,
            "filename": filename,
            "metadata": metadata,
            "chunks": chunks
        }
        return json.dumps(
            final_document,
            indent=2
        )

