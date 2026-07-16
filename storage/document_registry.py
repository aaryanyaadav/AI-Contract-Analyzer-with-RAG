import json
import os
from datetime import datetime
class DocumentRegistry:
    def __init__(
        self,
        registry_path="./storage/document_registry.json"
    ):
        self.registry_path = registry_path
        os.makedirs(
            os.path.dirname(
                self.registry_path
            ),
            exist_ok=True
        )
        if not os.path.exists(
            self.registry_path
        ):
            with open(
                self.registry_path,
                "w",
                encoding="utf-8"

            ) as f:
                json.dump([], f)
    def register_document(
        self,
        document_id,
        filename,
        metadata
    ):
        documents = self.get_all_documents()
        document_entry = {
            "document_id":
            document_id,
            "filename":
            filename,
            # User-facing editable name
            "display_name":
            filename,
            "upload_time":
            datetime.now().isoformat(),
            "document_type":
            metadata.get(
                "detected_type",
                "Unknown"
            ),
            "chunk_count":
            metadata.get(
                "total_chunks_extracted",
                0
            )
        }
        documents.append(
            document_entry
        )
        with open(
            self.registry_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                documents,
                f,
                indent=2
            )
        print(
            f"[Registry] Registered "
            f"document: {document_id}"
        )
    def get_all_documents(self):
        with open(
            self.registry_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    def delete_document(
        self,
        document_id
    ):
        documents = self.get_all_documents()
        updated_documents = [
            doc for doc in documents
            if doc["document_id"]
            != document_id
        ]
        with open(
            self.registry_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                updated_documents,
                f,
                indent=2
            )
        print(
            f"[Registry] Deleted "
            f"document: {document_id}"
        )
    def rename_document(
        self,
        document_id,
        new_display_name
    ):
        documents = self.get_all_documents()
        for doc in documents:
            if (
                doc["document_id"]
                == document_id
            ):
                doc["display_name"] = (
                    new_display_name
                )
                break
        with open(
            self.registry_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                documents,
                f,
                indent=2
            )
        print(
            f"[Registry] Renamed "
            f"document: {document_id}"
        )