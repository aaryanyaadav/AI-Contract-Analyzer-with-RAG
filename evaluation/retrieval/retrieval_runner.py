import os
from typing import List, Dict, Any, Optional
from retrieval.mmr_retriver import MMRRetriever

def resolve_chroma_path(session_id: Optional[str] = None, chroma_path: Optional[str] = None) -> str:

    if chroma_path:
        return os.path.abspath(chroma_path)
    
    if session_id:
        # Resolve path relative to the project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, "storage", "sessions", session_id, "chroma_db")
        if os.path.exists(path):
            return path
        
        # Fallback to local relative path if project base resolution is not found
        fallback_path = os.path.join("storage", "sessions", session_id, "chroma_db")
        return os.path.abspath(fallback_path)
        
    raise ValueError("Either session_id or chroma_path must be provided to locate the vector store.")

class RetrievalRunner:

    def __init__(self, session_id: Optional[str] = None, chroma_path: Optional[Optional[str]] = None):
        self.chroma_path = resolve_chroma_path(session_id=session_id, chroma_path=chroma_path)
        self.retriever = MMRRetriever(chroma_path=self.chroma_path)

    def run_query(self, question: str, document_id: str, k: int = 5) -> Dict[str, Any]:

        # Production retrieve logic
        initial_fetch_k = max(15, k * 3)
        retrieved_results = self.retriever.retrieve(
            query=question,
            document_id=document_id,
            initial_fetch_k=initial_fetch_k,
            final_k=k
        )

        retrieved_chunks = []
        if retrieved_results:
            # We preserve the order of elements as returned by the production retriever.
            # We must not recompute scores or reorder.
            for idx, item in enumerate(retrieved_results):
                metadata = item.get("metadata", {})
                
                # Extract chunk index safely
                chunk_index_raw = metadata.get("chunk_index")
                chunk_index = None
                if chunk_index_raw is not None:
                    try:
                        chunk_index = int(chunk_index_raw)
                    except (ValueError, TypeError):
                        pass

                # Retrieve score if available, otherwise None. We do not recompute.
                retrieval_score = item.get("score") or metadata.get("score") or item.get("rerank_score") or None
                if retrieval_score is not None:
                    try:
                        retrieval_score = float(retrieval_score)
                    except (ValueError, TypeError):
                        pass

                retrieved_chunks.append({
                    "rank": idx + 1,  # 1-indexed rank
                    "chunk_id": metadata.get("chunk_id", ""),
                    "chunk_index": chunk_index,
                    "retrieval_score": retrieval_score,
                    "document_id": metadata.get("document_id", document_id),
                    "filename": metadata.get("filename", ""),
                    "parent_section": metadata.get("parent_section", ""),
                    "chunk_text": item.get("text", "")
                })

        return {
            "question": question,
            "document_id": document_id,
            "retrieved_chunks": retrieved_chunks
        }

    def close(self):
        if hasattr(self, "retriever") and self.retriever:
            self.retriever.close()
