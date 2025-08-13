# Path: /astoria_rag_hub/app/rag_components/data_loader.py
# Filename: data_loader.py

import os
import logging
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredRTFLoader,
    TextLoader,
    BSHTMLLoader,
)

logger = logging.getLogger(__name__)

def load_documents_from_directory(directory_path: str):
    """
    Loads all supported documents (PDF, RTF, TXT, HTML) from a directory.
    
    Args:
        directory_path (str): The path to the directory containing the documents.
        
    Returns:
        list: A list of LangChain Document objects.
    """
    logger.info(f"Scanning for documents in directory: {directory_path}")
    all_documents = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Skip directories, process files
        if os.path.isfile(file_path):
            try:
                if filename.lower().endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    logger.info(f"Loading PDF: {filename}")
                elif filename.lower().endswith(".rtf"):
                    loader = UnstructuredRTFLoader(file_path)
                    logger.info(f"Loading RTF: {filename}")
                elif filename.lower().endswith(".txt"):
                    loader = TextLoader(file_path)
                    logger.info(f"Loading TXT: {filename}")
                elif filename.lower().endswith((".html", ".htm")):
                    loader = BSHTMLLoader(file_path)
                    logger.info(f"Loading HTML: {filename}")
                else:
                    logger.warning(f"Skipping unsupported file type: {filename}")
                    continue
                
                # Load the documents and add them to our list
                documents = loader.load()
                all_documents.extend(documents)

            except Exception as e:
                logger.error(f"Failed to load or process {filename}: {e}", exc_info=True)

    logger.info(f"Successfully loaded {len(all_documents)} documents from the directory.")
    return all_documents

#end-of-file
