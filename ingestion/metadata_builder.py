from datetime import datetime


class MetadataBuilder:

    def build_metadata(self, document_id, filename, chunks):

        sample_text = " ".join([c["text"] for c in chunks[:10]]).upper()

        doc_type = "Unknown"

        if "AGREEMENT" in sample_text:
            doc_type = "Agreement"
        elif "EMPLOYMENT" in sample_text:
            doc_type = "Employment Contract"
        elif "INSURANCE" in sample_text:
            doc_type = "Insurance Contract"

        return {
            "global_document_id": document_id,
            "source_filename": filename,
            "detected_type": doc_type,
            "total_chunks_extracted": len(chunks),

            # Helpful for evaluation
            "created_at": datetime.utcnow().isoformat(),
            "chunking_strategy": "RecursiveCharacterTextSplitter",
            "embedding_model": "all-MiniLM-L6-v2",
            "version": "1.0"
        }