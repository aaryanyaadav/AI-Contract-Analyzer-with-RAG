from retrieval.mmr_retriver import (
    MMRRetriever
)

from orchestration.query_analyzer import (
    QueryAnalyzer
)

from orchestration.retrieval_router import (
    RetrievalRouter
)

from orchestration.response_validator import (
    ResponseValidator
)

from llm.prompt_builder import (
    PromptBuilder
)

from llm.llm_client import (
    LLMClient
)

from retrieval.reraanker import (
    Reranker
)


class RAGOrchestrator:

    def __init__(

        self,

        chroma_path
    ):


        self.retriever = MMRRetriever(
            chroma_path=chroma_path
        )

        self.query_analyzer = (
            QueryAnalyzer(
                llm_client=LLMClient()
            )
        )

        self.retrieval_router = (
            RetrievalRouter()
        )

        self.prompt_builder = (
            PromptBuilder()
        )

        self.response_validator = (
            ResponseValidator()
        )

        self.llm = LLMClient()

        self.reranker = Reranker()


    def chat(

        self,

        query,

        document_id,

        conversation_history=None
    ):

        if conversation_history is None:

            conversation_history = []

        # Initialize guardrails
        from orchestration.guardrails import GuardrailSystem
        guardrails = GuardrailSystem()

        # Check input safety & off-topic/injection attempts
        is_safe, refusal_reason = guardrails.check_input_safety(query)
        if not is_safe:
            return {
                "answer": refusal_reason or "I cannot answer this question as it is off-topic or contains sensitive content.",
                "sources": [],
                "query_type": "refused"
            }

        # Sanitize query PII (just in case)
        sanitized_query, _ = guardrails.sanitize_pii(query)

        query_type = (
            self.query_analyzer.analyze(
                sanitized_query
            )
        )

        retrieval_config = (
            self.retrieval_router
            .get_retrieval_config(
                query_type
            )
        )


        retrieved_chunks = (
            self.retriever.retrieve(

                query=sanitized_query,

                document_id=document_id,

                initial_fetch_k=
                retrieval_config[
                    "initial_fetch_k"
                ],

                final_k=
                retrieval_config[
                    "final_k"
                ]
            )
        )


        reranked_chunks = (
            self.reranker.rerank(

                query=sanitized_query,

                retrieved_chunks=
                retrieved_chunks
            )
        )


        prompts = (
            self.prompt_builder.build_prompt(

                query=sanitized_query,

                retrieved_chunks=
                reranked_chunks,

                conversation_history=
                conversation_history
            )
        )

        answer = self.llm.generate(

            system_prompt=
            prompts["system_prompt"],

            user_prompt=
            prompts["user_prompt"]
        )



        valid = self.response_validator.validate(

            answer=answer,

            retrieved_chunks=
            reranked_chunks
        )

        if not valid:
            print(f"[Validator] Warning: Response validation failed.")

        # PII Output Prevention
        sanitized_answer, _ = guardrails.sanitize_pii(answer)
        answer = sanitized_answer

        return {

            "answer":
             answer,

            "sources":
            reranked_chunks,

            "query_type":
            query_type
        }

    def close(self):

        if hasattr(self, 'retriever') and self.retriever:

            self.retriever.close()