import requests
import json
import os
import shutil
import re

# --- CONFIGURATION ---
# REPLACE WITH YOUR INFO
REPO_ROOT = "https://raw.githubusercontent.com/Daiya404/Animanga-apps/main"

SOURCES = [
    {
        "type": "Anime",
        "url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/index.min.json",
        "mode": "whitelist",
        # Names as they appear in your request. The script normalizes them to match.
        "targets": ["AllAnime", "HiAnime", "AnimePahe", "AnimeKai"]
    },
    {
        "type": "Manga",
        "url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json",
        "mode": "whitelist",
        # Added "AllManga" and "All Manga" to be safe
        "targets": ["MangaDex", "Weeb Central", "All Manga", "AllManga"]
    },
    {
        "type": "Novel",
        "url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/index.min.json",
        "mode": "all",
        "targets": []
    }
]

OUTPUT_DIR = "apk"
INDEX_FILE = "index.min.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def clean_name(name):
    """Removes spaces and special chars for fuzzy matching (e.g. 'Weeb Central' -> 'weebcentral')"""
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

def setup_dirs():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def download_file(url, dest_path):
    headers = {'User-Agent': USER_AGENT}
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"  [X] Download failed: {url} \n      Error: {e}")
        return False

def process_repos():
    final_index = []
    setup_dirs()
    
    headers = {'User-Agent': USER_AGENT}

    for source in SOURCES:
        print(f"\n--- Processing {source['type']} ---")
        try:
            r = requests.get(source['url'], headers=headers)
            r.raise_for_status()
            extensions = r.json()
        except Exception as e:
            print(f"Failed to fetch source list: {e}")
            continue

        # Prepare target list (normalized)
        target_set = {clean_name(t) for t in source['targets']}
        
        count = 0
        for ext in extensions:
            name = ext.get('name', 'Unknown')
            pkg = ext.get('pkg', '')
            version = ext.get('version', '0')
            apk_url = ext.get('apk', '')
            
            normalized_name = clean_name(name)
            
            # Check if we should keep this extension
            keep = False
            if source['mode'] == "all":
                keep = True
            elif source['mode'] == "whitelist":
                if normalized_name in target_set:
                    keep = True
            
            if keep:
                # Construct local filename
                filename = f"{pkg}.v{version}.apk"
                file_path = os.path.join(OUTPUT_DIR, filename)
                
                print(f"  [+] Found: {name}")
                
                # Download APK
                if download_file(apk_url, file_path):
                    # Update the entry to point to our repo
                    ext['apk'] = f"{REPO_ROOT}/apk/{filename}"
                    final_index.append(ext)
                    count += 1
        
        print(f"  -> Added {count} extensions from {source['type']}")

    # Save the final index
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"\nSuccess! Generated {INDEX_FILE} with {len(final_index)} extensions.")

if __name__ == "__main__":
    process_repos()