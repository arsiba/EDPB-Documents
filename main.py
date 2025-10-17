import requests
import time
import random
from edpb_scraper.config import INDEX_FILE, HEADERS, URLS
from edpb_scraper.parser import scrape_page
import json
import os

def build_or_load_index():
    """Ensure INDEX_FILE exists, scan folders, and build initial index from existing files."""
    index = {}

    # Ensure all folders exist
    for u in URLS:
        folder = u["folder"]
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Scan existing files in the folder
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                index[filename] = {"url": None, "folder": folder}

    # Write initial index if it doesn't exist yet
    if not os.path.exists(INDEX_FILE):
        print(f"{INDEX_FILE} not found. Creating new index from existing files...")
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    else:
        # Load the index if it exists
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index.update(json.load(f))
            # Merge filesystem scan to catch any files not yet in index
            with open(INDEX_FILE, "w", encoding="utf-8") as f_write:
                json.dump(index, f_write, ensure_ascii=False, indent=2)

    print(f"Index initialized. {len(index)} files currently recorded.")
    return index

def main():
    print("Starting EDPB scraper...")
    downloaded_index = build_or_load_index()
    session = requests.Session()
    session.headers.update(HEADERS)

    all_documents = []

    for u in URLS:
        folder = u["folder"]
        page_number = 0
        while True:
            new_downloads, docs_count = scrape_page(
                session, u["url"], folder, downloaded_index, INDEX_FILE, page_number
            )
            if page_number == 0 and new_downloads == 0:
                print("No new files on first page. Stopping URL.")
                break
            if docs_count == 0:
                break
            page_number += 1
            time.sleep(random.uniform(3, 10))

    print("Scraping finished.")
    print(f"Total files in index: {len(downloaded_index)}")

if __name__ == "__main__":
    main()
