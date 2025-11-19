import requests
import json
import os
import shutil
import re
import time

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
        "keywords": [], # Empty = Download All
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

def version_str_to_tuple(v_str):
    """Converts '1.4.2' to (1, 4, 2) for correct comparison"""
    try:
        return tuple(map(int, (v_str.split("."))))
    except:
        return (0, 0, 0)

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
    setup_dirs()
    
    # We use a dictionary to store ONLY unique packages.
    # Key = Package Name (e.g., "eu.kanade.mayotune")
    # Value = The Extension Data Object
    unique_extensions = {}

    # --- PHASE 1: COLLECT AND DEDUPLICATE ---
    for source in SOURCES:
        print(f"\n--- Scanning {source['type']} ---")
        
        response = fetch_with_retry(source['json_url'])
        if not response: continue
            
        try:
            extensions = response.json()
        except: continue

        for ext in extensions:
            name = ext.get('name', 'Unknown')
            pkg = ext.get('pkg', 'unknown.pkg')
            version = ext.get('version', '0')
            
            # Cleaning & Matching Logic
            cleaned = clean_name(name)
            if any(b in cleaned for b in source['blacklist']): continue

            should_download = False
            if not source['keywords']:
                should_download = True
            else:
                for keyword in source['keywords']:
                    if keyword in cleaned:
                        should_download = True
                        break
            
            if should_download:
                # Version Comparison Logic
                is_new = False
                if pkg not in unique_extensions:
                    is_new = True
                else:
                    old_ver = version_str_to_tuple(unique_extensions[pkg]['version'])
                    new_ver = version_str_to_tuple(version)
                    if new_ver > old_ver:
                        print(f"  [^] Upgrade found for {name}: v{unique_extensions[pkg]['version']} -> v{version}")
                        is_new = True
                
                if is_new:
                    # Store source specific data in the object for Phase 2
                    ext['_source_base_url'] = source['apk_base_url']
                    unique_extensions[pkg] = ext

    # --- PHASE 2: DOWNLOAD AND GENERATE ---
    print(f"\n--- Downloading {len(unique_extensions)} unique extensions ---")
    final_index = []
    
    for pkg, ext in unique_extensions.items():
        name = ext.get('name')
        version = ext.get('version')
        raw_apk_link = ext.get('apk', '')
        base_url = ext.pop('_source_base_url') # Remove internal key

        print(f"  [+] Downloading: {name} (v{version})")

        # Filename
        final_filename = f"{pkg}.v{version}.apk"
        
        # URL Construction
        if raw_apk_link.startswith("http"):
            download_url = raw_apk_link
        else:
            download_url = f"{base_url}/{raw_apk_link}"

        # Download
        dest_path = os.path.join(OUTPUT_DIR, final_filename)
        
        if not os.path.exists(dest_path):
            r_apk = fetch_with_retry(download_url, stream=True)
            if r_apk:
                with open(dest_path, 'wb') as f:
                    for chunk in r_apk.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                print(f"      [X] Failed to download. Skipping.")
                continue
        
        # Update JSON for index
        ext['apk'] = f"{REPO_ROOT}/apk/{final_filename}"
        if 'sources' in ext: del ext['sources']
        
        final_index.append(ext)

    # Write Index
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"\nSuccess! Total extensions: {len(final_index)}")

if __name__ == "__main__":
    process_repos()