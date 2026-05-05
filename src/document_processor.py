"""
document_processor.py

Handles ingestion and preprocessing of raw documents into structured data.
Responsibilities:
  - Load files from disk (Markdown, PDF, plain text)
  - Clean and normalize text
  - Split content into chunks suitable for embedding
  - Extract metadata (title, date, tags)
"""

import os


def load_document(file_path: str) -> str:
    """Load raw text from a file on disk."""
    pass


def clean_text(text: str) -> str:
    """Strip noise, normalize whitespace, and standardize encoding."""
    pass


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    pass


def extract_metadata(file_path: str) -> dict:
    """Parse frontmatter or filename conventions to extract document metadata."""
    pass


def process_document(file_path: str) -> list[dict]:
    """Full pipeline: load → clean → chunk → attach metadata. Returns a list of chunk dicts."""
    pass


class MarkdownProcessor:
    """Loads and processes all Markdown files in a given directory."""

    def __init__(self, directory: str):
        if not os.path.exists(directory):
            raise FileNotFoundError(
                f"Knowledge base directory not found: '{directory}'\n"
                "  Fix: check the --kb path or create the directory and add .md files."
            )
        if not os.path.isdir(directory):
            raise NotADirectoryError(
                f"'{directory}' is a file, not a directory.\n"
                "  Fix: pass the folder path, e.g. 'knowledge_base/primary/'"
            )
        self.directory = directory
        self.files: list[dict] = []
        self.skipped: list[str] = []

    def process_all(self) -> list[dict]:
        """
        Walk the directory, read every .md file, and return a list of {filename, content} dicts.
        Files that are empty or unreadable are skipped with a warning rather than crashing.
        """
        self.files = []
        self.skipped = []
        md_files_found = False

        for root, _, filenames in os.walk(self.directory):
            for name in sorted(filenames):
                if not name.endswith(".md"):
                    continue
                md_files_found = True
                path = os.path.join(root, name)

                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                except PermissionError:
                    print(f"  Warning: no read permission for '{name}' — skipping.")
                    self.skipped.append(name)
                    continue
                except UnicodeDecodeError:
                    print(f"  Warning: '{name}' is not valid UTF-8 — skipping.")
                    self.skipped.append(name)
                    continue
                except OSError as e:
                    print(f"  Warning: could not read '{name}' ({e}) — skipping.")
                    self.skipped.append(name)
                    continue

                if not content.strip():
                    print(f"  Warning: '{name}' is empty — skipping.")
                    self.skipped.append(name)
                    continue

                self.files.append({"filename": name, "path": path, "content": content})

        if not md_files_found:
            raise FileNotFoundError(
                f"No .md files found in '{self.directory}'.\n"
                "  Fix: add Markdown files to the knowledge base directory before running."
            )
        if not self.files:
            raise ValueError(
                f"Found .md files in '{self.directory}' but all were empty or unreadable.\n"
                "  Fix: add content to the knowledge base files."
            )

        return self.files
