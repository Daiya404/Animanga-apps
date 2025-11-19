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

# Specific settings for each repository
SOURCES = [
    {
        "type": "Anime",
        "json_url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/apk",
        # Lowercase keywords to search for in the extension name
        "keywords": ["allanime", "hianime", "animepahe", "animekai"]
    },
    {
        "type": "Manga",
        "json_url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/apk",
        "keywords": ["mangadex", "weebcentral", "allmanga"]
    },
    {
        "type": "Novel",
        "json_url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/index.min.json",
        "apk_base_url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/apk",
        # Empty keywords = Download EVERYTHING from this source
        "keywords": [] 
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
    """
    Removes special characters and spaces to make matching easier.
    Example: "Aniyomi: AllAnime" -> "aniyomiallanime"
    """
    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

def fetch_with_retry(url, stream=False, retries=3):
    headers = {'User-Agent': USER_AGENT}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, stream=stream, timeout=15)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"    [!] Attempt {attempt+1} failed: {e}")
            time.sleep(2) # Wait 2 seconds before retrying
    return None

def process_repos():
    final_index = []
    setup_dirs()

    for source in SOURCES:
        print(f"\n--- Processing {source['type']} ---")
        
        # 1. Fetch the JSON list
        response = fetch_with_retry(source['json_url'])
        if not response:
            print("    [X] Failed to fetch JSON list. Skipping.")
            continue
            
        try:
            extensions = response.json()
        except json.JSONDecodeError:
            print("    [X] Failed to decode JSON.")
            continue

        count = 0
        
        for ext in extensions:
            name = ext.get('name', 'Unknown')
            raw_apk_name = ext.get('apk', '')
            version = ext.get('version', '0')
            
            # Prepare name for matching
            cleaned = clean_name(name)
            
            # 2. Check if we want this extension
            should_download = False
            
            # If keywords list is empty, we want ALL of them (Novel logic)
            if not source['keywords']:
                should_download = True
            else:
                # Check if ANY user keyword is inside the cleaned name
                for keyword in source['keywords']:
                    if keyword in cleaned:
                        should_download = True
                        break
            
            if should_download:
                print(f"  [+] Found target: {name}")

                # 3. Construct Download URL
                # If the APK link in JSON is full HTTP, use it. Otherwise join with base.
                if raw_apk_name.startswith("http"):
                    download_url = raw_apk_name
                    filename = raw_apk_name.split('/')[-1] # Grab just the name part
                else:
                    download_url = f"{source['apk_base_url']}/{raw_apk_name}"
                    filename = raw_apk_name

                # 4. Download the APK
                file_path = os.path.join(OUTPUT_DIR, filename)
                r_apk = fetch_with_retry(download_url, stream=True)
                
                if r_apk:
                    with open(file_path, 'wb') as f:
                        for chunk in r_apk.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # 5. Update JSON entry to point to OUR repo
                    ext['apk'] = f"{REPO_ROOT}/apk/{filename}"
                    
                    # Remove 'sources' list to save space in index.json (optional but cleaner)
                    if 'sources' in ext:
                        del ext['sources']
                        
                    final_index.append(ext)
                    count += 1
                    print(f"      -> Downloaded: {filename}")
                else:
                    print(f"      [X] Failed to download APK.")
        
        print(f"  -> Added {count} extensions from {source['type']}.")

    # Write the final master index
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"\nSuccess! Total extensions in repo: {len(final_index)}")

if __name__ == "__main__":
    process_repos()