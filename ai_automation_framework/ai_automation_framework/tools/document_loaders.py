"""Document loaders for various file formats."""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod


class BaseDocumentLoader(ABC):
    """Base class for document loaders."""

    def __init__(self, file_path: str):
        """
        Initialize the loader.

        Args:
            file_path: Path to the document
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """
        Load the document.

        Returns:
            List of document chunks with metadata
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get file metadata."""
        stat = self.file_path.stat()
        return {
            "source": str(self.file_path.absolute()),
            "filename": self.file_path.name,
            "size": stat.st_size,
            "extension": self.file_path.suffix,
        }


class TextLoader(BaseDocumentLoader):
    """Loader for plain text files."""

    def __init__(
        self,
        file_path: str,
        encoding: str = "utf-8",
        chunk_size: Optional[int] = None
    ):
        """
        Initialize text loader.

        Args:
            file_path: Path to text file
            encoding: File encoding
            chunk_size: Optional chunk size for splitting
        """
        super().__init__(file_path)
        self.encoding = encoding
        self.chunk_size = chunk_size

    def load(self) -> List[Dict[str, Any]]:
        """Load text file."""
        try:
            content = self.file_path.read_text(encoding=self.encoding)
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode file '{self.file_path}' with encoding '{self.encoding}': {e}"
            )
        except OSError as e:
            raise OSError(
                f"Failed to read file '{self.file_path}': {e}"
            )

        metadata = self.get_metadata()

        if self.chunk_size:
            # Split into chunks
            chunks = []
            for i in range(0, len(content), self.chunk_size):
                chunk = content[i:i + self.chunk_size]
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk": i // self.chunk_size,
                        "chunk_size": len(chunk)
                    }
                })
            return chunks
        else:
            return [{
                "content": content,
                "metadata": metadata
            }]


class PDFLoader(BaseDocumentLoader):
    """Loader for PDF files."""

    def __init__(self, file_path: str, extract_images: bool = False):
        """
        Initialize PDF loader.

        Args:
            file_path: Path to PDF file
            extract_images: Whether to extract images
        """
        super().__init__(file_path)
        self.extract_images = extract_images

    def load(self) -> List[Dict[str, Any]]:
        """Load PDF file."""
        try:
            import pypdf
        except ImportError:
            raise ImportError(
                "pypdf is required for PDF loading. "
                "Install it with: pip install pypdf"
            )

        documents = []
        metadata = self.get_metadata()

        try:
            with open(self.file_path, 'rb') as file:
                try:
                    pdf_reader = pypdf.PdfReader(file)
                except pypdf.errors.PdfReadError as e:
                    raise ValueError(
                        f"Failed to read PDF file '{self.file_path}': {e}"
                    )

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                    except Exception as e:
                        raise ValueError(
                            f"Failed to extract text from page {page_num + 1} "
                            f"in '{self.file_path}': {e}"
                        )

                    documents.append({
                        "content": text,
                        "metadata": {
                            **metadata,
                            "page": page_num + 1,
                            "total_pages": len(pdf_reader.pages)
                        }
                    })
        except OSError as e:
            raise OSError(
                f"Failed to open PDF file '{self.file_path}': {e}"
            )

        return documents


class DocxLoader(BaseDocumentLoader):
    """Loader for Word documents (.docx)."""

    def __init__(self, file_path: str):
        """
        Initialize DOCX loader.

        Args:
            file_path: Path to DOCX file
        """
        super().__init__(file_path)

    def load(self) -> List[Dict[str, Any]]:
        """Load DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX loading. "
                "Install it with: pip install python-docx"
            )

        try:
            doc = Document(self.file_path)
        except Exception as e:
            raise ValueError(
                f"Failed to open DOCX file '{self.file_path}': {e}"
            )

        paragraphs = []
        metadata = self.get_metadata()

        try:
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():  # Skip empty paragraphs
                    paragraphs.append({
                        "content": para.text,
                        "metadata": {
                            **metadata,
                            "paragraph": i + 1
                        }
                    })

            # Combine all paragraphs
            full_text = "\n\n".join(p["content"] for p in paragraphs)
        except Exception as e:
            raise ValueError(
                f"Failed to extract text from DOCX file '{self.file_path}': {e}"
            )

        return [{
            "content": full_text,
            "metadata": {
                **metadata,
                "paragraphs": len(paragraphs)
            }
        }]


class MarkdownLoader(BaseDocumentLoader):
    """Loader for Markdown files."""

    def __init__(self, file_path: str, split_by_headers: bool = False):
        """
        Initialize Markdown loader.

        Args:
            file_path: Path to Markdown file
            split_by_headers: Whether to split by headers
        """
        super().__init__(file_path)
        self.split_by_headers = split_by_headers

    def load(self) -> List[Dict[str, Any]]:
        """Load Markdown file."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode Markdown file '{self.file_path}' with UTF-8 encoding: {e}"
            )
        except OSError as e:
            raise OSError(
                f"Failed to read Markdown file '{self.file_path}': {e}"
            )

        metadata = self.get_metadata()

        if self.split_by_headers:
            # Simple splitting by headers
            sections = []
            current_section = []
            current_header = None

            for line in content.splitlines():
                if line.startswith("#"):
                    if current_section:
                        sections.append({
                            "content": "\n".join(current_section),
                            "metadata": {
                                **metadata,
                                "header": current_header,
                                "section": len(sections) + 1
                            }
                        })
                    current_header = line
                    current_section = [line]
                else:
                    current_section.append(line)

            # Add last section
            if current_section:
                sections.append({
                    "content": "\n".join(current_section),
                    "metadata": {
                        **metadata,
                        "header": current_header,
                        "section": len(sections) + 1
                    }
                })

            return sections
        else:
            return [{
                "content": content,
                "metadata": metadata
            }]


class DirectoryLoader:
    """Loader for entire directories."""

    def __init__(
        self,
        directory_path: str,
        glob_pattern: str = "**/*",
        exclude_patterns: Optional[List[str]] = None,
        loader_map: Optional[Dict[str, type]] = None
    ):
        """
        Initialize directory loader.

        Args:
            directory_path: Path to directory
            glob_pattern: Glob pattern for files
            exclude_patterns: Patterns to exclude
            loader_map: Mapping of file extensions to loaders
        """
        self.directory_path = Path(directory_path)
        if not self.directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        if not self.directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        self.glob_pattern = glob_pattern

        # Validate exclude_patterns to prevent path traversal
        self.exclude_patterns = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                # Check for path traversal attempts
                if ".." in pattern or pattern.startswith("/") or pattern.startswith("\\"):
                    raise ValueError(
                        f"Invalid exclude pattern '{pattern}': "
                        "Path traversal patterns are not allowed"
                    )
                self.exclude_patterns.append(pattern)

        self.loader_map = loader_map or {
            ".txt": TextLoader,
            ".md": MarkdownLoader,
            ".pdf": PDFLoader,
            ".docx": DocxLoader,
        }

    def load(self) -> List[Dict[str, Any]]:
        """Load all documents from directory."""
        documents = []
        errors = []

        for file_path in self.directory_path.glob(self.glob_pattern):
            if not file_path.is_file():
                continue

            # Check exclude patterns
            if any(pattern in str(file_path) for pattern in self.exclude_patterns):
                continue

            # Get appropriate loader
            loader_class = self.loader_map.get(file_path.suffix)
            if not loader_class:
                continue

            try:
                loader = loader_class(str(file_path))
                docs = loader.load()
                documents.extend(docs)
            except FileNotFoundError as e:
                error_msg = f"File not found while loading '{file_path}': {e}"
                errors.append(error_msg)
                print(error_msg)
            except ValueError as e:
                error_msg = f"Value error loading '{file_path}': {e}"
                errors.append(error_msg)
                print(error_msg)
            except OSError as e:
                error_msg = f"OS error loading '{file_path}': {e}"
                errors.append(error_msg)
                print(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error loading '{file_path}': {type(e).__name__}: {e}"
                errors.append(error_msg)
                print(error_msg)

        return documents


def load_document(file_path: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Automatically load a document based on its extension.

    Args:
        file_path: Path to the document
        **kwargs: Additional arguments for the loader

    Returns:
        List of document chunks with metadata

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file type is not supported
    """
    path = Path(file_path)

    # Validate file existence
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate it's a file, not a directory
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Validate and get file extension
    extension = path.suffix.lower()
    if not extension:
        raise ValueError(f"File has no extension: {file_path}")

    loader_map = {
        ".txt": TextLoader,
        ".md": MarkdownLoader,
        ".pdf": PDFLoader,
        ".docx": DocxLoader,
    }

    loader_class = loader_map.get(extension)
    if not loader_class:
        supported_types = ", ".join(loader_map.keys())
        raise ValueError(
            f"Unsupported file type '{extension}' for file '{file_path}'. "
            f"Supported types: {supported_types}"
        )

    loader = loader_class(file_path, **kwargs)
    return loader.load()
