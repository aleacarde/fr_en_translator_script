import argparse
import logging
import re


import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
import xml.etree.ElementTree as ET

def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def extract_text_from_epub(epub_path: str) -> list:
    """
    Extracts and returns the plain text from the given EPUB file.
    """
    book = epub.read_epub(epub_path, options={"ignore_ncx": True})
    docs = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)

    text = []
    for item in docs:
        soup = BeautifulSoup(item.get_body_content(), "html.parser")
        # Join all <p> paragraphs; adjust if you want headings, lists, etc.
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        text.append("\n\n".join(paragraphs))
    return text

def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Dump the textual content of an EPUB file into a text file.")
    parser.add_argument("input_epub_file", type=str, help="Path to the EPUB file.")
    parser.add_argument("output_txt_file", type=str, help="Path to save the output text file.")
    args = parser.parse_args()

    logging.info("Starting EPUB text extraction...")
    
    epub_path = args.input_epub_file
    extracted_text = extract_text_from_epub(epub_path)

    with open(args.output_txt_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(extracted_text))
    
    logging.info(f"EPUB extraction complete. The plain text has been saved as '{args.output_txt_file}'.")

if __name__ == "__main__":
    main()
