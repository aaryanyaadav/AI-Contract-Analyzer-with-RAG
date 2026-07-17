from datetime import datetime
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import (
    CORSMiddleware
)

import tempfile
import shutil
import json
import os

from ingestion.main_ingestion import (
    IngestionPipeline
)

from orchestration.rag_orchestrator import (
    RAGOrchestrator
)

from backend.session_manager import (
    SessionManager
)

from memory.conversation_memory import (
    ConversationMemory
)

from backend.delete_manager import (
    DeleteManager
)

from backend.storage.document_registry import (
    DocumentRegistry
)

app = FastAPI()

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"]
)

# SESSION
# We create session_manager here, but instantiate tools per request
session_manager = SessionManager()

# HEALTH CHECK

@app.get("/")

async def root():

    return {

        "message":
        "Backend Running"
    }

# UPLOAD

@app.post("/upload")

async def upload_contract(

    file: UploadFile = File(...),
    session_id: str = Form(...)
):

    temp_path = None
    pipeline = None
    try:
        session_data = session_manager.get_or_create_session(session_id)
        
        pipeline = IngestionPipeline(
            chroma_path=session_data["chroma_path"],
            registry_path=session_data["registry_path"]
        )

        suffix = os.path.splitext(
            file.filename
        )[1]

        with tempfile.NamedTemporaryFile(

            delete=False,

            suffix=suffix

        ) as tmp:

            shutil.copyfileobj(
                file.file,
                tmp
            )

            temp_path = tmp.name

        result = (
            pipeline.ingest_document(
                temp_path,
                original_filename=file.filename
            )
        )

        parsed = json.loads(result)

        session_manager.set_active_document(
            session_id=session_data["session_id"],
            document_id=parsed["document_id"],
            filename=parsed["filename"]
        )

        return {

            "success": True,

            "document_id":
            parsed["document_id"],

            "filename":
            parsed["filename"]
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }
    finally:
        if pipeline:
            pipeline.close()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"[Upload] Successfully removed temp file: {temp_path}")
            except Exception as e:
                print(f"[Upload] Error removing temp file {temp_path}: {e}")

# CHAT

@app.post("/chat")

async def chat(data: dict):

    chatbot = None
    try:
        session_id = data.get("session_id")
        session_data = session_manager.get_or_create_session(session_id)

        document_id = data.get("document_id") or session_data.get(
            "active_document_id"
        )

        if not document_id:
            return {
                "success": False,
                "error": "No contract is active for this session. Upload a contract first."
            }

        memory = ConversationMemory(
            memory_dir=session_data["memory_path"]
        )

        conversation_history = memory.load_memory(
            document_id
        )
        
        evaluation_mode = data.get("evaluation_mode", False)

        chatbot = RAGOrchestrator(
            chroma_path=session_data["chroma_path"]
        )

        result = chatbot.chat(

            query=data["query"],

            document_id=document_id,

            conversation_history=conversation_history,

            evaluation_mode=evaluation_mode
        )

        answer = result.get("answer", "")

        if (
            isinstance(answer, str)
            and answer.startswith("RateLimitError:")
        ):
            return {
                "success": False,
                "error": answer
            }

        memory.append_message(
            document_id=document_id,
            role="user",
            content=data["query"]
        )

        memory.append_message(
            document_id=document_id,
            role="assistant",
            content=answer
        )

        response_payload = {

            "success": True,

            "answer":
            answer,

            "document_id": document_id,

            "sources": result.get("sources", []),

            "query_type": result.get("query_type")
        }

        if evaluation_mode and "metrics" in result:
            response_payload["metrics"] = result["metrics"]

        return response_payload

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }
    finally:
        if chatbot:
            chatbot.close()

# DELETE

@app.post("/delete-contract")

async def delete_contract(data: dict):

    delete_manager = None
    try:
        session_id = data.get("session_id")
        session_data = session_manager.get_or_create_session(session_id)
        
        delete_manager = DeleteManager(
            chroma_path=session_data["chroma_path"],
            registry_path=session_data["registry_path"],
            memory_path=session_data["memory_path"]
        )

        delete_manager.delete_contract(

            data["document_id"]
        )

        registry = DocumentRegistry(
            registry_path=session_data["registry_path"]
        )

        remaining_documents = registry.get_all_documents()

        if remaining_documents:
            latest_document = remaining_documents[-1]

            session_manager.set_active_document(
                session_id=session_data["session_id"],
                document_id=latest_document["document_id"],
                filename=latest_document.get("filename")
            )
        else:
            session_manager.clear_active_document(
                session_id=session_data["session_id"]
            )

        return {

            "success": True
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }
    finally:
        if delete_manager:
            delete_manager.close()

# SESSION STATE

@app.get("/session-state")
async def session_state(session_id: str | None = None):

    try:
        session_data = session_manager.get_or_create_session(
            session_id
        )

        messages = []

        documents = []

        registry = DocumentRegistry(
            registry_path=session_data["registry_path"]
        )

        documents = registry.get_all_documents()

        active_document_id = session_data.get(
            "active_document_id"
        )

        if active_document_id:
            memory = ConversationMemory(
                memory_dir=session_data["memory_path"]
            )

            messages = memory.load_memory(
                active_document_id
            )

        return {
            "success": True,
            "session_id": session_data["session_id"],
            "document_id": active_document_id,
            "filename": session_data.get("active_filename"),
            "documents": documents,
            "messages": messages
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

@app.post("/session-active-document")

async def set_session_active_document(data: dict):

    try:
        session_id = data.get("session_id")
        document_id = data.get("document_id")

        session_data = session_manager.get_or_create_session(
            session_id
        )

        registry = DocumentRegistry(
            registry_path=session_data["registry_path"]
        )

        selected_document = None

        for document in registry.get_all_documents():
            if document.get("document_id") == document_id:
                selected_document = document
                break

        if not selected_document:
            return {
                "success": False,
                "error": "Selected contract was not found in this session."
            }

        session_manager.set_active_document(
            session_id=session_data["session_id"],
            document_id=selected_document["document_id"],
            filename=selected_document.get("filename")
        )

        return {
            "success": True,
            "document_id": selected_document["document_id"],
            "filename": selected_document.get("filename")
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
@app.post("/end-session")
async def end_session(data: dict):

    try:
        session_id = data.get("session_id")

        if not session_id:
            return {
                "success": False,
                "error": "session_id is required"
            }

        session_manager.delete_session(session_id)

        return {
            "success": True
        }
    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
# SERVE FRONTEND STATIC & TEMPLATES

app.mount("/frontend/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/frontend/templetes/index.html", response_class=HTMLResponse)
async def serve_index():
    with open("frontend/templetes/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Ping

@app.get("/ping")
def ping():

    return {
        "status": "alive",
        "timestamp": str(datetime.utcnow())
    }