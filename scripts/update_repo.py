import requests
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib

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
        "keywords": [],  # Empty = Download All
        "blacklist": []
    }
]

OUTPUT_DIR = Path("apk")
INDEX_FILE = Path("index.min.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def setup_dirs() -> None:
    """Setup output directory, preserving existing APKs"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_name(name: str) -> str:
    """Normalize extension name for matching"""
    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

def version_str_to_tuple(v_str: str) -> Tuple[int, ...]:
    """Converts version string to tuple for comparison"""
    try:
        return tuple(map(int, v_str.split(".")))
    except (ValueError, AttributeError):
        return (0, 0, 0)

def get_file_hash(filepath: Path) -> Optional[str]:
    """Calculate SHA256 hash of file"""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def fetch_with_retry(url: str, stream: bool = False, retries: int = 3) -> Optional[requests.Response]:
    """Fetch URL with retry logic"""
    headers = {'User-Agent': USER_AGENT}
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, stream=stream, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"    [!] Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None

def should_download_extension(name: str, keywords: List[str], blacklist: List[str]) -> bool:
    """Determine if extension matches criteria"""
    cleaned = clean_name(name)
    
    # Check blacklist first
    if any(b in cleaned for b in blacklist):
        return False
    
    # Empty keywords = download all
    if not keywords:
        return True
    
    # Check if any keyword matches
    return any(keyword in cleaned for keyword in keywords)

def load_existing_index() -> Dict[str, dict]:
    """Load existing index to avoid re-downloading unchanged files"""
    if not INDEX_FILE.exists():
        return {}
    
    try:
        with open(INDEX_FILE, 'r') as f:
            extensions = json.load(f)
        return {ext['pkg']: ext for ext in extensions}
    except Exception as e:
        print(f"[!] Warning: Could not load existing index: {e}")
        return {}

def collect_extensions() -> Dict[str, dict]:
    """Collect and deduplicate extensions from all sources"""
    unique_extensions = {}
    
    for source in SOURCES:
        print(f"\n--- Scanning {source['type']} ---")
        
        response = fetch_with_retry(source['json_url'])
        if not response:
            print(f"[!] Failed to fetch {source['type']} repository")
            continue
        
        try:
            extensions = response.json()
        except json.JSONDecodeError:
            print(f"[!] Invalid JSON from {source['type']} repository")
            continue
        
        for ext in extensions:
            name = ext.get('name', 'Unknown')
            pkg = ext.get('pkg', 'unknown.pkg')
            version = ext.get('version', '0')
            
            # Check if extension should be included
            if not should_download_extension(name, source['keywords'], source['blacklist']):
                continue
            
            # Version comparison
            is_new = False
            if pkg not in unique_extensions:
                is_new = True
                print(f"  [+] New: {name} (v{version})")
            else:
                old_ver = version_str_to_tuple(unique_extensions[pkg]['version'])
                new_ver = version_str_to_tuple(version)
                if new_ver > old_ver:
                    print(f"  [^] Upgrade: {name} v{unique_extensions[pkg]['version']} -> v{version}")
                    is_new = True
            
            if is_new:
                ext['_source_base_url'] = source['apk_base_url']
                unique_extensions[pkg] = ext
    
    return unique_extensions

def download_extension(pkg: str, ext: dict, existing_index: Dict[str, dict]) -> Optional[dict]:
    """Download a single extension APK"""
    name = ext.get('name')
    version = ext.get('version')
    raw_apk_link = ext.get('apk', '')
    base_url = ext.pop('_source_base_url')
    
    final_filename = f"{pkg}.v{version}.apk"
    dest_path = OUTPUT_DIR / final_filename
    
    # Skip if already exists and matches existing index
    if pkg in existing_index and existing_index[pkg].get('version') == version:
        if dest_path.exists():
            print(f"  [=] Skipped: {name} (v{version}) - already up to date")
            ext['apk'] = f"{REPO_ROOT}/apk/{final_filename}"
            # Remove internal keys
            ext.pop('_source_base_url', None)
            ext.pop('sources', None)
            return ext
    
    print(f"  [↓] Downloading: {name} (v{version})")
    
    # Construct download URL
    download_url = raw_apk_link if raw_apk_link.startswith("http") else f"{base_url}/{raw_apk_link}"
    
    # Download APK
    r_apk = fetch_with_retry(download_url, stream=True)
    if not r_apk:
        print(f"      [X] Failed to download. Skipping.")
        return None
    
    # Save APK
    try:
        with open(dest_path, 'wb') as f:
            for chunk in r_apk.iter_content(chunk_size=8192):
                f.write(chunk)
    except IOError as e:
        print(f"      [X] Failed to save: {e}")
        return None
    
    # Update extension metadata
    ext['apk'] = f"{REPO_ROOT}/apk/{final_filename}"
    ext.pop('sources', None)
    
    return ext

def cleanup_old_versions(final_index: List[dict]) -> None:
    """Remove old APK versions that are no longer in the index"""
    current_files = {ext['apk'].split('/')[-1] for ext in final_index}
    
    for apk_file in OUTPUT_DIR.glob("*.apk"):
        if apk_file.name not in current_files:
            print(f"  [−] Removing old version: {apk_file.name}")
            apk_file.unlink()

def process_repos() -> None:
    """Main processing function"""
    setup_dirs()
    
    # Load existing index for comparison
    existing_index = load_existing_index()
    
    # Phase 1: Collect and deduplicate
    unique_extensions = collect_extensions()
    
    if not unique_extensions:
        print("\n[!] No extensions found to process")
        return
    
    # Phase 2: Download and generate index
    print(f"\n--- Processing {len(unique_extensions)} unique extensions ---")
    final_index = []
    
    for pkg, ext in unique_extensions.items():
        result = download_extension(pkg, ext, existing_index)
        if result:
            final_index.append(result)
    
    # Phase 3: Write index
    with open(INDEX_FILE, 'w') as f:
        json.dump(final_index, f, indent=2)
    
    # Phase 4: Cleanup old versions
    cleanup_old_versions(final_index)
    
    print(f"\n✓ Success! Total extensions: {len(final_index)}")
    print(f"  - New/Updated: {len([e for e in final_index if e['pkg'] not in existing_index or existing_index[e['pkg']].get('version') != e.get('version')])}")
    print(f"  - Unchanged: {len([e for e in final_index if e['pkg'] in existing_index and existing_index[e['pkg']].get('version') == e.get('version')])}")

if __name__ == "__main__":
    try:
        process_repos()
    except KeyboardInterrupt:
        print("\n\n[!] Process interrupted by user")
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        raise