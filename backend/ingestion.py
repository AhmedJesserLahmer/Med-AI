import csv
import os
from pathlib import Path
from typing import Callable, Dict, List

from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    BSHTMLLoader,
)

# Single source of truth for the embedding model name: used at ingestion time
# (backend/ingest.py) and at query time (backend/retrieval.py). Previously
# ingestion used BAAI/bge-small-en-v1.5 while the live query path used
# thenlper/gte-small -- both are 384-dim so nothing ever errored, but queries
# and documents lived in different embedding spaces, silently degrading
# retrieval quality.
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

MARKDOWN_SEPARATORS = [
    "\n#{1,6} ",
    "```\n",
    "\n\\*\\*\\*+\n",
    "\n---+\n",
    "\n___+\n",
    "\n\n",
    "\n",
    " ",
    "",
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    add_start_index=True,
    strip_whitespace=True,
    separators=MARKDOWN_SEPARATORS,
)


def load_text(path: str) -> List[LangchainDocument]:
    return TextLoader(path, encoding="utf-8").load()


def load_healthcare_csv(path: str) -> List[LangchainDocument]:
    """Loads the healthcare_rag_dataset.csv schema: builds page_content from
    the clinical text fields only (content_text, symptoms, treatments, risk_factors,
    prevention) and keeps the rest of the columns as metadata instead of dumping all
    23 columns into the embedded text (which would bury the signal in noise like
    word_count/reading_level_score and waste context tokens at generation time).
    """
    docs = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            content = "\n".join(
                filter(
                    None,
                    [
                        f"{row.get('title', '')} ({row.get('document_type', '')})",
                        row.get("content_text"),
                        f"Symptoms: {row['symptoms']}" if row.get("symptoms") else None,
                        f"Treatments: {row['treatments']}" if row.get("treatments") else None,
                        f"Risk factors: {row['risk_factors']}" if row.get("risk_factors") else None,
                        f"Prevention: {row['prevention']}" if row.get("prevention") else None,
                    ],
                )
            )
            metadata = {
                "source": path,
                "doc_id": row.get("doc_id"),
                "title": row.get("title"),
                "category": row.get("category"),
                "icd10_code": row.get("icd10_code"),
                "severity_level": row.get("severity_level"),
                "source_name": row.get("source_name"),
                "source_url": row.get("source_url"),
            }
            docs.append(LangchainDocument(page_content=content, metadata=metadata))
    return docs


EXTENSION_LOADERS: Dict[str, Callable[[str], List[LangchainDocument]]] = {
    ".txt": load_text,
    ".md": load_text,
    ".pdf": lambda path: PyPDFLoader(path).load(),
    ".docx": lambda path: Docx2txtLoader(path).load(),
    ".html": lambda path: BSHTMLLoader(path).load(),
    ".htm": lambda path: BSHTMLLoader(path).load(),
    ".csv": load_healthcare_csv,
}


def load_any_file(path: str) -> List[LangchainDocument]:
    ext = Path(path).suffix.lower()
    loader = EXTENSION_LOADERS.get(ext)
    if loader is None:
        print(f"Skipping unsupported file type: {path}")
        return []
    try:
        return loader(path)
    except Exception as exc:
        print(f"Failed to load {path}: {exc}")
        return []


def load_directory(folder: str) -> List[LangchainDocument]:
    all_docs: List[LangchainDocument] = []
    for root, _, files in sorted(os.walk(folder)):
        for fname in sorted(files):
            all_docs.extend(load_any_file(os.path.join(root, fname)))
    return all_docs


def load_and_chunk(folder: str) -> List[LangchainDocument]:
    """Loads every supported file under `folder` and splits into chunks, in a
    stable, deterministic order -- the resulting list index is used as the
    chunk id (`vec{i}`) by both the ingestion script and the in-memory BM25
    corpus built at query time, so they must line up exactly.
    """
    raw_documents = load_directory(folder)
    return text_splitter.split_documents(raw_documents)
