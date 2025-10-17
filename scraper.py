# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time
import random
import json

BASE_URL = "https://www.edpb.europa.eu"

URLS = [
    {
        "url": BASE_URL + "/our-work-tools/consistency-findings/register-for-article-60-final-decisions_en",
        "folder": "article_60"
    },
    {
        "url": BASE_URL + "/our-work-tools/documents/our-documents_en",
        "folder": "our_documents"
    }
]

INDEX_FILE = "index.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL + "/",
    "Connection": "keep-alive",
}

for u in URLS:
    folder_path = u["folder"]
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

downloaded_index = {}
for u in URLS:
    folder_path = u["folder"]
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            downloaded_index[filename] = {"url": None, "folder": u["folder"]}

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(downloaded_index, f, ensure_ascii=False, indent=2)

print(f"Index aus Dateisystem aufgebaut: {len(downloaded_index)} Dateien vorhanden.")

def save_index():
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(downloaded_index, f, ensure_ascii=False, indent=2)

def download_file(session, url, filename, folder):
    if filename in downloaded_index:
        return False

    filepath = os.path.join(folder, filename)
    print("Sleeping in between downloads")
    time.sleep(random.uniform(3, 10))
    try:
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Datei heruntergeladen: {filename} in {folder}/")
        downloaded_index[filename] = {"url": url, "folder": folder}
        save_index()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Herunterladen von {url}: {e}")
        return False

def scrape_documents(base_url, session, folder):
    documents = []
    page_number = 0
    first_page_no_new = False

    while True:
        current_url = f"{base_url}?page={page_number}"
        print(f"\nScraping Seite {page_number + 1}: {current_url}")

        new_downloads_on_page = 0  # Zähler für neue Dateien auf dieser Seite

        try:
            response = session.get(current_url, timeout=30)
            if response.status_code == 403:
                print("403 Forbidden – Warte 60 Sekunden...")
                time.sleep(60)
                response = session.get(current_url, timeout=30)
                if response.status_code == 403:
                    print("Erneut 403. Breche ab.")
                    break

            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            document_items = soup.find_all("div", class_="views-row")

            if not document_items:
                print("Keine weiteren Dokumente gefunden.")
                break

            for idx, item in enumerate(document_items, 1):
                is_obsolete = item.find('div', class_='publication-status status-obsolete mb-1') is not None

                title_element = (
                    item.find("h4", class_="document-title")
                    or item.find("h3", class_="document-title")
                    or item.find("h4", class_="item-title")
                    or item.find("h3", class_="item-title")
                    or item.find("a")
                )

                if title_element and title_element.get("href"):
                    title = title_element.text.strip()
                    document_url = BASE_URL + title_element["href"]
                else:
                    title = "Kein Titel gefunden"
                    document_url = "Keine URL gefunden"

                download_links = (
                    item.find_all("a", class_="download")
                    + item.find_all("a", class_="file-download")
                    + item.find_all("a", class_="download-link")
                )

                if is_obsolete:
                    continue

                for link in download_links:
                    href = link.get("href")
                    if not href:
                        continue
                    download_url = href if href.startswith("http") else BASE_URL + href
                    filename = os.path.basename(download_url.split("?")[0])
                    if download_file(session, download_url, filename, folder):
                        new_downloads_on_page += 1
                        documents.append({
                            "title": title,
                            "url": document_url,
                            "downloaded_as": filename,
                            "folder": folder
                        })

        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Zugriff auf {current_url}: {e}")
            break

        if page_number == 0 and new_downloads_on_page == 0:
            print("Keine neuen Dateien auf der ersten Seite. Beende diese URL.")
            break
        page_number += 1
        time.sleep(random.uniform(3, 10))

    return documents

if __name__ == "__main__":
    print("Starte Scraper für EDPB-Dokumente")
    session = requests.Session()
    session.headers.update(HEADERS)

    all_documents = []
    for u in URLS:
        docs = scrape_documents(u["url"], session, u["folder"])
        all_documents.extend(docs)

    print("\nScraping abgeschlossen.")
    print(f"Anzahl heruntergeladener neuer Dokumente: {len([d for d in all_documents if d.get('downloaded_as')])}")
    print(f"Gesamtanzahl Dateien im Index: {len(downloaded_index)}")
