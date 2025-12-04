import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin

def scrape_skofja_loka():
    start_url = "https://grs-skofjaloka.com/novice/x7d8egh79ivnxo8ywetn2gyjetwh2j"
    base_url = "https://grs-skofjaloka.com"
    
    current_url = start_url
    posts = []
    
    print("Starting scraper for GRS Škofja Loka...")

    while current_url:
        print(f"Scraping {current_url}...")
        try:
            response = requests.get(current_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract Title
            title_tag = soup.find('h1', class_='entry-title')
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Extract Date
            # Try meta tag first as it is usually cleaner
            date_meta = soup.find('meta', itemprop='datePublished')
            if date_meta:
                date_text = date_meta.get('content')
            else:
                # Fallback to time tag
                time_tag = soup.find('time', class_='dt-published')
                date_text = time_tag.get_text(strip=True) if time_tag else "No Date"
            
            # Extract Content
            content_div = soup.find('div', class_='sqs-html-content')
            if content_div:
                content_text = content_div.get_text(separator='\n', strip=True)
            else:
                # Fallback to e-content if sqs-html-content is not found
                content_div = soup.find('div', class_='e-content')
                content_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
            
            post_data = {
                'url': current_url,
                'title': title,
                'date': date_text,
                'content': content_text
            }
            
            posts.append(post_data)
            print(f"Collected: {title} ({date_text})")
            
            # Find Next Post
            next_link = soup.find('a', class_='item-pagination-link--next')
            if next_link:
                next_href = next_link.get('href')
                current_url = urljoin(base_url, next_href)
            else:
                print("No next post found. Stopping.")
                current_url = None
                
            # Be polite
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping {current_url}: {e}")
            break

    # Save to Excel
    if posts:
        df = pd.DataFrame(posts)
        output_file = 'posts_grs_skofjaloka.xlsx'
        df.to_excel(output_file, index=False)
        print(f"Scraping finished. Saved {len(posts)} posts to {output_file}")
    else:
        print("No posts found.")

if __name__ == "__main__":
    scrape_skofja_loka()
