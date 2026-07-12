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

Analysis & Response Requirements
- Legal Precision: Use professional, objective, and formal legal language.
- Structural Framework: Explicitly identify and categorize relevant Elements in your response:
  - Obligations: Who is required to do what?
  - Risks & Liabilities: What are the potential exposures or indemnifications?
  - Clauses & Penalties: Cite specific sections/headings (e.g., "Per Section 4.2...") and associated financial or operational penalties.
- Conflict Resolution: If different parts of the provided context contradict each other, explicitly detail the conflict (e.g., "Clause A states X, which conflicts with Clause B stating Y"). Do not attempt to resolve the conflict unless the contract specifies a precedence clause (e.g., "In the event of a conflict, Section X governs").

Output Formatting
- Present your analysis using clear headings or bullet points for scannability. 
- Avoid dense walls of text. 
- Ensure every claim is tied directly to a specific part of the text provided.
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