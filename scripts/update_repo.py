import requests
import json
import os
import shutil

# Configuration
REPO_URL_BASE = "https://raw.githubusercontent.com/Daiya404/Animanga-apps/main/apk/" 

SOURCES = [
    {
        "url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/index.min.json",
        "type": "anime",
        "filter_mode": "whitelist",
        "targets": ["AllAnime", "HiAnime", "AnimePahe", "AnimeKai"] 
    },
    {
        "url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json",
        "type": "manga",
        "filter_mode": "whitelist",
        "targets": ["MangaDex", "Weeb Central", "AllManga"]
    },
    {
        "url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/index.min.json",
        "type": "novel",
        "filter_mode": "all", 
        "targets": [] # "all" mode grabs everything
    }
]

OUTPUT_DIR = "apk"
INDEX_FILE = "index.min.json"

def setup_dir():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def download_apk(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        file_path = os.path.join(OUTPUT_DIR, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def process_sources():
    final_index = []
    
    setup_dir()

    for source in SOURCES:
        print(f"Fetching {source['type']} extensions...")
        try:
            r = requests.get(source['url'])
            data = r.json()
        except Exception as e:
            print(f"Error fetching source JSON {source['url']}: {e}")
            continue

        # Handle target normalization for case-insensitive matching
        targets_lower = [t.lower() for t in source['targets']]

        for ext in data:
            name = ext.get("name", "")
            pkg = ext.get("pkg", "")
            version = ext.get("version", "0")
            
            # Determine if we should keep this extension
            should_keep = False
            if source['filter_mode'] == "all":
                should_keep = True
            elif source['filter_mode'] == "whitelist":
                # distinct check to handle "AllManga" vs "AllAnime" confusion
                if name.lower() in targets_lower:
                    should_keep = True

            if should_keep:
                print(f"Found target: {name} ({pkg})")
                
                # Define new filename based on package to avoid duplicates
                apk_filename = f"{pkg}.v{version}.apk"
                download_url = ext.get("apk")
                
                # Download the APK
                if download_apk(download_url, apk_filename):
                    # Modify the entry to point to OUR repo
                    ext['apk'] = f"{REPO_URL_BASE}{apk_filename}"
                    final_index.append(ext)

    # Write the new index file
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"Done! Total extensions: {len(final_index)}")

if __name__ == "__main__":
    process_sources()