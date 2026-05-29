import re

from docling_core.types.doc import (
    TextItem,
    TableItem
)


class DocumentNormalizer:

    # =====================================
    # ITERATOR WRAPPER
    # =====================================
    def _iter_document_items(

        self,

        document
    ):

        # =================================
        # CASE 1 — DOC OBJECT
        # =================================
        if hasattr(document, "iterate_items"):

            yield from document.iterate_items()

            return

        # =================================
        # CASE 2 — LIST OUTPUT
        # =================================
        if isinstance(document, list):

            for item in document:

                # Already normalized block
                if isinstance(item, dict):

                    yield item, 0

                # Tuple format
                elif (
                    isinstance(item, tuple)
                    and len(item) == 2
                ):

                    yield item

                # Nested doc objects
                elif hasattr(item, "iterate_items"):

                    yield from item.iterate_items()

            return

    # =====================================
    # NORMALIZATION
    # =====================================
    def normalize_document(

        self,

        document
    ):

        # =================================
        # FAST PATH
        # Already normalized
        # =================================
        if (

            isinstance(document, list)

            and

            len(document) > 0

            and

            isinstance(document[0], dict)

            and

            "text" in document[0]
        ):

            return document

        normalized_blocks = []

        in_toc = False

        # =================================
        # ITERATE ITEMS
        # =================================
        for item, level in (
            self._iter_document_items(
                document
            )
        ):

            # =================================
            # DICT FORMAT
            # =================================
            if isinstance(item, dict):

                normalized_blocks.append(item)

                continue

            label = getattr(

                item,

                "label",

                "unknown"
            )

            # =================================
            # PAGE NUMBER
            # =================================
            if getattr(item, "prov", None):

                page_num = (
                    item.prov[0].page_no
                )

            else:

                page_num = 1

            # =================================
            # REMOVE HEADERS/FOOTERS
            # =================================
            if label in [

                "page_header",

                "page_footer",

                "page_number"
            ]:

                continue

            # =================================
            # TOC DETECTION
            # =================================
            if isinstance(item, TextItem):

                text_content = (
                    item.text
                    .strip()
                    .lower()
                )

                # TOC START
                if (

                    label in [

                        "title",

                        "section_header"
                    ]

                    and

                    "table of contents"
                    in text_content
                ):

                    in_toc = True

                    continue

                # TOC END
                if (

                    in_toc

                    and

                    label in [

                        "title",

                        "section_header"
                    ]

                    and

                    level == 1
                ):

                    in_toc = False

            # =================================
            # SKIP TOC CONTENT
            # =================================
            if in_toc:

                continue

            # =================================
            # BLOCK STRUCTURE
            # =================================
            block_data = {

                "label": label,

                "page": page_num,

                "depth_level": level,

                "confidence": getattr(

                    item,

                    "confidence",

                    1.0
                )
            }

            # =================================
            # TEXT ITEMS
            # =================================
            if isinstance(item, TextItem):

                cleaned_text = (
                    self.clean_text(
                        item.text
                    )
                )

                if not cleaned_text:

                    continue

                block_data["text"] = (
                    cleaned_text
                )

                block_data["is_table"] = False

            # =================================
            # TABLE ITEMS
            # =================================
            elif isinstance(item, TableItem):

                try:

                    block_data["text"] = (
                        item.export_to_html()
                    )

                except Exception:

                    block_data["text"] = (
                        str(item)
                    )

                block_data["is_table"] = True

            else:

                continue

            normalized_blocks.append(
                block_data
            )

        return normalized_blocks

    # =====================================
    # TEXT CLEANING
    # =====================================
    def clean_text(

        self,

        text
    ):

        if not text:

            return ""

        # Collapse spaces
        text = re.sub(

            r"[^\S\n\r]+",

            " ",

            text
        )

        # Remove repeated blank lines
        text = re.sub(

            r"\n{3,}",

            "\n\n",

            text
        )

        return text.strip()