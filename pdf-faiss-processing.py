# -*- coding: utf-8 -*-
"""
@author: arneb

Preprocessing script for PDF documents with adjusted chunk sizes and overlap
"""

import torch
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import PyPDF2
import numpy as np
import os
import faiss
import re
import argparse
import pickle
import time
from tqdm import tqdm

PDF_DIRECTORIES = ["oss_documents", "edpb_documents", "gdpr_documents"]

CHUNK_SIZE = 120
CHUNK_OVERLAP = 25        

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
GEN_QA_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

OUTPUT_DIR = "vector_db"


def parse_args():
    parser = argparse.ArgumentParser(description='Preprocess PDF documents for QA system')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for embedding generation')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='Output directory for vector database')
    return parser.parse_args()


def clean_text(text):
    """Clean and normalize text from PDFs"""
    text = re.sub(r'(\n){2,}', '\n', text)
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)
    return text.strip()


def chunk_text(text, tokenizer):
    """Split text into semantic chunks with overlap"""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        tok_len = len(tokenizer.tokenize(sentence))
        if current_len + tok_len > CHUNK_SIZE:
            chunks.append(" ".join(current_chunk))
            overlap, overlap_len = [], 0
            for sent in reversed(current_chunk):
                slen = len(tokenizer.tokenize(sent))
                if overlap_len + slen > CHUNK_OVERLAP:
                    break
                overlap.insert(0, sent)
                overlap_len += slen
            current_chunk = overlap
            current_len = overlap_len

        current_chunk.append(sentence)
        current_len += tok_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def process_pdf(file_path, tokenizer):
    """Process a single PDF file and return its content with page tracking"""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = []
        for page_num, page in enumerate(reader.pages):
            text = clean_text(page.extract_text() or "")
            if text:
                full_text.append((page_num + 1, text))

    return {
        "title": os.path.basename(file_path),
        "pages": [t[1] for t in full_text],
        "page_numbers": [t[0] for t in full_text]
    }


def collect_pdf_files():
    """Collect all PDF files from specified directories"""
    all_files = []
    for directory in PDF_DIRECTORIES:
        if not os.path.exists(directory):
            print(f"Warning: Directory '{directory}' does not exist. Creating it...")
            os.makedirs(directory)
            continue

        pdfs = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith('.pdf')]
        all_files.extend(pdfs)
        print(f"Found {len(pdfs)} PDF files in {directory}")

    return all_files


def main():
    args = parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    print("Initializing models...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    if device == "cuda":
        embedding_model = embedding_model.half()

    gen_tokenizer = AutoTokenizer.from_pretrained(GEN_QA_MODEL)

    pdf_files = collect_pdf_files()
    if not pdf_files:
        print("No PDF files found. Exiting.")
        return

    document_metadata, all_chunks = [], []
    start = time.time()
    print(f"Processing {len(pdf_files)} PDFs...")
    for path in tqdm(pdf_files, desc="PDFs"):
        try:
            data = process_pdf(path, gen_tokenizer)
            for pg, txt in zip(data['page_numbers'], data['pages']):
                for chunk in chunk_text(txt, gen_tokenizer):
                    document_metadata.append({
                        "source": data['title'],
                        "page": pg,
                        "directory": os.path.basename(os.path.dirname(path))
                    })
                    all_chunks.append(chunk)
        except Exception as e:
            print(f"Error {path}: {e}")

    if not all_chunks:
        print("No text extracted from PDFs. Exiting.")
        return

    print(f"Extracted {len(all_chunks)} chunks in {(time.time() - start):.2f}s")

    print("Generating embeddings...")
    emb_start = time.time()
    embeddings = embedding_model.encode(
        all_chunks,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    print(f"Embeddings done in {(time.time() - emb_start):.2f}s")

    print("Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
    index.add_with_ids(embeddings.astype(np.float32), np.arange(len(all_chunks), dtype=np.int64))

    print("Saving vector database...")
    faiss.write_index(index, os.path.join(args.output, 'index.faiss'))
    with open(os.path.join(args.output, 'chunks.pkl'), 'wb') as cf:
        pickle.dump(all_chunks, cf)
    with open(os.path.join(args.output, 'metadata.pkl'), 'wb') as mf:
        pickle.dump(document_metadata, mf)

    print(f"Saved {len(all_chunks)} chunks from {len(pdf_files)} documents to {args.output}")
    total_time = time.time() - start
    print(f"Total preprocessing time: {total_time:.2f}s")


if __name__ == '__main__':
    main()
