import os
from ingestion.docling_parser import (
    DoclingParser
)
from ingestion.fast_pdf_parser import (
    FastPDFParser
)
class DocumentRouter:
    def __init__(self):
        self.docling_parser = (
            DoclingParser()
        )
        self.fast_pdf_parser = (
            FastPDFParser()
        )
    # router
    def route_document(
        self,
        file_path
    ):
        extension = os.path.splitext(
            file_path
        )[1].lower()
        # pdf routing
        if extension == ".pdf":
            has_text = (
                self.fast_pdf_parser
                .has_extractable_text(
                    file_path
                )
            )
            # text pdf
            if has_text:
                print(
                    "Routing PDF to "
                    "Fast Text Parser..."
                )
                return (
                    self.fast_pdf_parser
                    .parse(file_path)
                )
            # Scaned pdf
            else:
                print(
                    "Routing PDF to "
                    "Heavy OCR Pipeline..."
                )
                return (
                    self.docling_parser
                    .parse_complex_document(
                        file_path
                    )
                )
        # Image files
        elif extension in [
            ".png",
            ".jpg",
            ".jpeg"
        ]:
            print(
                f"Routing {extension} "
                f"to OCR/Vision Pipeline..."
            )
            return (
                self.docling_parser
                .parse_complex_document(
                    file_path
                )
            )
        # text files 
        elif extension in [
            ".docx",
            ".txt",
            ".md"
        ]:
            print(
                f"Routing {extension} "
                f"to Lightweight Text Pipeline..."
            )
            return (
                self.docling_parser
                .parse_simple_document(
                    file_path
                )
            )
        # unsupported format
        else:
            raise TypeError(
                "DocumentRouter blocked "
                f"unsupported file type: "
                f"{extension}"
            )