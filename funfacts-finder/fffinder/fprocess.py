import os
from typing import List
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from collections import Counter, defaultdict
import numpy as np
import networkx as nx


def parse_factslides_html(html_content: str) -> List[str]:
    """
    Parses the HTML content from a FACTSlides page to extract the text from each slide.

    This function finds the main container of the slides, iterates through each
    list item representing a slide, removes the unwanted HTML formatting and
    tool sections (like 'SOURCE' and 'SHARE'), and returns the clean text.

    Args:
        html_content: A string containing the raw HTML of the page.

    Returns:
        A list of strings, where each string is the text content of a single slide.
        Returns an empty list if the slide container isn't found.
    """
    # Initialize BeautifulSoup with the HTML content and the standard html.parser
    soup = BeautifulSoup(html_content, 'html.parser')

    # The slides are located within an ordered list with the id 'itemsContainer'
    slides_container = soup.find('ol', id='itemsContainer')

    # If the container is not found, return an empty list
    if not slides_container:
        return []

    slide_texts = []
    # Find all the <li> elements within the container, as each one holds a slide
    list_items = slides_container.find_all('li')

    for item in list_items:
        # Before extracting text, find and remove the 'factTools' div,
        # which contains the "SOURCE" and "SHARE" links.

        fact_tools = item.find('div', class_='factTools')
        if fact_tools:
            fact_tools.decompose() # .decompose() removes the tag from the tree

        # Get the remaining text from the slide.
        # The 'strip=True' argument removes leading/trailing whitespace.
        # The 'separator=" "' ensures that text from different tags is joined with a space.
        text = item.get_text(separator=' ', strip=True)

        # Add the cleaned text to our list, ensuring it's not an empty string
        if text:
            slide_texts.append(text)

    return slide_texts


def dedupe_and_save_to_json(base_dir: str, output_file: str = 'facts.json', similarity_threshold: int = 90) -> None:
    """
    Collects all parsed facts from HTML files in the given directory, deduplicates them using n-gram cosine similarity,
    and saves the unique facts to a JSON file as an array.

    Args:
        base_dir: The directory containing the raw HTML files.
        output_file: The path to the output JSON file (default: 'facts.json').
        similarity_threshold: The similarity threshold above which facts are considered duplicates (default: 90).
    """
    all_facts = []
    for filename in tqdm(os.listdir(base_dir), desc="Parsing files"):
        filepath = os.path.join(base_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as file:
                html_content = file.read()
            facts = parse_factslides_html(html_content)
            all_facts.extend(facts)

    # Deduplicate using character n-gram cosine similarity
    if not all_facts:
        unique_facts = []
    else:
        ngram_size = 2
        cos_threshold = similarity_threshold / 100.0
        fact_lowers = [fact.lower() for fact in all_facts]
        # Collect all unique n-grams
        all_ngrams = set()
        for text in fact_lowers:
            if len(text) >= ngram_size:
                for i in range(len(text) - ngram_size + 1):
                    all_ngrams.add(text[i:i + ngram_size])
        ngram_list = list(all_ngrams)
        ngram_to_id = {ng: idx for idx, ng in enumerate(ngram_list)}
        num_features = len(ngram_list)
        num_facts = len(all_facts)
        vectors = np.zeros((num_facts, num_features), dtype=np.float32)
        for j in tqdm(range(num_facts), desc="Vectorizing facts"):
            text = fact_lowers[j]
            if len(text) < ngram_size:
                continue
            counts = Counter(text[i:i + ngram_size] for i in range(len(text) - ngram_size + 1))
            row_sum = sum(counts.values())
            if row_sum == 0:
                continue
            for ng, count in counts.items():
                idx = ngram_to_id[ng]
                vectors[j, idx] = count / row_sum  # TF

        # IDF
        df = np.sum(vectors > 0, axis=0)
        idf = np.log((num_facts + 1) / (df + 1)) + 1
        vectors *= idf

        # L2 normalize for cosine
        norms = np.linalg.norm(vectors, axis=1)
        norms[norms == 0] = 1
        vectors /= norms[:, np.newaxis]

        # Compute similarity matrix
        sim = np.dot(vectors, vectors.T)

        # Build graph for connected components
        G = nx.Graph()
        G.add_nodes_from(range(num_facts))
        # Add edges where sim > threshold and i < j
        triu_i, triu_j = np.triu_indices(num_facts, k=1)
        mask = sim[triu_i, triu_j] > cos_threshold
        edges = zip(triu_i[mask], triu_j[mask])
        G.add_edges_from(tqdm(edges, desc="Adding edges", total=len(mask[mask])))

        # Get connected components
        components = list(nx.connected_components(G))

        # Select one fact per component (the one with smallest index)
        unique_indices = [min(comp) for comp in tqdm(components, desc="Selecting uniques")]

        # Sort indices to preserve original order as much as possible
        unique_indices.sort()
        unique_facts = [all_facts[i] for i in unique_indices]

    # Save to JSON as an array
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(unique_facts, json_file, indent=4)


if __name__ == "__main__":
    BASE_DIR = "raw_dataset"
    # Deduplicate and save all facts to JSON
    dedupe_and_save_to_json(BASE_DIR)
