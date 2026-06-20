from backend.model_manager import (
    ModelManager
)


class Reranker:

    def __init__(self):



        self.model = (
            ModelManager
            .get_reranker_model()
        )


    def rerank(

        self,

        query,

        retrieved_chunks,

        top_k=5
    ):

        if not retrieved_chunks:

            return []


        pairs = [

            (
                query,

                chunk["text"]
            )

            for chunk in retrieved_chunks
        ]

        scores = (
            self.model.predict(pairs)
        )


        scored_chunks = []

        for chunk, score in zip(

            retrieved_chunks,

            scores
        ):

            chunk["rerank_score"] = (
                float(score)
            )

            scored_chunks.append(
                chunk
            )

        scored_chunks.sort(

            key=lambda x:
            x["rerank_score"],

            reverse=True
        )

        return scored_chunks[:top_k]