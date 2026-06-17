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
You are an advanced legal contract AI assistant.

Your task is to answer questions ONLY using
the provided contract context.

STRICT RULES:
1. Never hallucinate information.
2. If information is missing, say:
   "The contract does not contain enough information."
3. Be concise but detailed.
4. Use professional legal language.
5. Reference obligations, risks,
   clauses, penalties, and liabilities clearly.
6. Do not make assumptions.
7. Focus ONLY on the uploaded contract.
8. If multiple clauses conflict,
   explain the conflict clearly.
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