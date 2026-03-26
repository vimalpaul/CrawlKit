<div align="center">

```
   ___                    _ _  ___ _
  / __| _ __ _ __ __ __ | | |/ (_) |_
 | (__ | '__|/ _` |\ V  V /| | ' <| | __|
  \___||_|  \__,_| \_/\_/ |_|_|\_\_|\__|
```

### Universal Web Crawler & Asset Enumerator

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?logo=kalilinux&logoColor=white)](https://kali.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**CrawlKit** is a powerful web crawler and asset enumerator for security professionals, created by **Vimal T**. Point it at any domain, feed it HAR files, and get comprehensive **Excel + HTML reports** with full URL enumeration.

</div>

---

## Features

- **Universal Crawling** — Works with any domain. Just give it a URL.
- **HAR File Analysis** — Parse browser-captured HAR files for deep URL extraction (AJAX, API calls, etc.)
- **Excel Reports** — 5-sheet XLSX: All URLs, Domain Summary, Source Breakdown, Status Codes, Content Types
- **Premium HTML Reports** — Beautiful white-theme reports with dashboard cards, searchable tables, domain charts
- **Deep Extraction** — Extracts from `<a>`, `<script>`, `<link>`, `<img>`, `<iframe>` + JavaScript regex
- **BFS Crawling** — Breadth-first traversal with configurable rate limiting
- **Cross-Platform** — Works on Kali Linux, Ubuntu, Windows

---

## Installation

```bash
git clone https://github.com/vimalpaul/CrawlKit.git
cd CrawlKit
pip3 install -r requirements.txt
```

---

## Usage

### Basic Crawl

```bash
python crawlkit.py -u https://www.example.com
```

### Crawl + HAR File (recommended)

```bash
python crawlkit.py -u https://www.wickes.co.uk -har www.wickes.co.uk.har -m 2000 -o wickes_enumeration
```

### HAR-Only Mode

```bash
python crawlkit.py -u https://target.com -har capture.har --skip-crawl
```

### Quick Scan

```bash
python crawlkit.py -u https://example.com -m 500 -d 0.1
```

---

## CLI Reference

| Flag | Short | Required | Default | Description |
|------|-------|----------|---------|-------------|
| `--url` | `-u` | Yes | — | Target URL to crawl |
| `--har` | `-har` | No | — | Path to HAR file |
| `--max-pages` | `-m` | No | `2000` | Max pages to crawl |
| `--output` | `-o` | No | `{domain}_crawlkit_report` | Output filename prefix |
| `--delay` | `-d` | No | `0.3` | Delay between requests (seconds) |
| `--skip-crawl` | — | No | `False` | Skip crawling, parse HAR only |
| `--version` | `-v` | No | — | Show version |

---

## Output

### Excel Report (`.xlsx`) — 5 Sheets

| Sheet | Contents |
|-------|----------|
| All URLs | Every URL with domain, path, query params, status, content type, source |
| Domain Summary | URL count per subdomain |
| Source Breakdown | Crawler vs HAR per domain |
| Status Codes | HTTP status distribution |
| Content Types | Content type distribution |

### HTML Report (`.html`)

- Hero header with domain + key metrics
- Dashboard cards (Total URLs, Domains, Crawler/HAR counts)
- Domain breakdown bar chart
- Status code distribution
- Searchable, sortable URL table
- Self-contained single HTML file

---

## How It Works

```
1. Web Crawler (BFS)
   - Follow <a>, <link>, <script> tags
   - Extract <img>, <iframe> URLs
   - Regex scan JavaScript for URLs

2. HAR File Parser
   - Parse HTTP Archive JSON
   - Extract all network requests
   - Filter by target domain

3. Report Generation
   - Excel (.xlsx) — 5 sheets
   - HTML (.html) — Premium report
```

---

## How to Capture a HAR File

1. Open Chrome → Press F12 → Go to **Network** tab
2. Browse the target website (click around!)
3. Right-click in the Network panel → **Save all as HAR with content**
4. Feed it to CrawlKit with `-har filename.har`

---

## License

MIT License — do whatever you want with it.

---

<div align="center">

**Built for Kali Linux** | **Made with Python** | **Author: Vimal T**

</div>
