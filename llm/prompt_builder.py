class PromptBuilder:

    def build_prompt(

        self,

        query,

        retrieved_chunks,

        conversation_history=None
    ):

        # Converstional memory

        history_text = ""

        if conversation_history:

            for msg in conversation_history:

                role = msg.get(
                    "role",
                    "user"
                )

                content = msg.get(
                    "content",
                    ""
                )

                history_text += (
                    f"{role.upper()}: "
                    f"{content}\n"
                )

        # Retrieved context

        context_blocks = []

        for idx, chunk in enumerate(
            retrieved_chunks,
            start=1
        ):

            text = chunk.get(
                "text",
                ""
            )

            metadata = chunk.get(
                "metadata",
                {}
            )

            section = metadata.get(
                "parent_section",
                "Unknown Section"
            )

            risk_level = metadata.get(
                "risk_level",
                "Unknown"
            )

            block = f"""
[Chunk {idx}]
Section:
{section}

Risk Level:
{risk_level}

Content:
{text}
"""

            context_blocks.append(block)

        context_text = "\n\n".join(
            context_blocks
        )

        # System prompt

        system_prompt = """
Role & Objective
You are an expert, highly precise legal contract AI assistant. Your sole task is to analyze the provided contract context and answer the user's query with absolute factual accuracy.

Strict Constraints (Anti-Hallucination Guardrails)
1. Context Bound: Rely ONLY on the explicitly provided contract context. Do not use external legal knowledge, case law, or assumptions.
2. Missing Information: If the context does not explicitly contain the answer, you must state exactly: "The contract does not contain enough information to answer this question." Do not extrapolate.
3. No Assumptions: If a term or condition is ambiguous or undefined in the text, highlight the ambiguity rather than interpreting it.

Response Requirements
- Direct and Plain Text: Provide ONLY the direct, plain text answer to the user's question. Get straight to the point.
- NO Formatting Symbols: Do NOT use markdown symbols (such as bolding `**`, headers, or bullet points) in your response. Output a clean, normal plain text response.
- NO Inline Citations/References: Do NOT write inline citations or document references (like "Per Section 9.1" or "according to chunk 2"). The user interface automatically displays the source documents below your answer, so your text should contain ONLY the direct plain answer.
- NO Boilerplate/Section Headers: Do NOT output sections like "Obligations:", "Risks & Liabilities:", "Answer:", or "Additional Information:". Answer the question naturally in one or two direct sentences.
- Pattern Override: Ignore any formatting, bullet styles, or section structures used in previous assistant responses in the CONVERSATION HISTORY. Do NOT copy the format of previous messages.
"""

        # User prompt

        user_prompt = f"""
==============================
CONVERSATION HISTORY
==============================

{history_text}

==============================
CONTRACT CONTEXT
==============================

{context_text}

==============================
USER QUESTION
==============================

{query}

==============================
ANSWER
==============================
"""

        return {

            "system_prompt":
            system_prompt,

            "user_prompt":
            user_prompt
        }