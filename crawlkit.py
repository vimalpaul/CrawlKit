#!/usr/bin/env python3
"""
CrawlKit v1.0.0 - Universal Web Crawler & Asset Enumerator
Author: Vimal T
A Kali Linux tool for comprehensive domain enumeration.

Usage:
    python crawlkit.py -u https://www.wickes.co.uk -har www.wickes.co.uk.har -m 2000 -o wickes_report
    python crawlkit.py -u https://www.example.com -m 500
    python crawlkit.py -u https://target.com -har capture.har --skip-crawl
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time
import sys
import os
import re
import json
import argparse
import datetime
from collections import deque, Counter

__version__ = "1.0.0"

# ============================================================================
# SAFE PRINT (Windows + Linux compatible)
# ============================================================================

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.system('')  # Enable ANSI on Windows 10+


def cprint(msg):
    """Safe colored print with fallback."""
    try:
        print(msg)
    except (UnicodeEncodeError, UnicodeDecodeError):
        clean = re.sub(r'\033\[[0-9;]*m', '', msg)
        clean = clean.encode('ascii', errors='replace').decode('ascii')
        print(clean)


# ============================================================================
# BANNER
# ============================================================================

BANNER = """
\033[1;36m   ___                    _ _  ___ _
  / __| _ __ _ __ __ __ | | |/ (_) |_
 | (__ | '__|/ _` |\\ V  V /| | ' <| | __|
  \\___||_|  \\__,_| \\_/\\_/ |_|_|\\_\\_|\\__|
\033[0m
\033[1;37m  CrawlKit\033[0m \033[0;36mv{version}\033[0m
\033[1;37m  Universal Web Crawler & Asset Enumerator\033[0m
\033[0;37m  Author: Vimal T\033[0m
\033[0;37m  ------------------------------------------------\033[0m
"""


# ============================================================================
# CORE CRAWLER ENGINE
# ============================================================================

class CrawlKit:
    """Universal web crawler engine. Works with any target domain."""

    def __init__(self, start_url):
        self.start_url = start_url.rstrip('/')
        self.target_domain = self._extract_domain(start_url)
        self.visited = set()
        self.to_visit = deque([self.start_url])
        self.results = []
        self.all_domains = set()
        self.crawl_stats = {
            'pages_crawled': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def _extract_domain(self, url):
        """Extract base domain from URL."""
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            # Remove www. prefix for matching
            if netloc.startswith('www.'):
                return netloc[4:]
            return netloc
        except Exception:
            return None

    def _get_domain(self, url):
        """Get full domain/subdomain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None

    def _is_target(self, url):
        """Check if URL belongs to the target domain."""
        domain = self._get_domain(url)
        return domain and self.target_domain in domain

    def _add_result(self, url, status_code='N/A', content_type='N/A', source='crawler'):
        """Add a URL to results if not already present."""
        if url in [r['URL'] for r in self.results]:
            return
        parsed = urlparse(url)
        domain = self._get_domain(url)
        if domain:
            self.all_domains.add(domain)
        self.results.append({
            'URL': url,
            'Domain/Subdomain': domain,
            'Path': parsed.path,
            'Query Parameters': parsed.query if parsed.query else '',
            'Status Code': status_code,
            'Content Type': content_type,
            'Source': source
        })

    def _process_url(self, url, base_url):
        """Normalize and enqueue URL."""
        try:
            full_url = urljoin(base_url, url)
            full_url = full_url.split('#')[0]
            if self._is_target(full_url) and full_url not in self.visited:
                self.to_visit.append(full_url)
        except Exception:
            pass

    # ---- Web Crawl ----

    def crawl(self, max_pages=2000, delay=0.3):
        """BFS crawl the target website."""
        self.crawl_stats['start_time'] = datetime.datetime.now()

        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;37m  [*] CRAWLKIT - WEB CRAWLING\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[0;37m  Target  : \033[1;32m{self.target_domain}\033[0m")
        cprint(f"\033[0;37m  Start   : \033[1;32m{self.start_url}\033[0m")
        cprint(f"\033[0;37m  Max     : \033[1;32m{max_pages}\033[0m")
        cprint(f"\033[0;37m  Delay   : \033[1;32m{delay}s\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m\n")

        while self.to_visit and len(self.visited) < max_pages:
            current_url = self.to_visit.popleft()
            if current_url in self.visited:
                continue
            if not self._is_target(current_url):
                continue

            try:
                progress = len(self.visited) + 1
                short = current_url[:70] + '...' if len(current_url) > 70 else current_url
                cprint(f"  \033[0;36m[{progress}/{max_pages}]\033[0m {short}")

                resp = requests.get(current_url, headers=self.headers, timeout=10, allow_redirects=True)
                self.visited.add(current_url)

                self._add_result(
                    url=current_url,
                    status_code=resp.status_code,
                    content_type=resp.headers.get('Content-Type', 'N/A'),
                    source='web_crawler'
                )

                if resp.status_code == 200:
                    content = resp.text
                    ctype = resp.headers.get('Content-Type', '')

                    if 'text/html' in ctype:
                        soup = BeautifulSoup(content, 'html.parser')
                        for tag in soup.find_all('a', href=True):
                            self._process_url(tag['href'], current_url)
                        for tag in soup.find_all('script', src=True):
                            self._process_url(tag['src'], current_url)
                        for tag in soup.find_all('link', href=True):
                            self._process_url(tag['href'], current_url)
                        for tag in soup.find_all('img', src=True):
                            self._process_url(tag['src'], current_url)
                        for tag in soup.find_all('iframe', src=True):
                            self._process_url(tag['src'], current_url)

                    # Regex URL extraction from JS/text
                    for found in re.findall(r'https?://[^\s"\')\}<>]+', content):
                        if self.target_domain in found.lower():
                            self._process_url(found, current_url)

                time.sleep(delay)

            except Exception as e:
                self.crawl_stats['errors'] += 1
                cprint(f"  \033[0;31m[ERR]\033[0m {str(e)[:50]}")
                continue

        self.crawl_stats['pages_crawled'] = len(self.visited)
        self.crawl_stats['end_time'] = datetime.datetime.now()

        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;32m  [+] Crawl Complete\033[0m")
        cprint(f"\033[0;37m  Pages : \033[1;37m{len(self.visited)}\033[0m")
        cprint(f"\033[0;37m  URLs  : \033[1;37m{len(self.results)}\033[0m")
        cprint(f"\033[0;37m  Errors: \033[1;37m{self.crawl_stats['errors']}\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")

    # ---- HAR File Parser ----

    def parse_har(self, har_path):
        """Extract target-domain URLs from a HAR file."""
        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;37m  [*] CRAWLKIT - HAR FILE ANALYSIS\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[0;37m  File   : \033[1;32m{har_path}\033[0m")
        cprint(f"\033[0;37m  Filter : \033[1;32m{self.target_domain}\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m\n")

        try:
            with open(har_path, 'r', encoding='utf-8') as f:
                har_data = json.load(f)
        except FileNotFoundError:
            cprint(f"  \033[1;31m[!] HAR file not found: {har_path}\033[0m")
            return
        except json.JSONDecodeError:
            cprint(f"  \033[1;31m[!] Invalid HAR file format\033[0m")
            return
        except Exception as e:
            cprint(f"  \033[1;31m[!] Error: {e}\033[0m")
            return

        entries = har_data.get('log', {}).get('entries', [])
        cprint(f"  \033[0;37mTotal entries: \033[1;37m{len(entries)}\033[0m")
        matched = 0

        for idx, entry in enumerate(entries):
            try:
                req = entry.get('request', {})
                res = entry.get('response', {})
                url = req.get('url', '')

                if not self._is_target(url):
                    continue

                status = res.get('status', 'N/A')
                ctype = 'N/A'
                for h in res.get('headers', []):
                    if h.get('name', '').lower() == 'content-type':
                        ctype = h.get('value', 'N/A')
                        break

                self._add_result(url=url, status_code=status, content_type=ctype, source='har_file')
                matched += 1

                if (idx + 1) % 200 == 0:
                    cprint(f"  \033[0;36m[{idx+1}/{len(entries)}]\033[0m processed...")
            except Exception:
                continue

        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;32m  [+] HAR Analysis Complete\033[0m")
        cprint(f"\033[0;37m  Matched : \033[1;37m{matched}\033[0m")
        cprint(f"\033[0;37m  Skipped : \033[1;37m{len(entries) - matched}\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")

    # ---- Excel Report ----

    def save_excel(self, output_name):
        """Save results to Excel with multiple sheets."""
        if not self.results:
            cprint("\n  \033[1;31m[!] No results to export.\033[0m")
            return None

        filename = f"{output_name}.xlsx"
        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;37m  [*] GENERATING EXCEL REPORT\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")

        df = pd.DataFrame(self.results)

        domain_summary = df['Domain/Subdomain'].value_counts().reset_index()
        domain_summary.columns = ['Domain/Subdomain', 'URL Count']

        source_breakdown = df.groupby(['Domain/Subdomain', 'Source']).size().reset_index(name='Count')

        status_breakdown = df['Status Code'].value_counts().reset_index()
        status_breakdown.columns = ['Status Code', 'Count']

        content_breakdown = df['Content Type'].apply(
            lambda x: x.split(';')[0].strip() if isinstance(x, str) else 'N/A'
        ).value_counts().reset_index()
        content_breakdown.columns = ['Content Type', 'Count']

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All URLs', index=False)
            domain_summary.to_excel(writer, sheet_name='Domain Summary', index=False)
            source_breakdown.to_excel(writer, sheet_name='Source Breakdown', index=False)
            status_breakdown.to_excel(writer, sheet_name='Status Codes', index=False)
            content_breakdown.to_excel(writer, sheet_name='Content Types', index=False)

        cprint(f"\033[1;32m  [+] Saved: \033[0;37m{filename}\033[0m")
        cprint(f"\033[0;37m  URLs   : \033[1;37m{len(df)}\033[0m")
        cprint(f"\033[0;37m  Sheets : \033[1;37m5\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")
        return filename

    # ---- HTML Report ----

    def save_html(self, output_name):
        """Generate a premium white-theme HTML report."""
        if not self.results:
            cprint("\n  \033[1;31m[!] No results to export.\033[0m")
            return None

        filename = f"{output_name}.html"
        cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
        cprint(f"\033[1;37m  [*] GENERATING HTML REPORT\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")

        total_urls = len(self.results)
        domains = set(r['Domain/Subdomain'] for r in self.results if r.get('Domain/Subdomain'))
        total_domains = len(domains)

        source_counts = Counter(r.get('Source', 'unknown') for r in self.results)
        crawler_count = source_counts.get('web_crawler', 0)
        har_count = source_counts.get('har_file', 0)

        # Status code buckets
        status_counts = Counter()
        for r in self.results:
            sc = r.get('Status Code', 'N/A')
            if isinstance(sc, int) or (isinstance(sc, str) and sc.isdigit()):
                code = int(sc)
                if 200 <= code < 300: status_counts['2xx Success'] += 1
                elif 300 <= code < 400: status_counts['3xx Redirect'] += 1
                elif 400 <= code < 500: status_counts['4xx Client Error'] += 1
                elif 500 <= code < 600: status_counts['5xx Server Error'] += 1
                else: status_counts['Other'] += 1
            else:
                status_counts['N/A'] += 1

        # Domain breakdown
        domain_counts = Counter(r['Domain/Subdomain'] for r in self.results if r.get('Domain/Subdomain'))
        top_domains = domain_counts.most_common(20)
        max_dc = top_domains[0][1] if top_domains else 1

        # Content types
        content_counts = Counter()
        for r in self.results:
            ct = r.get('Content Type', 'N/A')
            content_counts[ct.split(';')[0].strip() if isinstance(ct, str) and ct != 'N/A' else 'N/A'] += 1
        top_content = content_counts.most_common(10)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pages_crawled = self.crawl_stats.get('pages_crawled', 0)

        # Build domain bars
        domain_bars = ''
        for d, c in top_domains:
            pct = (c / max_dc) * 100
            domain_bars += f'<div class="bar-row"><div class="bar-label" title="{d}">{d}</div><div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div><div class="bar-value">{c}</div></div>\n'

        # Build status items
        scolors = {'2xx Success':'#10b981','3xx Redirect':'#f59e0b','4xx Client Error':'#ef4444','5xx Server Error':'#dc2626','N/A':'#94a3b8','Other':'#6b7280'}
        status_html = ''
        for label, cnt in sorted(status_counts.items()):
            color = scolors.get(label, '#6b7280')
            status_html += f'<div class="status-item"><span class="status-dot" style="background:{color}"></span><span class="status-label">{label}</span><span class="status-count">{cnt}</span></div>\n'

        # Content type items
        content_html = ''
        for ct, cnt in top_content:
            content_html += f'<div class="content-item"><span class="content-label">{ct}</span><span class="content-count">{cnt}</span></div>\n'

        # Table rows
        rows = ''
        for i, r in enumerate(self.results):
            sc = r.get('Status Code', 'N/A')
            sc_cls = ''
            if isinstance(sc, int) or (isinstance(sc, str) and sc.isdigit()):
                c = int(sc)
                if 200 <= c < 300: sc_cls = 'status-2xx'
                elif 300 <= c < 400: sc_cls = 'status-3xx'
                elif 400 <= c < 500: sc_cls = 'status-4xx'
                elif c >= 500: sc_cls = 'status-5xx'

            url = r.get('URL', '')
            dom = r.get('Domain/Subdomain', '')
            path = r.get('Path', '')
            ct = r.get('Content Type', 'N/A')
            src = r.get('Source', '')
            badge = 'badge-crawler' if src == 'web_crawler' else 'badge-har'
            ct_short = ct.split(';')[0][:25] if isinstance(ct, str) else 'N/A'

            rows += f'''<tr>
<td class="cell-num">{i+1}</td>
<td class="cell-url" title="{url}"><a href="{url}" target="_blank">{url[:80]}{'...' if len(url)>80 else ''}</a></td>
<td class="cell-domain">{dom}</td>
<td class="cell-path" title="{path}">{path[:40]}{'...' if len(path)>40 else ''}</td>
<td class="cell-status {sc_cls}">{sc}</td>
<td class="cell-type" title="{ct}">{ct_short}</td>
<td class="cell-source"><span class="source-badge {badge}">{src}</span></td>
</tr>
'''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CrawlKit Report - {self.target_domain}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#f8f9fc;--surface:#fff;--text:#1a1d29;--text2:#5a5f72;--muted:#9498a8;--border:#e8eaef;--border-light:#f0f1f5;--accent:#4f6ef7;--accent-light:#eef1fe;--success:#10b981;--warning:#f59e0b;--danger:#ef4444;--shadow:0 1px 3px rgba(0,0,0,.04),0 1px 2px rgba(0,0,0,.06);--shadow-md:0 4px 12px rgba(0,0,0,.05),0 2px 4px rgba(0,0,0,.04);--r:12px;--r-sm:8px}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}}
.container{{max-width:1320px;margin:0 auto;padding:0 24px}}
.hero{{background:var(--surface);border-bottom:1px solid var(--border);padding:48px 0 40px}}
.hero-inner{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:24px}}
.hero-brand{{display:flex;align-items:center;gap:16px}}
.hero-logo{{width:52px;height:52px;background:linear-gradient(135deg,var(--accent),#7c3aed);border-radius:var(--r);display:flex;align-items:center;justify-content:center;font-size:24px;color:#fff;font-weight:800;letter-spacing:-1px;box-shadow:0 4px 12px rgba(79,110,247,.3)}}
.hero-text h1{{font-size:24px;font-weight:700;letter-spacing:-.5px}}
.hero-text p{{font-size:14px;color:var(--text2);margin-top:2px}}
.domain-badge{{display:inline-flex;align-items:center;gap:6px;background:var(--accent-light);color:var(--accent);padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;margin-top:8px}}
.hero-meta{{display:flex;gap:32px;flex-wrap:wrap}}
.hero-stat{{text-align:right}}
.hero-stat-value{{font-size:22px;font-weight:700}}
.hero-stat-label{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:500}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:32px 0}}
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px;box-shadow:var(--shadow);transition:box-shadow .2s,transform .2s}}
.stat-card:hover{{box-shadow:var(--shadow-md);transform:translateY(-2px)}}
.stat-card-icon{{width:40px;height:40px;border-radius:var(--r-sm);display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:16px}}
.stat-card-icon.blue{{background:#eef1fe;color:var(--accent)}}.stat-card-icon.green{{background:#ecfdf5;color:var(--success)}}.stat-card-icon.amber{{background:#fffbeb;color:var(--warning)}}.stat-card-icon.red{{background:#fef2f2;color:var(--danger)}}
.stat-card-value{{font-size:28px;font-weight:700;letter-spacing:-1px}}
.stat-card-label{{font-size:13px;color:var(--muted);margin-top:4px;font-weight:500}}
.panels{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:32px 0}}
@media(max-width:768px){{.panels{{grid-template-columns:1fr}}}}
.panel{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px;box-shadow:var(--shadow)}}
.panel-title{{font-size:15px;font-weight:700;margin-bottom:20px;letter-spacing:-.2px}}
.bar-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
.bar-label{{width:200px;font-size:12px;color:var(--text2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0}}
.bar-track{{flex:1;height:8px;background:var(--border-light);border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,var(--accent),#7c3aed);border-radius:4px;transition:width .6s ease}}
.bar-value{{width:48px;font-size:13px;font-weight:600;text-align:right;flex-shrink:0}}
.status-item{{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light)}}
.status-item:last-child{{border-bottom:none}}
.status-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.status-label{{flex:1;font-size:13px;color:var(--text2)}}
.status-count{{font-size:14px;font-weight:600}}
.content-item{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-light)}}
.content-item:last-child{{border-bottom:none}}
.content-label{{font-size:12px;color:var(--text2);font-family:'Consolas',monospace}}
.content-count{{font-size:13px;font-weight:600}}
.source-split{{display:flex;gap:8px;margin-top:16px}}
.source-block{{flex:1;text-align:center;padding:16px;border-radius:var(--r-sm);background:var(--bg)}}
.source-block-value{{font-size:22px;font-weight:700}}
.source-block-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-top:4px;font-weight:500}}
.table-container{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);overflow:hidden;margin:32px 0}}
.table-toolbar{{padding:16px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}}
.search-box{{display:flex;align-items:center;gap:8px;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px 14px;width:320px;max-width:100%;transition:border-color .2s}}
.search-box:focus-within{{border-color:var(--accent)}}
.search-box input{{border:none;outline:none;background:transparent;font-size:13px;font-family:'Inter',sans-serif;color:var(--text);width:100%}}
.search-box input::placeholder{{color:var(--muted)}}
.table-count{{font-size:13px;color:var(--muted);font-weight:500}}
.table-scroll{{overflow-x:auto;max-height:600px;overflow-y:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
thead{{position:sticky;top:0;z-index:10}}
thead th{{background:var(--bg);padding:12px 16px;text-align:left;font-weight:600;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border);cursor:pointer;user-select:none;white-space:nowrap}}
thead th:hover{{color:var(--text)}}
tbody tr{{border-bottom:1px solid var(--border-light);transition:background .15s}}
tbody tr:hover{{background:#f8f9ff}}
tbody td{{padding:10px 16px;color:var(--text2);white-space:nowrap}}
.cell-num{{color:var(--muted);font-size:12px;width:50px}}
.cell-url{{max-width:350px;overflow:hidden;text-overflow:ellipsis}}
.cell-url a{{color:var(--accent);text-decoration:none;font-weight:500}}
.cell-url a:hover{{text-decoration:underline}}
.cell-domain{{font-weight:500;color:var(--text)}}
.cell-path{{font-family:'Consolas',monospace;font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis}}
.cell-status{{font-weight:600;font-size:12px}}
.status-2xx{{color:var(--success)}}.status-3xx{{color:var(--warning)}}.status-4xx{{color:var(--danger)}}.status-5xx{{color:#dc2626}}
.cell-type{{font-family:'Consolas',monospace;font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis}}
.source-badge{{display:inline-flex;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:.2px}}
.badge-crawler{{background:#eef1fe;color:var(--accent)}}.badge-har{{background:#ecfdf5;color:var(--success)}}
.footer{{text-align:center;padding:40px 0;color:var(--muted);font-size:13px}}
.footer-brand{{font-weight:700;color:var(--text2)}}
.section-header{{margin-bottom:20px}}.section-title{{font-size:18px;font-weight:700;letter-spacing:-.3px}}.section-subtitle{{font-size:13px;color:var(--muted)}}
::-webkit-scrollbar{{width:6px;height:6px}}::-webkit-scrollbar-track{{background:transparent}}::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}::-webkit-scrollbar-thumb:hover{{background:var(--muted)}}
</style>
</head>
<body>

<header class="hero">
<div class="container">
<div class="hero-inner">
<div class="hero-brand">
<div class="hero-logo">CK</div>
<div class="hero-text">
<h1>CrawlKit Report</h1>
<p>Universal Web Crawler &amp; Asset Enumerator</p>
<div class="domain-badge"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 010 20M12 2a15 15 0 000 20M2 12h20"/></svg> {self.target_domain}</div>
</div>
</div>
<div class="hero-meta">
<div class="hero-stat"><div class="hero-stat-value">{total_urls:,}</div><div class="hero-stat-label">Total URLs</div></div>
<div class="hero-stat"><div class="hero-stat-value">{total_domains}</div><div class="hero-stat-label">Domains</div></div>
<div class="hero-stat"><div class="hero-stat-value">{pages_crawled}</div><div class="hero-stat-label">Pages Crawled</div></div>
</div>
</div>
</div>
</header>

<main class="container">

<div class="stats-grid">
<div class="stat-card"><div class="stat-card-icon blue"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg></div><div class="stat-card-value">{total_urls:,}</div><div class="stat-card-label">Total URLs Discovered</div></div>
<div class="stat-card"><div class="stat-card-icon green"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20"/></svg></div><div class="stat-card-value">{total_domains}</div><div class="stat-card-label">Unique Domains &amp; Subdomains</div></div>
<div class="stat-card"><div class="stat-card-icon amber"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></div><div class="stat-card-value">{crawler_count:,}</div><div class="stat-card-label">From Web Crawler</div></div>
<div class="stat-card"><div class="stat-card-icon red"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg></div><div class="stat-card-value">{har_count:,}</div><div class="stat-card-label">From HAR File</div></div>
</div>

<div class="panels">
<div class="panel">
<div class="panel-title">Domain &amp; Subdomain Breakdown</div>
{domain_bars}
</div>
<div style="display:flex;flex-direction:column;gap:16px">
<div class="panel" style="flex:1">
<div class="panel-title">Status Code Distribution</div>
{status_html}
</div>
<div class="panel" style="flex:1">
<div class="panel-title">Data Source Split</div>
<div class="source-split">
<div class="source-block"><div class="source-block-value">{crawler_count:,}</div><div class="source-block-label">Web Crawler</div></div>
<div class="source-block"><div class="source-block-value">{har_count:,}</div><div class="source-block-label">HAR File</div></div>
</div>
</div>
</div>
</div>

<div class="panels" style="grid-template-columns:1fr">
<div class="panel">
<div class="panel-title">Content Type Breakdown</div>
<div style="columns:2;column-gap:32px">{content_html}</div>
</div>
</div>

<div class="table-container">
<div class="table-toolbar">
<div class="search-box">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;color:var(--muted)"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
<input type="text" id="searchInput" placeholder="Search URLs, domains, paths..." oninput="filterTable()">
</div>
<div class="table-count" id="tableCount">Showing {total_urls:,} results</div>
</div>
<div class="table-scroll">
<table id="urlTable">
<thead><tr>
<th onclick="sortTable(0)">#</th>
<th onclick="sortTable(1)">URL</th>
<th onclick="sortTable(2)">Domain</th>
<th onclick="sortTable(3)">Path</th>
<th onclick="sortTable(4)">Status</th>
<th onclick="sortTable(5)">Content Type</th>
<th onclick="sortTable(6)">Source</th>
</tr></thead>
<tbody id="urlTableBody">
{rows}
</tbody>
</table>
</div>
</div>

</main>

<footer class="footer">
<p><span class="footer-brand">CrawlKit</span> - Universal Web Crawler &amp; Asset Enumerator</p>
<p style="margin-top:4px">Report generated on {timestamp}</p>
</footer>

<script>
function filterTable(){{const q=document.getElementById('searchInput').value.toLowerCase();const rows=document.querySelectorAll('#urlTableBody tr');let v=0;rows.forEach(r=>{{const t=r.textContent.toLowerCase();const s=t.includes(q);r.style.display=s?'':'none';if(s)v++}});document.getElementById('tableCount').textContent='Showing '+v.toLocaleString()+' results'}}
let sd={{}};function sortTable(c){{const tb=document.getElementById('urlTableBody');const rows=Array.from(tb.querySelectorAll('tr'));sd[c]=!sd[c];const d=sd[c]?1:-1;rows.sort((a,b)=>{{const at=a.children[c]?.textContent.trim()||'';const bt=b.children[c]?.textContent.trim()||'';const an=parseFloat(at);const bn=parseFloat(bt);if(!isNaN(an)&&!isNaN(bn))return(an-bn)*d;return at.localeCompare(bt)*d}});rows.forEach(r=>tb.appendChild(r))}}
</script>
</body>
</html>'''

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        cprint(f"\033[1;32m  [+] Saved: \033[0;37m{filename}\033[0m")
        cprint(f"\033[0;37m  URLs    : \033[1;37m{total_urls}\033[0m")
        cprint(f"\033[0;37m  Domains : \033[1;37m{total_domains}\033[0m")
        cprint(f"\033[1;36m{'=' * 60}\033[0m")
        return filename


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog='crawlkit',
        description='CrawlKit - Universal Web Crawler & Asset Enumerator',
        epilog='Example: python crawlkit.py -u https://www.wickes.co.uk -har www.wickes.co.uk.har -m 2000 -o wickes_report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('-u', '--url', required=True, help='Target URL to crawl (e.g., https://www.wickes.co.uk)')
    parser.add_argument('-har', '--har', default=None, help='Path to HAR file for additional URL extraction')
    parser.add_argument('-m', '--max-pages', type=int, default=2000, help='Maximum pages to crawl (default: 2000)')
    parser.add_argument('-o', '--output', default=None, help='Output filename prefix (default: based on domain)')
    parser.add_argument('-d', '--delay', type=float, default=0.3, help='Delay between requests in seconds (default: 0.3)')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip web crawling, only parse HAR file')
    parser.add_argument('-v', '--version', action='version', version=f'CrawlKit v{__version__}')

    args = parser.parse_args()

    # Print banner
    cprint(BANNER.format(version=__version__))

    start_url = args.url.rstrip('/')
    kit = CrawlKit(start_url)
    output = args.output or kit.target_domain.replace('.', '_') + '_crawlkit_report'

    # Config summary
    cprint(f"\033[1;36m{'=' * 60}\033[0m")
    cprint(f"\033[1;37m  CONFIGURATION\033[0m")
    cprint(f"\033[1;36m{'=' * 60}\033[0m")
    cprint(f"\033[0;37m  Target URL : \033[1;32m{start_url}\033[0m")
    cprint(f"\033[0;37m  Domain     : \033[1;32m{kit.target_domain}\033[0m")
    cprint(f"\033[0;37m  HAR File   : \033[1;32m{args.har or 'None'}\033[0m")
    cprint(f"\033[0;37m  Max Pages  : \033[1;32m{args.max_pages}\033[0m")
    cprint(f"\033[0;37m  Delay      : \033[1;32m{args.delay}s\033[0m")
    cprint(f"\033[0;37m  Output     : \033[1;32m{output}\033[0m")
    cprint(f"\033[0;37m  Skip Crawl : \033[1;32m{args.skip_crawl}\033[0m")
    cprint(f"\033[1;36m{'=' * 60}\033[0m\n")

    # Step 1: Web Crawl
    if not args.skip_crawl:
        kit.crawl(max_pages=args.max_pages, delay=args.delay)
    else:
        cprint(f"\n\033[1;33m  >> Skipping web crawling (--skip-crawl)\033[0m\n")

    # Step 2: HAR
    if args.har:
        kit.parse_har(args.har)

    # Check
    if not kit.results:
        cprint(f"\n\033[1;31m  [!] No URLs found! Nothing to report.\033[0m")
        cprint(f"\033[0;37m  - Check the URL is correct\033[0m")
        cprint(f"\033[0;37m  - Provide a HAR file with -har\033[0m")
        cprint(f"\033[0;37m  - Increase -m (max pages)\033[0m\n")
        sys.exit(1)

    # Step 3: Reports
    excel_file = kit.save_excel(output)
    html_file = kit.save_html(output)

    # Done
    cprint(f"\n\033[1;36m{'=' * 60}\033[0m")
    cprint(f"\033[1;32m  [+] CRAWLKIT - ALL DONE!\033[0m")
    cprint(f"\033[1;36m{'=' * 60}\033[0m")
    cprint(f"\033[0;37m  Total URLs    : \033[1;37m{len(kit.results):,}\033[0m")
    cprint(f"\033[0;37m  Domains Found : \033[1;37m{len(kit.all_domains)}\033[0m")
    if excel_file:
        cprint(f"\033[0;37m  Excel Report  : \033[1;32m{excel_file}\033[0m")
    if html_file:
        cprint(f"\033[0;37m  HTML Report   : \033[1;32m{html_file}\033[0m")
    cprint(f"\033[1;36m{'=' * 60}\033[0m\n")

    # Print top domains
    cprint(f"\033[1;37m  TOP DOMAINS/SUBDOMAINS:\033[0m")
    domain_counts = Counter(r['Domain/Subdomain'] for r in kit.results if r.get('Domain/Subdomain'))
    for i, (d, c) in enumerate(domain_counts.most_common(15)):
        cprint(f"  \033[0;36m{i+1:3d}.\033[0m {d:50s} : {c:5d} URLs")
    cprint("")


if __name__ == '__main__':
    main()
