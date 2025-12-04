import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

def scrape_grs_trzic():
    site_name = "grs-tržič"
    base_url = "https://www.grs-trzic.si/novice.php?pid={}"
    max_pid = 529
    posts = []

    print(f"Starting scraper for {site_name}...")

    for pid in range(max_pid, 0, -1):
        url = base_url.format(pid)
        print(f"Scraping {url}...")
        
        try:
            response = requests.get(url)
            if response.status_code == 404:
                print(f"Page not found: {url}")
                continue
            
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selectors for GRS Tržič
            # Find the main content cell (td class="stolpec" containing h1)
            content_td = None
            for td in soup.find_all('td', class_='stolpec'):
                if td.find('h1'):
                    content_td = td
                    break
            
            if not content_td:
                print(f"No content container found for pid {pid}")
                continue

            # Extract Title
            title_tag = content_td.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Extract Date
            date_text = ""
            # Look for the div containing author info: Objavil/a: ...
            author_div = content_td.find(lambda tag: tag.name == 'div' and 'Objavil/a' in tag.get_text())
            if author_div:
                # The date is typically in the second <b> tag
                # Example: Objavil/a: ... <b>nedelja, 22. december 2024</b> ...
                b_tags = author_div.find_all('b')
                if len(b_tags) >= 2:
                    date_text = b_tags[1].get_text(strip=True)

            # Extract Content
            # Content starts after <div id='pikice'>
            content_parts = []
            pikice_div = content_td.find('div', id='pikice')
            
            if pikice_div:
                curr = pikice_div.next_sibling
                while curr:
                    # Stop if we hit the gallery or social media section
                    if curr.name == 'div' and 'rounded_frame' in curr.get('class', []):
                        if 'Fotogalerija' in curr.get_text():
                            break
                    
                    # Sometimes the gallery div is inside a p tag
                    if curr.name == 'p':
                        if 'Fotogalerija' in curr.get_text():
                            break
                        text = curr.get_text(strip=True)
                        if text:
                            content_parts.append(text)
                    elif isinstance(curr, str): # NavigableString
                        text = curr.strip()
                        if text:
                            content_parts.append(text)
                    
                    curr = curr.next_sibling
                
                full_text = "\n\n".join(content_parts)
            else:
                # Fallback if pikice not found
                full_text = ""

            # Combine title and text as requested "post text"
            final_post_text = f"{title}\n\n{full_text}"

            posts.append({
                'pid': pid,
                'date': date_text,
                'post_text': final_post_text,
                'url': url
            })
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        time.sleep(0.2)

    if posts:
        df = pd.DataFrame(posts)
        output_file = f'posts_{site_name}.xlsx'
        df.to_excel(output_file, index=False)
        print(f"Successfully saved {len(posts)} posts to {output_file}")
    else:
        print(f"No posts found for {site_name}.")

if __name__ == "__main__":
    scrape_grs_trzic()
