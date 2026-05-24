class MetadataBuilder:
    def build_metadata(self, document_id, filename, chunks):
        
        # Look at the first 10 chunks to guess the document type
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
            "total_chunks_extracted": len(chunks),
            "detected_type": doc_type
        }