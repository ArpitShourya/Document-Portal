# tests/test_unit_cases.py

import pytest
from fastapi.testclient import TestClient
from api.main import app   # or your FastAPI entrypoint
from pathlib import Path
from io import BytesIO
from src.document_ingestion.data_ingestion import FaissManager, ChatIngestor, DocHandler, DocumentComparator, DocumentPortalException
from langchain.schema import Document

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Document Portal" in response.text



@pytest.fixture
def sample_doc():
    """
    Provides a sample `Document` object for testing.
    
    Content: "Hello world"
    Metadata: {"source": "test.pdf", "row_id": "1"}
    
    This fixture is reused in tests that require a valid Document instance
    without repeatedly creating it inside each test.
    """
    return Document(page_content="Hello world", metadata={"source": "test.pdf", "row_id": "1"})

def test_faissmanager_fingerprint(sample_doc):
    """
    Test FaissManager._fingerprint:
    
    - Generates a unique fingerprint string for a document 
      based on its content and metadata.
    - Here we check that the fingerprint contains the document's source 
      (`test.pdf`), ensuring metadata is part of the key.
    """
    key = FaissManager._fingerprint(sample_doc.page_content, sample_doc.metadata)
    assert "test.pdf" in key

def test_doc_handler_save_pdf(tmp_path):
    """
    Test DocHandler.save_pdf with a valid PDF:
    
    - Creates a fake PDF file in memory.
    - Passes it to `save_pdf`, which should write it to disk.
    - Asserts that the saved file path actually exists in the temporary directory.
    """
    handler = DocHandler(data_dir=tmp_path)
    fake_pdf = BytesIO(b"%PDF-1.4 fake pdf content")
    fake_pdf.name = "test.pdf"
    save_path = handler.save_pdf(fake_pdf)
    assert Path(save_path).exists()

def test_doc_handler_save_non_pdf(tmp_path):
    """
    Test DocHandler.save_pdf with a non-PDF file:
    
    - Creates a fake text file with `.txt` extension.
    - Attempts to save it using `save_pdf`.
    - Expects a `DocumentPortalException` because only `.pdf` is allowed.
    - Also verifies that the exception message mentions "Invalid file type".
    """
    handler = DocHandler(data_dir=tmp_path)
    fake_file = BytesIO(b"not a pdf")
    fake_file.name = "test.txt"
    with pytest.raises(DocumentPortalException) as exc:
        handler.save_pdf(fake_file)

    # Optional: check the error message
    assert "Invalid file type" in str(exc.value)


def test_doc_handler_read_pdf(tmp_path):
    """
    Test DocHandler.read_pdf with a fake/corrupted PDF:
    
    - Writes invalid PDF bytes to a temporary file.
    - Calls `read_pdf` on it.
    - Expects a `DocumentPortalException` since the PDF is not valid.
    
    (Note: for more realistic tests, a tiny valid PDF should be used instead.)
    """
    handler = DocHandler(data_dir=tmp_path)
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf")  # ideally use a real tiny PDF
    with pytest.raises(DocumentPortalException):
        handler.read_pdf(str(pdf_path))

def test_document_comparator_save_and_read(tmp_path):
    """
    Test DocumentComparator.save_uploaded_files:
    
    - Creates two fake PDFs: `ref.pdf` (reference) and `act.pdf` (actual).
    - Saves them using the comparator's helper function.
    - Asserts that both saved file paths exist on disk.
    
    This ensures that file-saving logic works correctly for comparison tasks.
    """
    comp = DocumentComparator(base_dir=tmp_path)
    fake_pdf = BytesIO(b"%PDF-1.4 fake pdf")
    fake_pdf.name = "ref.pdf"
    act_pdf = BytesIO(b"%PDF-1.4 fake pdf")
    act_pdf.name = "act.pdf"
    ref_path, act_path = comp.save_uploaded_files(fake_pdf, act_pdf)
    assert ref_path.exists() and act_path.exists()
