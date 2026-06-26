import uuid
import os
import json
import shutil


class SessionManager:

    def __init__(self):

        self.base_dir = "storage/sessions"

        os.makedirs(
            self.base_dir,
            exist_ok=True
        )

    def _get_session_state_path(self, session_path):
        return os.path.join(
            session_path,
            "session_state.json"
        )

    def _load_session_state(self, session_path):
        state_path = self._get_session_state_path(
            session_path
        )

        if not os.path.exists(state_path):
            return {
                "active_document_id": None,
                "active_filename": None
            }

        with open(
            state_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def _save_session_state(self, session_path, state):
        state_path = self._get_session_state_path(
            session_path
        )

        with open(
            state_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                state,
                f,
                indent=2
            )

    def get_or_create_session(self, session_id):
        if not session_id:
            session_id = str(uuid.uuid4())

        session_path = os.path.join(
            self.base_dir,
            session_id
        )

        os.makedirs(
            session_path,
            exist_ok=True
        )

        os.makedirs(
            os.path.join(
                session_path,
                "chat_memory"
            ),
            exist_ok=True
        )

        session_state = self._load_session_state(
            session_path
        )

        return {

            "session_id": session_id,

            "session_path": session_path,

            "chroma_path":
            os.path.join(
                session_path,
                "chroma_db"
            ),

            "registry_path":
            os.path.join(
                session_path,
                "registry.json"
            ),

            "memory_path":
            os.path.join(
                session_path,
                "chat_memory"
            ),

            "active_document_id":
            session_state.get(
                "active_document_id"
            ),

            "active_filename":
            session_state.get(
                "active_filename"
            )
        }

    def create_session(self):
        return self.get_or_create_session(None)

    def set_active_document(

        self,

        session_id,

        document_id,

        filename
    ):
        session_data = self.get_or_create_session(
            session_id
        )

        session_path = session_data["session_path"]

        self._save_session_state(
            session_path,
            {
                "active_document_id": document_id,
                "active_filename": filename
            }
        )

    def clear_active_document(self, session_id):
        session_data = self.get_or_create_session(
            session_id
        )

        session_path = session_data["session_path"]

        self._save_session_state(
            session_path,
            {
                "active_document_id": None,
                "active_filename": None
            }
        )

    def delete_session(self, session_id):
        if not session_id:
            return False

        session_path = os.path.join(
            self.base_dir,
            session_id
        )

        if os.path.exists(session_path):
            shutil.rmtree(
                session_path,
                ignore_errors=True
            )

        return True
