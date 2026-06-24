from ingestion.vector_store import (
    ContractVectorStore
)

from memory.conversation_memory import (
    ConversationMemory
)

from backend.storage.document_registry import (
    DocumentRegistry
)


class DeleteManager:

    def __init__(

        self,

        chroma_path,

        registry_path,

        memory_path
    ):

        self.vector_store = (
            ContractVectorStore(
                db_path=chroma_path
            )
        )

        self.registry = (
            DocumentRegistry(
                registry_path=registry_path
            )
        )

        self.memory = (
            ConversationMemory(
                memory_dir=memory_path
            )
        )

    def delete_contract(
        self,
        document_id
    ):

        self.vector_store.delete_document(
            document_id
        )

        self.memory.clear_memory(
            document_id
        )

        self.registry.delete_document(
            document_id
        )

        print(
            f"[DeleteManager] "
            f"Deleted contract: "
            f"{document_id}"
        )

    def close(self):

        if hasattr(self, 'vector_store') and self.vector_store:

            self.vector_store.close()