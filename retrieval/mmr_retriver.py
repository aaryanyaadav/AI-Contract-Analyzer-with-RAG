import numpy as np
import torch

from ingestion.vector_store import (
    ContractVectorStore
)

from sentence_transformers.util import (
    cos_sim
)


class MMRRetriever:

    def __init__(

        self,

        chroma_path
    ):

        self.vector_store = (
            ContractVectorStore(
                db_path=chroma_path
            )
        )

    # =====================================
    # MAXIMAL MARGINAL RELEVANCE
    # =====================================
    def maximal_marginal_relevance(

        self,

        query_embedding,

        candidate_embeddings,

        lambda_param=0.7,

        top_k=5
    ):

        # =====================================
        # FORCE FLOAT32 TENSORS
        # =====================================
        query_embedding = torch.tensor(

            query_embedding,

            dtype=torch.float32
        )

        candidate_embeddings = torch.tensor(

            candidate_embeddings,

            dtype=torch.float32
        )

        selected_indices = []

        # =====================================
        # QUERY SIMILARITY
        # =====================================
        similarity_to_query = cos_sim(

            query_embedding,

            candidate_embeddings

        )[0].numpy()

        # =====================================
        # FIRST BEST MATCH
        # =====================================
        first_idx = np.argmax(
            similarity_to_query
        )

        selected_indices.append(
            first_idx
        )

        # =====================================
        # ITERATIVE MMR SELECTION
        # =====================================
        while len(selected_indices) < min(

            top_k,

            len(candidate_embeddings)
        ):

            remaining_indices = [

                i for i in range(
                    len(candidate_embeddings)
                )

                if i not in selected_indices
            ]

            mmr_scores = []

            for idx in remaining_indices:

                # =============================
                # RELEVANCE
                # =============================
                relevance = (
                    similarity_to_query[idx]
                )

                # =============================
                # DIVERSITY
                # =============================
                diversity = max([

                    cos_sim(

                        candidate_embeddings[idx],

                        candidate_embeddings[
                            selected_idx
                        ]

                    ).item()

                    for selected_idx
                    in selected_indices
                ])

                # =============================
                # MMR SCORE
                # =============================
                mmr_score = (

                    lambda_param * relevance

                    - (1 - lambda_param)
                    * diversity
                )

                mmr_scores.append(
                    (idx, mmr_score)
                )

            # =============================
            # SELECT BEST NEXT CHUNK
            # =============================
            next_selected = max(

                mmr_scores,

                key=lambda x: x[1]
            )[0]

            selected_indices.append(
                next_selected
            )

        return selected_indices

    # =====================================
    # RETRIEVE
    # =====================================
    def retrieve(

        self,

        query,

        document_id,

        initial_fetch_k=15,

        final_k=5
    ):

        # =====================================
        # QUERY EMBEDDING
        # =====================================
        query_embedding = np.array(

            self.vector_store.encoder.encode(

                [query],

                convert_to_numpy=True
            ),

            dtype=np.float32
        )

        # =====================================
        # VECTOR SEARCH
        # =====================================
        results = (
            self.vector_store.collection.query(

                query_embeddings=
                query_embedding.tolist(),

                n_results=
                initial_fetch_k,

                where={
                    "document_id":
                    document_id
                },

                include=[
                    "documents",
                    "metadatas",
                    "distances",
                    "embeddings"
                ]
            )
        )

        # =====================================
        # SAFETY CHECK
        # =====================================
        if (
            not results["documents"]
            or
            not results["documents"][0]
        ):

            return []

        docs = results["documents"][0]

        metas = results["metadatas"][0]

        embeddings = np.array(

            results["embeddings"][0],

            dtype=np.float32
        )

        # =====================================
        # MMR SELECTION
        # =====================================
        selected_indices = (
            self.maximal_marginal_relevance(

                query_embedding=
                query_embedding,

                candidate_embeddings=
                embeddings,

                top_k=final_k
            )
        )

        # =====================================
        # FINAL RESULTS
        # =====================================
        final_results = []

        for idx in selected_indices:

            final_results.append({

                "text": docs[idx],

                "metadata": metas[idx]
            })

        return final_results