import os
import time
import random
import json

def save_index(index, index_file):
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def download_file(session, url, filename, folder, downloaded_index, index_file):
    if filename in downloaded_index:
        return False

    if not os.path.exists(folder):
        os.makedirs(folder)

    filepath = os.path.join(folder, filename)
    print(f"Sleeping before downloading {filename}...")
    time.sleep(random.uniform(3, 10))
    try:
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"File downloaded: {filename} in {folder}/")
        downloaded_index[filename] = {"url": url, "folder": folder}
        save_index(downloaded_index, index_file)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False
