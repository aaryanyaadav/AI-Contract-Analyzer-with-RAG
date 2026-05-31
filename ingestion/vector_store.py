import os
import chromadb

from backend.model_manager import (
    ModelManager
)


class ContractVectorStore:

    def __init__(

        self,

        db_path,

        collection_name="contract_clauses"
    ):

        """
        Persistent ChromaDB Vector Store
        with session-isolated storage.
        """

        self.db_path = db_path

        self.collection_name = (
            collection_name
        )


        os.makedirs(
            self.db_path,
            exist_ok=True
        )


        self.client = chromadb.PersistentClient(
            path=self.db_path
        )


        from backend.model_manager import (
            ModelManager
        )

        self.encoder = (
            ModelManager
            .get_embedding_model()
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name
            )
        )

    def upsert_chunks(

        self,

        document_id,

        filename,

        chunks
    ):

        if not chunks:

            print(
                "[VectorStore] No chunks provided."
            )

            return

        ids = []

        documents = []

        metadatas = []


        for chunk in chunks:

            documents.append(
                chunk["text"]
            )

            ids.append(
                chunk["chunk_id"]
            )

            metadatas.append({

                "document_id":
                document_id,

                "filename":
                filename,

                "parent_section":
                chunk["parent_section"],

                "risk_level":
                chunk.get(
                    "risk_level",
                    "Low"
                ),

                "risk_category":
                chunk.get(
                    "risk_category",
                    "Other"
                ),

                "risk_reason":
                chunk.get(
                    "risk_reason",
                    ""
                ),

                "needs_review":
                str(
                    chunk["needs_review"]
                ),

                "is_table":
                str(
                    chunk["is_table"]
                )
            })


        print(
            f"[VectorStore] "
            f"Generating embeddings "
            f"for {len(chunks)} chunks..."
        )

        computed_embeddings = (
            self.encoder.encode(

                documents,

                convert_to_numpy=True
            ).tolist()
        )


        print(
            "[VectorStore] "
            "Saving vectors to ChromaDB..."
        )

        self.collection.upsert(

            ids=ids,

            embeddings=computed_embeddings,

            documents=documents,

            metadatas=metadatas
        )

        print(
            f"[VectorStore] "
            f"Successfully indexed "
            f"{len(chunks)} chunks."
        )


    def query_contracts(

        self,

        query_text,

        top_k=5,

        doc_id_filter=None
    ):

        where_filter = {}

        if doc_id_filter:

            where_filter["document_id"] = (
                doc_id_filter
            )


        query_vector = (
            self.encoder.encode(

                [query_text],

                convert_to_numpy=True
            ).tolist()
        )

        results = self.collection.query(

            query_embeddings=query_vector,

            n_results=top_k,

            where=(
                where_filter
                if where_filter
                else None
            ),

            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )


        if not results["ids"]:

            results["embeddings"] = [[]]

            return results

        retrieved_ids = results["ids"][0]

        if not retrieved_ids:

            results["embeddings"] = [[]]

            return results


        embedding_records = (
            self.collection.get(

                ids=retrieved_ids,

                include=["embeddings"]
            )
        )

        results["embeddings"] = [

            embedding_records[
                "embeddings"
            ]
        ]

        return results

    def delete_document(
        self,
        document_id
    ):

        self.collection.delete(

            where={
                "document_id":
                document_id
            }
        )

        print(
            f"[VectorStore] Deleted "
            f"document: {document_id}"
        )