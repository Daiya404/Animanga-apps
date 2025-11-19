import requests
import json
import os
import shutil
import re
import time

# --- CONFIGURATION ---
GITHUB_USERNAME = "Daiya404"
REPO_NAME = "Animanga-apps"
REPO_ROOT = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main"

SOURCES = [
    {
        "type": "Anime",
        "json_url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/apk",
        "keywords": ["allanime", "hianime", "animepahe", "animekai"],
        "blacklist": ["allanimechi"] 
    },
    {
        "type": "Manga",
        "json_url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/apk",
        # Added requested extensions here
        "keywords": [
            "mangadex", "weebcentral", "allmanga", 
            "bato", "xbato", "mangafire", "mangapark", "mayotune"
        ],
        "blacklist": []
    },
    {
        "type": "Novel",
        "json_url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/apk",
        "keywords": [], # Empty list = Download Everything from this source
        "blacklist": []
    }
]

OUTPUT_DIR = "apk"
INDEX_FILE = "index.min.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def setup_dirs():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

def fetch_with_retry(url, stream=False, retries=3):
    headers = {'User-Agent': USER_AGENT}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, stream=stream, timeout=20)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"    [!] Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

def process_repos():
    final_index = []
    setup_dirs()

    for source in SOURCES:
        print(f"\n--- Processing {source['type']} ---")
        
        response = fetch_with_retry(source['json_url'])
        if not response:
            continue
            
        try:
            extensions = response.json()
        except json.JSONDecodeError:
            print("    [X] JSON Decode Error")
            continue

        count = 0
        
        for ext in extensions:
            name = ext.get('name', 'Unknown')
            pkg = ext.get('pkg', 'unknown.pkg')
            version = ext.get('version', '0')
            raw_apk_link = ext.get('apk', '')
            
            cleaned = clean_name(name)
            
            # 1. Check Blacklist
            if any(b in cleaned for b in source['blacklist']):
                continue

            # 2. Check Whitelist/Keywords
            should_download = False
            if not source['keywords']:
                should_download = True
            else:
                for keyword in source['keywords']:
                    if keyword in cleaned:
                        should_download = True
                        break
            
            if should_download:
                print(f"  [+] Processing: {name}")

                # 3. Standardize Filename
                final_filename = f"{pkg}.v{version}.apk"
                
                # 4. Determine Download URL
                if raw_apk_link.startswith("http"):
                    download_url = raw_apk_link
                else:
                    download_url = f"{source['apk_base_url']}/{raw_apk_link}"

                # 5. Download
                dest_path = os.path.join(OUTPUT_DIR, final_filename)
                
                # Skip redownload if file exists (optimization)
                if os.path.exists(dest_path):
                     # Still add to index even if we don't re-download
                    ext['apk'] = f"{REPO_ROOT}/apk/{final_filename}"
                    if 'sources' in ext: del ext['sources']
                    final_index.append(ext)
                    count += 1
                    continue

                r_apk = fetch_with_retry(download_url, stream=True)
                
                if r_apk:
                    with open(dest_path, 'wb') as f:
                        for chunk in r_apk.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    ext['apk'] = f"{REPO_ROOT}/apk/{final_filename}"
                    if 'sources' in ext: del ext['sources']
                        
                    final_index.append(ext)
                    count += 1
                else:
                    print(f"      [X] Download failed.")
        
        print(f"  -> Added {count} extensions.")

    # Write single index file
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"\nSuccess! Total extensions: {len(final_index)}")

if __name__ == "__main__":
    process_repos()