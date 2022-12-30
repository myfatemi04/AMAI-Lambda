from io import StringIO, BytesIO
import requests

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

def pdftext_from_url(url: str):
    """Extract text from a PDF file at a URL."""
    response = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
    })
    response.raise_for_status()
    with BytesIO(response.content) as fh:
        return pdftext_from_fileobj(fh)

def pdftext_from_fileobj(in_file):
    output_string = StringIO()
    print("Creating PDFParser")
    parser = PDFParser(in_file)
    print("Creating PDFDocument")
    doc = PDFDocument(parser)
    print("Creating PDFResourceManager")
    rsrcmgr = PDFResourceManager()
    print("Creating TextConverter")
    device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
    print("Creating PDFPageInterpreter")
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    print("Processing pages")
    for page in PDFPage.create_pages(doc):
        print("Processing page...")
        interpreter.process_page(page)
    return output_string.getvalue()
