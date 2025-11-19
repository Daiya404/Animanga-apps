import requests
import json
import os
import shutil
import re

# --- CONFIGURATION ---
GITHUB_USERNAME = "Daiya404"
REPO_NAME = "Animanga-apps"

# This builds the download link for your new repo
REPO_ROOT = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main"

SOURCES = [
    {
        "type": "Anime",
        "url": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/index.min.json",
        # Backup base URL in case the source uses relative links
        "apk_base": "https://raw.githubusercontent.com/yuzono/anime-repo/repo/apk",
        "mode": "whitelist",
        # We use "clean" names here (lowercase, no spaces) to match ANY variation
        "targets": ["allanime", "hianime", "animepahe", "animekai"]
    },
    {
        "type": "Manga",
        "url": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.min.json",
        "apk_base": "https://raw.githubusercontent.com/keiyoushi/extensions/repo/apk",
        "mode": "whitelist",
        "targets": ["mangadex", "weebcentral", "allmanga"]
    },
    {
        "type": "Novel",
        "url": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/index.min.json",
        "apk_base": "https://raw.githubusercontent.com/dannovels/novel-extensions/repo/apk",
        "mode": "all",
        "targets": []
    }
]

OUTPUT_DIR = "apk"
INDEX_FILE = "index.min.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def clean_name(name):
    """
    Converts 'All Anime' -> 'allanime', 'Weeb Central' -> 'weebcentral'
    This ensures we find the extension even if the spacing is different.
    """
    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

def setup_dirs():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def download_file(url, dest_path):
    headers = {'User-Agent': USER_AGENT}
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            if r.status_code != 200:
                print(f"    [!] HTTP {r.status_code} for {url}")
                return False
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"    [!] Download Exception: {e}")
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
            print(f"[!] Failed to fetch source list: {e}")
            continue

        # Prepare the list of targets for this source
        target_set = set(source['targets'])
        
        count = 0
        
        for ext in extensions:
            name = ext.get('name', 'Unknown')
            pkg = ext.get('pkg', '')
            version = ext.get('version', '0')
            apk_link = ext.get('apk', '')
            
            # 1. Fix broken URLs (Relative URL support)
            if not apk_link.startswith("http"):
                # If the link is just "app.apk", prepend the source repo URL
                apk_link = f"{source['apk_base']}/{apk_link}"

            # 2. Normalize name for comparison
            cleaned_name = clean_name(name)
            
            # 3. Check if we should keep this extension
            keep = False
            if source['mode'] == "all":
                keep = True
            elif source['mode'] == "whitelist":
                # Check if the cleaned name (e.g., 'allanime') is in our target list
                if cleaned_name in target_set:
                    keep = True

            if keep:
                # Create filename like: app.name.v1.2.3.apk
                filename = f"{pkg}.v{version}.apk"
                dest = os.path.join(OUTPUT_DIR, filename)
                
                print(f"  [+] Found: {name} (v{version})")
                
                # Download to our folder
                if download_file(apk_link, dest):
                    # IMPORTANT: Rewrite the APK link to point to YOUR repo
                    ext['apk'] = f"{REPO_ROOT}/apk/{filename}"
                    final_index.append(ext)
                    count += 1
        
        print(f"  -> Successfully added {count} {source['type']} extensions.")

    # Write the final index.min.json
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    print(f"\nSuccess! Final {INDEX_FILE} contains {len(final_index)} extensions.")

if __name__ == "__main__":
    process_repos()