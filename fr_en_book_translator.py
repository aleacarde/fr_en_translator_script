import argparse
import re
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import torch
from transformers import MarianMTModel, MarianTokenizer

# Set device to GPU if available (e.g., Nvidia GTX 3070)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the MarianMT model and tokenizer for French-to-English translation.
MODEL_NAME = "Helsinki-NLP/opus-mt-fr-en"
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
model = MarianMTModel.from_pretrained(MODEL_NAME).to(device)

def split_text_into_chunks(text, max_chars=500):
    """
    Splits the input text into chunks with a maximum of `max_chars` characters.
    This is a simple segmentation to avoid exceeding model token limits.
    """
    # Split by newlines and then join segments until max_chars is reached.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def translate_text(text):
    """
    Translates a given French text into English using the MarianMT model.
    Splits text into chunks to avoid long sequence issues.
    """
    chunks = split_text_into_chunks(text, max_chars=500)
    translated_chunks = []
    for chunk in chunks:
        # Tokenize and generate translation
        batch = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True).to(device)
        translated = model.generate(**batch)
        translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        translated_chunks.append(translated_text)
    return " ".join(translated_chunks)

def translate_soup(soup):
    """
    Recursively translates NavigableString objects in the BeautifulSoup parse tree,
    preserving the HTML structure.
    """
    for element in soup.find_all(text=True):
        # Skip text that is only whitespace.
        if element.strip():
            # Translate the text and replace it in the tree.
            translated = translate_text(element)
            element.replace_with(NavigableString(translated))
    return soup

def process_epub(input_path, output_path):
    """
    Processes the input EPUB: translates its content and writes out a new EPUB.
    """
    book = epub.read_epub(input_path)

    # Iterate over all document items (HTML content)
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            content = item.get_content()
            soup = BeautifulSoup(content, "html.parser")
            # Translate text within the HTML content
            soup = translate_soup(soup)
            # Update the content of the item with the translated HTML.
            item.set_content(soup.prettify("utf-8"))
    
    # Write the new EPUB file.
    epub.write_epub(output_path, book)
    print(f"Translation complete. English EPUB saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Translate a French EPUB novel into English.")
    parser.add_argument("--input", required=True, help="Path to the input French EPUB file.")
    parser.add_argument("--output", required=True, help="Path for the output English EPUB file.")
    args = parser.parse_args()

    process_epub(args.input, args.output)

if __name__ == "__main__":
    main()
