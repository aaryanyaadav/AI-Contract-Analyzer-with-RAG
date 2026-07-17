import uuid
import re
class ClauseChunker:
    def __init__(
        self,
        target_chunk_size=1800,
        overlap_size=300
    ):
        self.target_chunk_size = (
            target_chunk_size
        )
        self.overlap_size = (
            overlap_size
        )
        # legal section detection 
        self.section_pattern = re.compile(
            r'^('
            r'(SECTION|ARTICLE|CLAUSE)\s+\d+'
            r'|'
            r'\d+(\.\d+)*'
            r'|'
            r'[A-Z][A-Z\s]{5,}'
            r')',

            re.IGNORECASE
        )
    # main chunking
    def split_into_clauses(
        self,
        normalized_blocks
    ):
        chunks = []
        current_chunk = []
        current_length = 0
        current_section = "General"
        for block in normalized_blocks:
            text = block.get(
                "text",
                ""
            ).strip()
            if not text:
                continue

            label = block.get(
                "label",
                "paragraph"
            )
            is_table = (
                block.get(
                    "is_table",
                    False
                )
                or
                label == "table"
            )
            # section header detection  
            is_section_header = (
                label in [
                    "title",
                    "section_header"
                ]
                or
                self.section_pattern.match(
                    text
                )
            )
            # update active section
            if is_section_header:
                current_section = text[:150]
            text_length = len(text)
            should_split = (
                current_length + text_length
                > self.target_chunk_size
            )
            if should_split and current_chunk:
                packaged_chunk = (
                    self._package_chunk(
                        current_chunk,
                        current_section
                    )
                )
                chunks.append(
                    packaged_chunk
                )
                # overlap preservation
                overlap_text = (
                    packaged_chunk["text"][
                        -self.overlap_size:
                    ]
                )
                current_chunk = [{
                    "text": overlap_text,
                    "label": "overlap",
                    "is_table": False,
                    "confidence": 1.0
                }]
                current_length = len(
                    overlap_text
                )
            # append current block
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
        # final flush
        if current_chunk:
            chunks.append(
                self._package_chunk(
                    current_chunk,
                    current_section
                )
            )
        # Assign stable sequential chunk_index (0...N-1)
        for idx, chunk in enumerate(chunks):
            chunk["chunk_index"] = idx
        return chunks
    # package chunk
    def _package_chunk(
        self,
        elements,
        parent_section
    ):
        combined_text = "\n\n".join([
            el["text"]
            for el in elements
        ])

        avg_confidence = (
            sum([
                el["confidence"]
                for el in elements
            ]) / len(elements)
        )
        is_table = any([
            el["is_table"]
            for el in elements
        ])
        # Collect page numbers from all elements
        page_numbers = sorted(
            list(
                set(
                    el.get("page_number")
                    for el in elements
                    if el.get("page_number") is not None
                )
            )
        )
        return {
            # Unique identifier (will be overridden by sequential integer in split_into_clauses)
            "chunk_id": str(uuid.uuid4()),

            # Chunk content
            "text": combined_text,

            # Structure
            "parent_section": parent_section,
            "section_heading": parent_section,
            "page_numbers": page_numbers,
            "page_number": page_numbers[0] if page_numbers else None,

            # OCR / Parsing quality
            "average_confidence": round(avg_confidence, 3),
            "needs_review": avg_confidence < 0.80,

            # Content information
            "is_table": is_table,
            "chunk_length": len(combined_text)
        }