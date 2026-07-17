from sentence_transformers import (

    SentenceTransformer,

    CrossEncoder
)
class ModelManager:
    _embedding_model = None
    _reranker_model = None
    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            print(
                "[ModelManager] "
                "Loading embedding model..."
            )
            cls._embedding_model = (
                SentenceTransformer(
                    "all-MiniLM-L6-v2"
                )
            )
        return cls._embedding_model
    @classmethod
    def get_reranker_model(cls):
        if cls._reranker_model is None:
            print(
                "[ModelManager] "
                "Loading reranker model..."
            )
            cls._reranker_model = (
                CrossEncoder(
                    "cross-encoder/ms-marco-MiniLM-L-6-v2"
                )
            )
        return cls._reranker_model