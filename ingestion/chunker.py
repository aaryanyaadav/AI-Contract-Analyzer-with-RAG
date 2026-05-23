import uuid
import re


class ClauseChunker:

    def __init__(

        self,

        target_chunk_size=1800,
        overlap_size=300
    ):

        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

        # Detect legal section headers
        self.section_pattern = re.compile(
            r'^('
            r'(SECTION|ARTICLE)\s+\d+'
            r'|'
            r'\d+(\.\d+)*'
            r'|'
            r'[A-Z][A-Z\s]{5,}'
            r')',
            re.IGNORECASE
        )

    def split_into_clauses(
        self,
        normalized_blocks
    ):

        chunks = []

        current_chunk = []
        current_length = 0

        current_section = "General"

        for block in normalized_blocks:

            text = block.get("text", "").strip()

            if not text:
                continue

            label = block.get(
                "label",
                "paragraph"
            )

            is_table = (
                block.get("is_table", False)
                or label == "table"
            )

            # Detect section headers
            is_section_header = (
                label in ["title", "section_header"]
                or self.section_pattern.match(text)
            )

            # Update active section
            if is_section_header:
                current_section = text[:150]

            text_length = len(text)

            # Split ONLY if chunk becomes too large
            if (
                current_length + text_length
                > self.target_chunk_size
            ):

                packaged = self._package_chunk(
                    current_chunk,
                    current_section
                )

                chunks.append(packaged)

                # Overlap preservation
                overlap_text = packaged["text"][
                    -self.overlap_size:
                ]

                current_chunk = [{
                    "text": overlap_text,
                    "label": "overlap",
                    "is_table": False,
                    "confidence": 1.0
                }]

                current_length = len(overlap_text)

            current_chunk.append({

                "text": text,
                "label": label,
                "is_table": is_table,
                "confidence": block.get(
                    "confidence",
                    1.0
                )
            })

            current_length += text_length

        # Final flush
        if current_chunk:

            chunks.append(
                self._package_chunk(
                    current_chunk,
                    current_section
                )
            )

        return chunks

    def _package_chunk(

        self,
        elements,
        parent_section
    ):

        combined_text = "\n\n".join([
            el["text"]
            for el in elements
        ])

        avg_confidence = sum([
            el["confidence"]
            for el in elements
        ]) / len(elements)

        is_table = any([
            el["is_table"]
            for el in elements
        ])

        return {

            "chunk_id": str(uuid.uuid4()),

            "text": combined_text,

            "parent_section": parent_section,


            "needs_review": (
                avg_confidence < 0.80
            ),

            "is_table": is_table
        }