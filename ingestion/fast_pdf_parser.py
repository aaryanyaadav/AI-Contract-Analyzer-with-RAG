import fitz


class FastPDFParser:

    def parse(
        self,
        file_path
    ):

        doc = fitz.open(file_path)

        parsed_blocks = []

        for page_num, page in enumerate(doc):

            text = page.get_text()

            if text.strip():

                parsed_blocks.append({

                    "text": text,

                    "label": "paragraph",

                    "page": page_num + 1,

                    "confidence": 1.0
                })

        return parsed_blocks

    # Detecting pdf if has text

    def has_extractable_text(

        self,

        file_path
    ):

        try:

            doc = fitz.open(file_path)

            total_text = ""

            # Read first few pages only
            for page in doc[:3]:

                total_text += (
                    page.get_text()
                )

            return (
                len(total_text.strip())
                > 200
            )

        except Exception:

            return False