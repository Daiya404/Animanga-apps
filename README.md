# Animanga Apps Extension Repo

![Update Extensions](https://github.com/Daiya404/Animanga-apps/actions/workflows/update.yml/badge.svg)

A curated, lightweight extension repository for **Aniyomi**, **Mihon**, **Tachiyomi**, and **Dantotsu**. 

This repository is automatically updated daily. It features a **smart version-checker** that filters multiple sources and ensures you only download the latest, stable version of an extension without duplicates.

## 📥 How to Add

1. Open your App (**Aniyomi**, **Mihon**, etc.).
2. Go to **Settings** > **Browse** > **Extension Repos**.
3. Tap **Add** and paste the following URL:

```text
https://raw.githubusercontent.com/Daiya404/Animanga-apps/main/index.min.json
```

> **⚠️ Important:** After adding the repo, go to your Extensions list and **pull down to refresh**. If extensions do not appear, check your **Filter** icon and ensure **"English"** and **"All"** languages are enabled.

## 🧩 Extension List

### 📺 Anime
| Extension | Language | Source |
| :--- | :---: | :--- |
| **AllAnime** | EN | Yuzono |
| **HiAnime** (Zoro) | EN | Yuzono |
| **AnimePahe** | EN | Yuzono |
| **AnimeKai** | EN | Yuzono |

### 📖 Manga
| Extension | Language | Source |
| :--- | :---: | :--- |
| **MangaDex** | All | Keiyoushi |
| **Weeb Central** | EN | Keiyoushi |
| **AllManga** | EN | Keiyoushi |
| **Bato.to** | EN | Keiyoushi |
| **MangaFire** | EN | Keiyoushi |
| **MangaPark** | EN | Keiyoushi |
| **MayoTune** | EN | Keiyoushi |

### 📚 Novels
| Extension | Language | Source |
| :--- | :---: | :--- |
| **AnnasArchive** | All | Dannovels |
| **Libgen** | All | Dannovels |

## ⚙️ How it Works

1.  **Aggregation:** A Python script runs every 24 hours via GitHub Actions.
2.  **Smart Filtering:** It scans massive extension repositories (Yuzono, Keiyoushi, Dannovels).
3.  **Deduplication:** If multiple versions of the same extension exist (e.g., v1.4.1 and v1.4.2), the script mathematically compares them and keeps **only the highest version**.
4.  **Hosting:** The APKs are hosted directly in this repository for fast, reliable access.

## 🏆 Credits

This repo wouldn't exist without the work of these upstream maintainers:
*   **Anime:** [yuzono/anime-repo](https://github.com/yuzono/anime-repo)
*   **Manga:** [keiyoushi/extensions](https://github.com/keiyoushi/extensions)
*   **Novels:** [dannovels/novel-extensions](https://github.com/dannovels/novel-extensions)

---
*This repository is for personal use and education. I do not create the extensions, I only mirror specific ones for convenience.*