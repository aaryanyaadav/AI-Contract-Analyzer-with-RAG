import os
import requests
from typing import Dict, Any, Optional

class RagasRunner:
    def __init__(self, backend_url: Optional[str] = None, session_id: Optional[str] = None):
        self.backend_url = backend_url
        self.session_id = session_id
        self._test_client = None

        if not self.backend_url:
            # Lazily import TestClient and app to avoid unnecessary side effects
            from fastapi.testclient import TestClient
            from backend.api.main import app
            self._test_client = TestClient(app)

    def query(self, question: str, document_id: str) -> Dict[str, Any]:
        """
        Queries the backend chat endpoint with evaluation_mode enabled.
        """
        payload = {
            "query": question,
            "document_id": document_id,
            "session_id": self.session_id
        }

        if self.backend_url:
            url = f"{self.backend_url.rstrip('/')}/chat"
            response = requests.post(url, json=payload)
            response.raise_for_status()
            res_json = response.json()
        else:
            response = self._test_client.post("/chat", json=payload)
            response.raise_for_status()
            res_json = response.json()

        if not res_json.get("success", False):
            raise RuntimeError(f"Backend chat API returned failure: {res_json.get('error', 'Unknown error')}")

        return {
            "generated_answer": res_json.get("answer", ""),
            "retrieved_sources": res_json.get("sources", [])
        }
