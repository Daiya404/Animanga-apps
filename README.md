# Animanga Apps Extension Repo

![Update Extensions](https://github.com/Daiya404/Animanga-apps/actions/workflows/update.yml/badge.svg)

A curated, lightweight extension repository for **Aniyomi**, **Mihon**, and **Dantotsu**. This repository is automatically updated daily to ensure you always have the latest versions of specific extensions without the bloat of the full repositories.

## 📥 How to Add

1. Open **Aniyomi** (or your preferred app).
2. Go to **More** -> **Settings** -> **Browse** -> **Extension Repos**.
3. Tap **Add** and paste the following URL:

```
https://raw.githubusercontent.com/Daiya404/Animanga-apps/main/index.min.json
```

> **Note:** After adding, make sure to pull down on the Extensions list to refresh it. If you don't see the extensions, check your **Filter** settings and ensure "English" and "All" languages are enabled.

## 🧩 Extension List

This repository currently hosts and auto-updates the following:

### 📺 Anime
| Extension | Language |
| :--- | :---: |
| **AllAnime** | EN |
| **HiAnime** (Zoro) | EN |
| **AnimePahe** | EN |
| **AnimeKai** | EN |

### 📖 Manga
| Extension | Language |
| :--- | :---: |
| **MangaDex** | All |
| **Weeb Central** | EN |
| **AllManga** | EN |

### 📚 Novels
| Extension | Language |
| :--- | :---: |
| **AnnasArchive** | All |
| **Libgen** | All |

## ⚙️ How it Works

*   **Automation:** A GitHub Actions workflow runs every 24 hours.
*   **Scripting:** A Python script fetches the latest data from the source repositories (Yuzono, Keiyoushi, Dannovels).
*   **Filtering:** It filters out *only* the extensions listed above, downloads the APKs, and generates a custom `index.min.json`.
*   **Hosting:** The APKs are hosted directly in this repository's `apk/` folder for fast access.

## credits

*   **Anime Source:** [yuzono/anime-repo](https://github.com/yuzono/anime-repo)
*   **Manga Source:** [keiyoushi/extensions](https://github.com/keiyoushi/extensions)
*   **Novel Source:** [dannovels/novel-extensions](https://github.com/dannovels/novel-extensions)

---
*This repository is for personal use and education. I do not create the extensions, I only mirror specific ones for convenience.*