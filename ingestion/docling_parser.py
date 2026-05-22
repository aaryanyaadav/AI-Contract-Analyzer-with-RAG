from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

class DoclingParser:
    def __init__(self):
        complex_options = PdfPipelineOptions()
        complex_options.do_ocr = True 
        complex_options.do_table_structure = False  
        
        self.complex_converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=complex_options)}
        )
        
        self.simple_converter = DocumentConverter()

    def parse_complex_document(self, file_path: str):
        """Runs the deep, local machine layout and OCR parsing pipeline."""
        print(f"[DoclingParser] Executing local complex AI/OCR parse on: {file_path}")
        result = self.complex_converter.convert(file_path)
        return result.pages_document if hasattr(result, "pages_document") else result.document

    def parse_simple_document(self, file_path: str):
        """Runs a lightweight native text extraction pipeline."""
        print(f"[DoclingParser] Executing simple fast-track parse on: {file_path}")
        result = self.simple_converter.convert(file_path)
        return result.document