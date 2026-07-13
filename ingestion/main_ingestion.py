import uuid
import os

from ingestion.validator import (
    validate_file
)

from ingestion.route import (
    DocumentRouter
)

from ingestion.normalizer import (
    DocumentNormalizer
)

from ingestion.metadata_builder import (
    MetadataBuilder
)

from ingestion.document_serializer import (
    DocumentSerializer
)

from ingestion.chunker import (
    ClauseChunker
)

from ingestion.vector_store import (
    ContractVectorStore
)

from backend.storage.document_registry import (
    DocumentRegistry
)

from risk_analysis.llm_risk_classifier import (
    LLMRiskClassifier
)


class IngestionPipeline:

    def __init__(

        self,

        chroma_path,

        registry_path=None
    ):

        # core components
        self.router = (
            DocumentRouter()
        )

        self.normalizer = (
            DocumentNormalizer()
        )

        self.chunker = (
            ClauseChunker()
        )

        self.metadata_builder = (
            MetadataBuilder()
        )

        self.serializer = (
            DocumentSerializer()
        )

        self.vector_store = (
            ContractVectorStore(
                db_path=chroma_path
            )
        )

        self.registry = (
            DocumentRegistry()
            if registry_path is None
            else DocumentRegistry(
                registry_path=registry_path
            )
        )

        self.risk_classifier = (
            LLMRiskClassifier()
        )

    # main ingestion
    
    def ingest_document(

        self,

        file_path,

        original_filename=None
    ):

        # validation
        
        validate_file(file_path)

        # ids
        
        document_id = str(
            uuid.uuid4()
        )

        filename = (
            original_filename
            if original_filename
            else os.path.basename(
                file_path
            )
        )

        # parse document
        
        parsed_document = (
            self.router.route_document(
                file_path
            )
        )

        # normalize
        
        normalized_blocks = (
            self.normalizer.normalize_document(
                parsed_document
            )
        )

        # chunk
        
        chunks = (
            self.chunker.split_into_clauses(
                normalized_blocks
            )
        )

        # risk classification
        
        batch_size = 5

        for i in range(

            0,

            len(chunks),

            batch_size
        ):

            chunk_batch = chunks[
                i:i + batch_size
            ]

            risk_results = (

                self.risk_classifier
                .classify_risk_batch(
                    chunk_batch
                )
            )

            for chunk, risk_data in zip(

                chunk_batch,

                risk_results
            ):

                chunk["risk_level"] = (
                    risk_data.get(
                        "risk_level",
                        "Low"
                    )
                )

                chunk["risk_category"] = (
                    risk_data.get(
                        "risk_category",
                        "Other"
                    )
                )

                chunk["risk_reason"] = (
                    risk_data.get(
                        "risk_reason",
                        ""
                    )
                )

        # vector storage
        
        self.vector_store.upsert_chunks(

            document_id=document_id,

            filename=filename,

            chunks=chunks
        )

        # metadata
        
        metadata = (
            self.metadata_builder
            .build_metadata(

                document_id=document_id,

                filename=filename,

                chunks=chunks
            )
        )

        # export evaluation artifact
        try:
            from evaluation.exporter import EvaluationExporter
            exporter = EvaluationExporter()
            exporter.export(
                document_id=document_id,
                filename=filename,
                metadata=metadata,
                chunks=chunks
            )
        except Exception as e:
            print(f"[IngestionPipeline] Error exporting evaluation metadata: {e}")

        # registry
        
        self.registry.register_document(

            document_id=document_id,

            filename=filename,

            metadata=metadata
        )

        # serialization
        
        final_json_document = (
            self.serializer.serialize_document(

                document_id=document_id,

                filename=filename,

                metadata=metadata,

                chunks=chunks
            )
        )

        return final_json_document

    def close(self):

        if hasattr(self, 'vector_store') and self.vector_store:

            self.vector_store.close()