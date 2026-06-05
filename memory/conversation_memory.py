import os
import json


class ConversationMemory:

    def __init__(

        self,

        memory_dir="storage/chat_memory"
    ):

        self.memory_dir = memory_dir

        os.makedirs(
            self.memory_dir,
            exist_ok=True
        )

    # =====================================
    # MEMORY FILE PATH
    # =====================================
    def _get_memory_path(
        self,
        document_id
    ):

        return os.path.join(

            self.memory_dir,

            f"{document_id}.json"
        )

    # =====================================
    # LOAD MEMORY
    # =====================================
    def load_memory(
        self,
        document_id
    ):

        path = self._get_memory_path(
            document_id
        )

        if not os.path.exists(path):
            return []

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    # =====================================
    # SAVE MEMORY
    # =====================================
    def save_memory(

        self,

        document_id,

        messages
    ):

        path = self._get_memory_path(
            document_id
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                messages,
                f,
                indent=2
            )

    # =====================================
    # APPEND MESSAGE
    # =====================================
    def append_message(

        self,

        document_id,

        role,

        content
    ):

        memory = self.load_memory(
            document_id
        )

        memory.append({

            "role": role,

            "content": content
        })

        # Keep only latest 10 messages
        memory = memory[-10:]

        self.save_memory(
            document_id,
            memory
        )

    # =====================================
    # CLEAR MEMORY
    # =====================================
    def clear_memory(
        self,
        document_id
    ):

        path = self._get_memory_path(
            document_id
        )

        if os.path.exists(path):
            os.remove(path)