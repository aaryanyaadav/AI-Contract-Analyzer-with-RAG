class ContextBuilder:

    def build_context(
        self,
        retrieved_chunks
    ):

        context_parts = []

        for idx, chunk in enumerate(retrieved_chunks):

            section = chunk["metadata"].get(
                "parent_section",
                "Unknown"
            )

            context_parts.append(
                f"""
[Section: {section}]

{chunk['text']}
"""
            )

        return "\n".join(context_parts)