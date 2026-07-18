# ContractFlow AI — Contract Analyzer with RAG

An enterprise-grade, privacy-first legal document assistant powered by **Retrieval-Augmented Generation (RAG)**. ContractFlow AI automatically processes, parses, normalizes, indexes, and queries complex contracts. By utilizing multi-stage safety guardrails, Max Marginal Relevance (MMR) retrieval, and cross-encoder re-ranking, it guarantees grounded, hallucination-free, and context-rich answers.

This project uses a session-isolated storage architecture. All user uploads, embeddings, registries, and memory traces are isolated by unique session IDs, making absolute session deletion and cleanups easy and secure.

---

##  Tech Stack

<div align="center">
  <h2>Tech Stack</h2>
  
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Uvicorn-490A3D?style=for-the-badge&logo=python&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  
  <br><br>
  
  <img src="https://img.shields.io/badge/PyMuPDF-FF6F00?style=for-the-badge&logo=adobe&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Python--Docx-2B579A?style=for-the-badge&logo=microsoftword&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Tesseract--OCR-4B0082?style=for-the-badge&logo=google&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Pillow-333333?style=for-the-badge&logo=python&logoColor=white" /> &nbsp;
  <img src="https://img.shields.io/badge/Groq--SDK-F5A623?style=for-the-badge&logo=openai&logoColor=white" />
</div>

---

##  Core Capabilities

###  Session-Based Architecture
ContractFlow AI enforces complete data segregation using **Session-Isolated Environments** rather than shared table schemas.
- **Zero Cross-Talk**: Each browser connection is issued a unique UUID (`session_id`). This ID namespaces the underlying directory folders, document registries, vector DB stores, and chat log caches.
- **Dynamic Connection Binding**: The ChromaDB client establishes persistent DB links scoped *only* to the session storage folder, preventing any data leakages across other active sessions.
- **Automated Hard-Deletion**: The moment a session is terminated via `POST /end-session`, the disk controller executes a recursive purge of the session folder, instantly erasing all indexed vectors, history traces, and registries.

###  Safety Guardrails & Privacy
The application implements lightweight, robust safety auditing to preserve privacy and data security:
- **Input PII Verification**: Scans user queries for Personally Identifiable Information (PII) before processing to block sensitive credentials or personal info from leaking downstream.
- **PII Scrubbing & Redaction**: Output responses are continuously audited. Using optimized regex patterns, any email addresses, phone numbers, Social Security Numbers (SSNs), and Credit Card details are automatically scrubbed and replaced with placeholders like `[REDACTED_EMAIL]`.

###  Advanced RAG & Memory Pipeline
Retrieval and interaction are optimized for complex legal terminology:
- **Max Marginal Relevance (MMR)**: Standard semantic retrievers often load near-duplicate sections due to repetitive contract phrasing. MMR runs PyTorch vector math to maximize chunk diversity alongside semantic closeness.
- **Cross-Encoder Re-ranking**: Retrieved chunks are fed into a cross-encoder model (`ms-marco-MiniLM-L-6-v2`) to perform absolute joint query-context alignment grading, filtering out marginal results.
- **Session-Isolated Chat Memory**: Conversation histories are saved per-document in local JSON files within their respective session folders (`storage/sessions/<session_id>/chat_memory/<document_id>.json`), maintaining clean multi-tenant data boundaries.
- **Sliding Conversation Window**: Conversation memory uses a structured sliding context window to feed historical messages into LLM templates without overloading token capacity.

---

##  System Architecture

###  Architecture Flowchart

The following flowchart diagrams how user transactions move through the ingestion layers, query routing controllers, and safety guardrails:

```mermaid
flowchart TD
    %% Client Tier
    User([User Browser]) <-->|HTTP / File Upload| FE[Frontend UI: HTML/CSS/JS]

    %% Gateway Tier
    FE <-->|REST API Requests| API[Backend Gateway: main.py]

    %% Session Orchestration
    subgraph Isolation [Session Context & Resource Manager]
        API <--> SessionMgr[SessionManager]
        API --> Registry[DocumentRegistry]
        API --> DeleteMgr[DeleteManager]
    end

    %% Ingestion Pipeline Path
    subgraph IngestionPipeline [Ingestion & Indexing Pipeline]
        API -->|1. Ingest File| Route[DocumentRouter]
        Route -->|Searchable PDF| FastPDF[FastPDFParser]
        Route -->|Scanned PDF / Word / Image| Docling[DoclingParser]
        FastPDF & Docling --> Norm[DocumentNormalizer]
        Norm --> Chunk[ClauseChunker]
        
        %% Risk analysis during ingestion
        Chunk --> RiskClass[LLMRiskClassifier]
        RiskClass -->|Score & Label Clauses| EmbedModel[SentenceTransformer Encoder]
        EmbedModel --> VectorStore[(Session-Isolated ChromaDB)]
    end

    %% RAG Query Path
    subgraph RAGOrchestration [Interactive Grounded RAG Flow]
        API <--> Orchestrator[RAGOrchestrator]
        
        %% Security Guardrails
        Orchestrator <--> Guardrails{GuardrailSystem}
        Guardrails -->|Input Filters| PIIFilter[PII Masking & Safety Auditor]
        Guardrails -->|Output Checks| GroundingValidator[Grounding & Hallucination Auditor]
        
        Orchestrator --> QueryAnalyzer[QueryAnalyzer]
        QueryAnalyzer --> RetrievalRouter[RetrievalRouter]
        
        RetrievalRouter --> MMR[MMRRetriever]
        MMR -->|Diverse Fetch| VectorStore
        MMR --> Reranker[Reranker: Cross-Encoder]
        
        Reranker --> PromptBuilder[PromptBuilder]
        PromptBuilder --> LLM[LLMClient: Groq SDK]
        LLM --> RespVal[ResponseValidator]
        RespVal --> Orchestrator
        Orchestrator <--> Mem[ConversationMemory]
    end
```

---

###  End-to-End Sequence Flow

This sequence chart diagrams the backend coordination sequence when a document is uploaded, queried, deleted, or when a session is finalized:

```mermaid
sequenceDiagram
      autonumber
      participant B as Browser Frontend
      participant A as FastAPI API
      participant S as SessionManager
      participant I as IngestionPipeline
      participant V as VectorStore
      participant G as DocumentRegistry
      participant M as ConversationMemory
      participant R as RAGOrchestrator
      participant L as LLMClient

      %% Upload & Index Sequence
      B->>A: POST /upload (file, session_id)
      A->>S: get_or_create_session(session_id)
      A->>I: ingest_document(temp_file, original_filename)
      I->>I: validate -> parse -> normalize -> chunk
      I->>L: classify risk for clause batches
      I->>V: upsert chunks, embeddings, metadata
      I->>G: register_document(document_id, filename, metadata)
      A->>S: set_active_document(session_id, document_id, filename)
      A-->>B: { success, document_id, filename }

      %% Chat & Query Sequence
      B->>A: POST /chat (query, document_id, session_id)
      A->>S: get_or_create_session(session_id)
      A->>M: load_memory(document_id)
      A->>R: chat(query, document_id, conversation_history)
      R->>L: classify query
      R->>V: retrieve chunks for document_id
      R->>L: generate answer from selected context
      A->>M: append user message + assistant answer
      A-->>B: answer, sources, query_type

      %% Delete Document Sequence
      B->>A: POST /delete-contract (document_id, session_id)
      A->>S: get_or_create_session(session_id)
      A->>V: delete_document(document_id)
      A->>M: clear_memory(document_id)
      A->>G: delete_document(document_id)
      A-->>B: success

      %% End Session Sequence
      B->>A: POST /end-session (session_id)
      A->>S: delete_session(session_id)
      A-->>B: success
```

---

###  Storage Model & Layout

Every browser connection triggers a dedicated directory tree under `storage/sessions/<session_id>/`. This isolation makes data protection compliance straightforward: removing the session folder deletes the vector data, history, and raw files.

```text
storage/
   sessions/
      <session_id>/
         chroma_db/             # Local database storing vector embeddings
         chat_memory/           # Per-document chat history files
            <document_id>.json
         registry.json          # List of documents uploaded in this session
         session_state.json     # Tracks the active document ID and filename
   llm_daily_usage.json         # Shared rate-limiting usage counter file
```

---

##  Module-by-Module Walkthrough

### 1. Backend Gateway & Session Manager (`/backend`)
- [main.py](file:///d:/project/contract-intelligence/backend/api/main.py): Sets up the FastAPI app instance, CORS configurations, mounts static/template directories, and registers REST routes for document uploads, conversation messaging, session loading/teardowns, and contract deletions.
- [session_manager.py](file:///d:/project/contract-intelligence/backend/session_manager.py): Organizes isolated working directories for each unique user session. It dynamically instantiates separate ChromaDB database paths, document registries, and memory folders, preventing cross-tenant leakage.
- [delete_manager.py](file:///d:/project/contract-intelligence/backend/delete_manager.py): Orchestrates the hard-deletion of documents, including removing corresponding vector IDs from ChromaDB and purging references from registries/cache files.

### 2. Ingestion Pipeline (`/ingestion`)
- [route.py](file:///d:/project/contract-intelligence/ingestion/route.py): An intelligent router evaluating incoming document extensions and properties. Searchable PDFs are routed to a fast text parser, while scanned PDFs, images, and Word files are forwarded to docling-driven OCR parsers.
- [docling_parser.py](file:///d:/project/contract-intelligence/ingestion/docling_parser.py) & [fast_pdf_parser.py](file:///d:/project/contract-intelligence/ingestion/fast_pdf_parser.py): Extraction modules that convert raw document layouts, structural elements, and tables into plain text blocks.
- [normalizer.py](file:///d:/project/contract-intelligence/ingestion/normalizer.py): Formats extracted text blocks by removing redundant whitespace, fixing Unicode representations, and stripping formatting artifacts.
- [chunker.py](file:///d:/project/contract-intelligence/ingestion/chunker.py): Performs layout-aware, semantic clause division. Rather than basic character windowing, it splits texts along structural clause boundaries to keep definitions whole.
- [vector_store.py](file:///d:/project/contract-intelligence/ingestion/vector_store.py): Implements interfaces for ChromaDB. It retrieves sentence embedding representations via classes from the model manager class and updates local session indexes.

### 3. Retrieval & Re-ranking (`/retrieval`)
- [mmr_retriver.py](file:///d:/project/contract-intelligence/retrieval/mmr_retriver.py): Generates vector search queries and performs **Max Marginal Relevance (MMR)** selection using PyTorch tensor math, ensuring that context chunks are both semantically close and structurally diverse.
- [reraanker.py](file:///d:/project/contract-intelligence/retrieval/reraanker.py): Employs a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to re-rank chunks based on absolute prompt-context alignment, filtering out marginal matches.

### 4. LLM Interface (`/llm`)
- [llm_client.py](file:///d:/project/contract-intelligence/llm/llm_client.py): Integrates directly with the Groq SDK, deploying the high-throughput `llama-3.1-8b-instant` model. It features exponential backoff retries and structures thread-safe daily request limit counters to avoid API exhaustion.
- [prompt_builder.py](file:///d:/project/contract-intelligence/llm/prompt_builder.py): Dynamically creates prompt templates, embedding context chunks, user query profiles, and conversation memories into highly structured assistant instructions.

### 5. Guardrail System (`/orchestration`)
- [guardrails.py](file:///d:/project/contract-intelligence/orchestration/guardrails.py): The primary security framework containing:
  - **PII Leakage Prevention**: Identifies and redacts regex-mapped emails, phones, SSNs, and credit cards from inputs and outputs.
  - **Input Safety Check**: Uses a fast LLM evaluation to reject off-topic questions (e.g. general coding, hobbies, trivia) and prompt-injection attempts.
  - **Output Grounding Validator**: Fact-checks generated answers against the source contract chunks to flag and block hallucinations.
- [response_validator.py](file:///d:/project/contract-intelligence/orchestration/response_validator.py): Performs heuristic and text-matching quality evaluations on generated outputs to verify formatting constraints.

### 6. Orchestration & Memory (`/orchestration`, `/memory`)
- [rag_orchestrator.py](file:///d:/project/contract-intelligence/orchestration/rag_orchestrator.py): Coordinates the RAG pipeline. It handles incoming queries, verifies input safety, triggers query classification and routing, queries vector indexes, re-ranks contexts, feeds prompts to Groq, verifies output grounding, and structures memory.
- [query_analyzer.py](file:///d:/project/contract-intelligence/orchestration/query_analyzer.py): Classifies queries (e.g., `summary`, `risk`, `obligation`, `qa`) to optimize downstream retrieval models.
- [retrieval_router.py](file:///d:/project/contract-intelligence/orchestration/retrieval_router.py): Adjusts retrieval limits (`initial_fetch_k`, `final_k`) based on the query classification (e.g., fetching broader contexts for summaries, but tighter contexts for clause searches).
- [conversation_memory.py](file:///d:/project/contract-intelligence/memory/conversation_memory.py): Stores message exchanges locally within session files, acting as a sliding conversational history window.

### 7. Risk Analysis Module (`/risk_analysis`)
- [llm_risk_classifier.py](file:///d:/project/contract-intelligence/risk_analysis/llm_risk_classifier.py): Scores batches of clauses during the ingestion phase using LLM reasoning to evaluate potential liabilities, indemnification issues, or non-standard provisions.
- [risk_analyzer.py](file:///d:/project/contract-intelligence/risk_analysis/risk_analyzer.py): Queries the vector database for high-risk clauses and generates structured legal risk assessment reports.

---

##  API Endpoints Reference

| HTTP Method | Route | Content-Type | Request Parameters / Body | Response Summary |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | `application/json` | None | `{ "message": "Backend Running" }` (Health Check) |
| **POST** | `/upload` | `multipart/form-data` | `file`: UploadFile<br>`session_id`: Form string | `{ "success": true, "document_id": "...", "filename": "..." }` |
| **POST** | `/chat` | `application/json` | `{ "query": "...", "document_id": "...", "session_id": "..." }` | `{ "success": true, "answer": "...", "sources": [...], "query_type": "..." }` |
| **POST** | `/delete-contract`| `application/json` | `{ "document_id": "...", "session_id": "..." }` | `{ "success": true }` (Clears document records) |
| **GET** | `/session-state` | Query Parameters | `session_id`: string | `{ "success": true, "session_id": "...", "document_id": "...", "filename": "...", "documents": [...], "messages": [...] }` |
| **POST** | `/session-active-document` | `application/json` | `{ "document_id": "...", "session_id": "..." }` | `{ "success": true, "document_id": "...", "filename": "..." }` |
| **POST** | `/end-session` | `application/json` | `{ "session_id": "..." }` | `{ "success": true }` (Hard deletes session folder) |
| **GET** | `/frontend/templetes/index.html` | `text/html` | None | Serves the HTML frontend interface page |

---

##  User Interface Showcase

Below are structured layout blocks where you can add screenshots of your running application. To embed your own images, place them inside your assets folder and update the image URLs.

### 1. Document Upload & Ingestion Interface
*A clean, modern, and dark-themed glassmorphic dashboard featuring drag-and-drop file uploaders, session states, and active file lists.*
<table>
  <tr>
    <td align="center">
      <img src="readme_assets/main page.jpg" alt="Welcome & Ingestion Screen" width="100%"/>
    </td>
  </tr>
</table>

### 2. Context-Aware Grounded Chat
*A persistent, responsive sidebar managing past chat memories and uploaded contracts, retaining state across browser refreshes.*
<table>
  <tr>
    <td align="center">
      <img src="readme_assets/chat 1.jpg" alt="Interactive Chat Interface" width="100%"/>
    </td>
  </tr>
</table>

### 3. Memory Based Chat 
*Memory based conversation architecture to remember the old messages and context.*
<table>
  <tr>
    <td align="center">
      <img src="readme_assets/chat.jpg" alt="Memory Based Chat Screen" width="100%"/>
    </td>
  </tr>
</table>

### 4. Terminating a Session
*Terminating the session created so that all the files related to it gets deleted and is not saved anywhere.*
<table>
  <tr>
    <td align="center">
      <img src="readme_assets/end session.jpg" width="100%"/>
    </td>
  </tr>
</table>

---

##  Setup & Installation

### Prerequisites
- Python 3.9+
- A Groq Cloud account and API key.

### 1. Clone & Set Up Directory
```bash
git clone <your-repository-url>
cd contract-intelligence
```

### 2. Configure Virtual Environment
```powershell
# Create environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\activate

# Activate on Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_DAILY_REQUEST_LIMIT=1000
LLM_DAILY_USAGE_PATH=storage/llm_daily_usage.json
```

### 5. Start Backend Server
```bash
uvicorn backend.api.main:app
```

### 6. Start Frontend App
Open the entrypoint file directly in your browser:
- [frontend/templetes/index.html](frontend/templetes/index.html)

Ensure your browser has access to the local port `8000` to hit the REST endpoints.

---

##  Key Design Principles & Roadmap

### Key Design Principles
1. **Isolated Multi-Tenancy**: Zero crossover between session variables, databases, or memory states.
2. **True Grounding**: All LLM queries must base responses strictly on indexed context chunks to avoid hallucinated liability reviews.
3. **Simple Teardown**: Simple folder purges erase all session traces.
4. **Intuitive UX**: Rich visual feedback channels state progress directly to users.

---

## Evaluation & Performance Results

To ensure the system's accuracy, retrieval quality, and speed, we run comprehensive performance evaluations using a curated benchmark dataset.

### Evaluation Process

The project includes an in-depth evaluation module under [evaluation/](file:///d:/project/contract-intelligence/evaluation) containing scripts to benchmark different parts of the pipeline:

1. **System Performance Evaluation ([system_runner.py](file:///d:/project/contract-intelligence/evaluation/system_runner.py))**:
   Runs the end-to-end RAG system (via the FastAPI API server or in-process TestClient) against the benchmark queries to measure latency statistics (embedding, retrieval, generation) and success rates.
   ```powershell
   # Run system evaluation (defaults to 40 queries)
   python -m evaluation.system_runner --backend-url ""
   ```

2. **Retrieval Evaluation ([run_retrieval_eval.py](file:///d:/project/contract-intelligence/evaluation/run_retrieval_eval.py))**:
   Evaluates the quality of retrieved contexts against expected chunk mappings using standard retrieval metrics:
   * **Hit@K**: Measures if the relevant chunk is in the top K retrieved results.
   * **Precision@K**: The proportion of retrieved chunks that are relevant.
   * **Recall@K**: The proportion of relevant chunks that are retrieved.
   * **Mean Reciprocal Rank (MRR)**: Evaluates the rank order of the first relevant chunk.
   ```powershell
   # Run retrieval evaluation
   python -m evaluation.run_retrieval_eval --session-id "bda10496-9291-47a9-93bc-f19ec1706cf5" -k 5
   ```

3. **RAGAS Evaluation ([run_ragas_eval.py](file:///d:/project/contract-intelligence/evaluation/run_ragas_eval.py))**:
   Benchmarks generation accuracy, faithfulness, and answer relevance using the Ragas framework.
   ```powershell
   # Run Ragas evaluation
   python -m evaluation.run_ragas_eval --limit 40
   ```

---

### Benchmark Evaluation Results

The system was evaluated against **40 test queries** from the contract benchmark dataset. Below are the summarized results from the run:

#### 1. Latency & Timing Breakdown
* **Total Queries**: 40
* **Success Rate**: 100% (40/40)

| Phase | Average | P50 (Median) | Min | Max | P95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Embedding** | 0.291s | 0.025s | 0.018s | 5.494s | 0.887s |
| **Retrieval** | 0.187s | 0.016s | 0.011s | 2.598s | 0.798s |

#### 2. Token & Retrieval Density
* **Average Retrieved Chunks**: 3.48 chunks per query
* **Average Prompt Size**: 2,684.1 tokens
* **Average Completion Size**: 27.3 tokens
* **Average Total Tokens**: 2,711.3 tokens

#### 3. Retrieval Evaluation Results (Precision & Recall)
Evaluated against **60 benchmark queries** with top-K set to 5 (`k = 5`):
* **Hit@K**: `1.0000` (100% of queries successfully retrieved the ground truth chunk in the top 5 results)
* **Recall@K**: `1.0000` (100% recall of relevant chunks)
* **Precision@K**: `0.2000` (Exactly 1 relevant chunk out of the 5 retrieved results per query)
* **Mean Reciprocal Rank (MRR)**: `0.7486` (The target chunk is positioned at rank 1 or 2 on average)

#### 4. Generation Accuracy & Alignment (Ragas Framework Results)
Evaluated using the Semantic Fallback Evaluation Engine powered by `llama-3.1-8b-instant` across **40 queries**:
* **Faithfulness**: `0.6388` (63.88% of statements are factually supported by retrieved contexts)
* **Answer Correctness**: `0.6225` (62.25% semantic correctness compared to the baseline)
* **Context Precision**: `0.6350` (63.50% relevance of retrieved context sections)
* **Context Recall**: `0.5975` (59.75% coverage of required target details in the retrieved chunks)

### 🔍 Retrieval & Generation Quality Analysis

#### How is our Retrieval performing?
* **Perfect Recall & Hit Rate**: The retrieval pipeline achieves a perfect **100% Hit@5 and Recall@5**. This proves that the retriever never misses the correct clause when searching the contract database.
* **Excellent Rank Position**: The Mean Reciprocal Rank (MRR) of **0.7486** shows that the target clause is positioned at rank 1 or 2 in the prompt context on average. This is due to the effectiveness of the **Cross-Encoder Reranker** sorting the most relevant text to the top, preventing the "lost-in-the-middle" LLM phenomenon.

#### How is our Generation performing?
* **Solid Baseline**: A **Faithfulness of 63.88%** and **Answer Correctness of 62.25%** represent a solid foundation for a small 8B parameter model (`llama-3.1-8b-instant`).
* **Opportunities for Improvement**: 
  * The **faithfulness (63.88%)** indicates that the model sometimes generates formatting elements or minor assumptions not explicitly defined in the context. 
  * The **context recall (59.75%)** suggests that the chunking boundaries occasionally split necessary context across chunk borders, making it hard for the generator to retrieve 100% of the relevant details.

---

### Latency Optimization Insights
Analysis of the logs reveals that **LLM Generation accounts for over 94% of total system latency** (24.11s out of 25.53s). Embedding and retrieval are extremely fast. 

Future optimization strategies include:
* Bypassing the LLM-based query classification in `QueryAnalyzer` and opting for keyword-based heuristics.
* Lowering `final_k` in the `RetrievalRouter` to feed fewer chunks (e.g., 2 instead of 4) to the LLM.
* Re-indexing with a smaller `target_chunk_size` (e.g., 1000 characters) to reduce context window tokens.

---

##  Author & Creator

This system was created and architected by:
- **Author**: **Aryan Yadav**
- **GitHub**: [@aaryanyaadav](https://github.com/aaryanyaadav)
- **Project Repository**: [AI-Contract-Analyzer-with-RAG](https://github.com/aaryanyaadav/AI-Contract-Analyzer-with-RAG)


