import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

def scrape_grs_celje():
    site_name = "grs-celje"
    base_url = "https://www.grs-celje.si/novice.php?pid={}"
    max_pid = 76
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
            
            # Selectors for GRS Celje
            article = soup.find('article', class_='post')
            if not article:
                print(f"No article found for pid {pid}")
                continue

            # Extract Date
            date_text = ""
            h4_tags = article.find_all('h4')
            for h4 in h4_tags:
                # Check if this h4 has the calendar icon
                if h4.find('i', class_='fa-calendar'):
                    parts = []
                    user_icon_found = False
                    for content in h4.contents:
                        # Stop if we hit the user icon or the eye icon (views)
                        if hasattr(content, 'get') and content.get('class') and ('fa-user-circle' in content.get('class') or 'fa-eye' in content.get('class')):
                            user_icon_found = True
                            break
                        
                        # Skip the calendar icon itself
                        if hasattr(content, 'get') and content.get('class') and 'fa-calendar' in content.get('class'):
                            continue
                            
                        if isinstance(content, str):
                            parts.append(content)
                        elif content.name == 'i': # Skip other icons if any
                            continue
                            
                    date_text = "".join(parts).strip().rstrip(',')
                    break
            
            # Extract Title
            title_tag = article.find('h1', class_='entry_title')
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Extract Content
            # We look for divs with text-align:justify which seem to hold the content
            content_parts = []
            content_divs = article.find_all('div', style=lambda x: x and 'text-align:justify' in x.replace(' ', ''))
            
            if content_divs:
                for div in content_divs:
                    content_parts.append(div.get_text(separator='\n', strip=True))
                full_text = "\n\n".join(content_parts)
            else:
                # Fallback: get all text from article excluding title and metadata
                # Create a copy to not modify the original soup if we were to continue using it (though we aren't)
                article_copy = BeautifulSoup(str(article), 'html.parser')
                
                # Remove title
                t = article_copy.find('h1', class_='entry_title')
                if t: t.decompose()
                
                # Remove metadata h4
                h4s = article_copy.find_all('h4')
                for h in h4s:
                    if h.find('i', class_='fa-calendar'):
                        h.decompose()
                
                # Remove figure (images)
                for f in article_copy.find_all('figure'):
                    f.decompose()
                    
                full_text = article_copy.get_text(separator='\n', strip=True)

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
    scrape_grs_celje()
