import os
from ingestion.docling_parser import DoclingParser

class DocumentRouter:

    def __init__(self):
        self.docling_parser = DoclingParser()

    def route_document(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        # Route 1: Local Machine Heavy Layout/OCR Parser (PDFs + Flat Images)
        if extension in [".pdf", ".png", ".jpg", ".jpeg"]:
            print(f"Routing {extension} to Local Heavy Vision/OCR Pipeline...")
            return self.docling_parser.parse_complex_document(file_path)

        # Route 2: Native/Digital Text Documents
        elif extension in [".docx", ".txt", ".md"]:
            print(f"Routing {extension} to Lightweight Text Pipeline...")
            return self.docling_parser.parse_simple_document(file_path)

        else:
            raise TypeError(f"DocumentRouter blocked unsupported file type: {extension}")