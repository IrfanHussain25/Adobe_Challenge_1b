import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter, defaultdict
from datetime import datetime, timezone

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import numpy as np

# --- CONFIGURATION ---
MODEL_NAME = 'all-MiniLM-L6-v2'

class PDFAnalyzer:
    """
    A truly generic PDF analyzer that uses a two-stage semantic ranking
    system to provide context-aware results for any persona or task.
    """
    def __init__(self):
        print("Loading sentence-transformer model...")
        self.model = SentenceTransformer(MODEL_NAME)
        # Define TOP_N_SECTIONS as an instance attribute
        self.TOP_N_SECTIONS = 5
        print("Model loaded.")

    def extract_page_chunks(self, pdf_path: Path) -> List[Dict]:
        """
        Extracts content page by page, identifying the most prominent line of text
        (based on font size) as the candidate title for each page.
        """
        chunks = []
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc, 1):
                full_text = page.get_text("text")
                if not full_text.strip():
                    continue

                blocks = page.get_text("dict", sort=True)['blocks']
                max_font_size = 0
                candidate_title = f"Content from page {page_num}"
                for block in blocks:
                    if 'lines' in block:
                        for line in block['lines']:
                            if 'spans' in line and line['spans']:
                                span = line['spans'][0]
                                line_text = " ".join([s['text'] for s in line['spans']]).strip()
                                # Heuristic for a title: larger font, contains letters, and is reasonably short.
                                if span['size'] > max_font_size and len(line_text) > 0 and re.search(r'[a-zA-Z]', line_text) and len(line_text.split()) < 25:
                                    max_font_size = span['size']
                                    candidate_title = line_text

                chunks.append({
                    "document": pdf_path.name,
                    "page_number": page_num,
                    "section_title": candidate_title,
                    "content": full_text
                })
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
        return chunks

    def analyze_and_rank(self, all_chunks: List[Dict], query: str) -> Dict:
        """
        Ranks chunks using a two-stage semantic analysis process.
        """
        if not all_chunks:
            return {"extracted_sections": [], "subsection_analysis": []}

        print("Starting two-stage semantic analysis...")
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # --- Stage 1: Rank Documents by Overall Relevance ---
        print("Stage 1: Ranking documents...")
        docs_content = defaultdict(str)
        for chunk in all_chunks:
            docs_content[chunk['document']] += chunk['content'] + "\n"

        doc_names = list(docs_content.keys())
        doc_embeddings = self.model.encode([docs_content[name] for name in doc_names], convert_to_tensor=True)
        doc_scores = util.cos_sim(query_embedding, doc_embeddings)[0].numpy()
        
        doc_relevance = {name: score for name, score in zip(doc_names, doc_scores)}
        print(f"Document relevance scores (sample): {list(doc_relevance.items())[:3]}")

        # --- Stage 2: Rank Individual Chunks with Document Bonus ---
        print("Stage 2: Ranking individual chunks with document relevance bonus...")
        for chunk in all_chunks:
            content_embedding = self.model.encode(chunk['content'], convert_to_tensor=True)
            content_score = util.cos_sim(query_embedding, content_embedding)[0].item()
            
            document_bonus = doc_relevance.get(chunk['document'], 0)
            chunk['score'] = content_score + document_bonus

        all_chunks.sort(key=lambda x: x['score'], reverse=True)

        # --- Format the top N results using the class attribute ---
        top_chunks = all_chunks[:self.TOP_N_SECTIONS]

        extracted_sections = [
            {
                "document": chunk['document'],
                "section_title": chunk['section_title'],
                "importance_rank": i + 1,
                "page_number": chunk['page_number']
            }
            for i, chunk in enumerate(top_chunks)
        ]

        # --- Generate intelligent summaries for the top results ---
        subsection_analysis = []
        for chunk in top_chunks:
            # Use the full content of the page for summarization
            content_for_summary = chunk['content']
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content_for_summary) if len(s.strip()) > 20]
            if not sentences:
                subsection_analysis.append({"document": chunk['document'], "refined_text": chunk['section_title'], "page_number": chunk['page_number']})
                continue
            
            sentence_embeddings = self.model.encode(sentences, convert_to_tensor=True)
            sentence_scores = util.cos_sim(query_embedding, sentence_embeddings)[0].numpy()
            
            top_indices = np.argsort(sentence_scores)[-2:] # Top 2 sentences
            refined_text = " ".join([sentences[i] for i in sorted(top_indices)])
            
            subsection_analysis.append({"document": chunk['document'], "refined_text": refined_text, "page_number": chunk['page_number']})

        return {"extracted_sections": extracted_sections, "subsection_analysis": subsection_analysis}

def main(collection_path: Path):
    input_path = collection_path / "challenge1b_input.json"
    output_path = collection_path / "challenge1b_output.json"
    pdfs_path = collection_path / "PDFs"
    
    print(f"\n--- Processing collection: {collection_path.name} ---")
    
    try:
        with open(input_path, 'r') as f: input_data = json.load(f)
        
        persona, job = input_data["persona"]["role"], input_data["job_to_be_done"]["task"]
        query = f"{persona}: {job}"
        
        analyzer = PDFAnalyzer()
        
        all_chunks = []
        for doc_info in input_data["documents"]:
            pdf_file = pdfs_path / doc_info["filename"]
            if pdf_file.exists():
                print(f"Extracting content from {pdf_file.name}...")
                all_chunks.extend(analyzer.extract_page_chunks(pdf_file))
        
        analysis_results = analyzer.analyze_and_rank(all_chunks, query)
        
        final_output = {
            "metadata": {
                "input_documents": [doc["filename"] for doc in input_data["documents"]],
                "persona": persona,
                "job_to_be_done": job,
                "processing_timestamp": datetime.now(timezone.utc).isoformat()
            },
            **analysis_results
        }
        
        with open(output_path, 'w') as f: json.dump(final_output, f, indent=4)
        print(f"Successfully generated output for {collection_path.name}")
        
    except Exception as e:
        print(f"FATAL ERROR processing collection {collection_path.name}: {e}")

if __name__ == '__main__':
    base_path = Path(".")
    for collection_dir in sorted(base_path.glob("Collection *")):
        if collection_dir.is_dir():
            main(collection_dir)
