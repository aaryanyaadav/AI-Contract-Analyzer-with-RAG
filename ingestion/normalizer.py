import re
from docling_core.types.doc import TextItem, TableItem

class DocumentNormalizer:

    def normalize_document(self, document):
        normalized_blocks = []
        in_toc = False # Flag to track if we are inside the Table of Contents

        for item, level in document.iterate_items():
            label = getattr(item, "label", "unknown")
            page_num = getattr(item.prov[0], "page_no", 1) if getattr(item, "prov", None) else 1

            # --- IMPROVEMENT 1: HEADER & FOOTER ERADICATION ---
            if label in ["page_header", "page_footer", "page_number"]:
                continue

            # --- IMPROVEMENT 2: THE TOC TRAP ---
            if isinstance(item, TextItem):
                text_content = item.text.strip().lower()
                
                # Detect the start of the TOC
                if label in ["title", "section_header"] and "table of contents" in text_content:
                    in_toc = True
                    continue
                
                # Detect the end of the TOC (usually the first major header after the TOC)
                # If we are in the TOC, and we hit a major header that ISN'T "table of contents", we are out.
                if in_toc and label in ["title", "section_header"] and level == 1:
                    in_toc = False
            
            # If we are currently inside the TOC, skip adding this item
            if in_toc:
                continue

            # --- CORE EXTRACTION ---
            block_data = {
                "label": label,
                "page": page_num,
                "depth_level": level,
                # Grab the OCR confidence if Docling/RapidOCR provided it
                "confidence": getattr(item, "confidence", 1.0) 
            }

            if isinstance(item, TextItem):
                cleaned_text = self.clean_text(item.text)
                if not cleaned_text:
                    continue
                block_data["text"] = cleaned_text
                
            elif isinstance(item, TableItem):
                # IMPROVEMENT 4: Docling's export_to_html natively handles cross-page tables
                # as long as the AI recognized them as a single continuous structure!
                block_data["text"] = item.export_to_html() 
            else:
                continue 

            normalized_blocks.append(block_data)

        return normalized_blocks

    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r"[^\S\n\r]+", " ", text)
        return text.strip()