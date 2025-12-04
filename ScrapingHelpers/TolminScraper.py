import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_post_urls():
    base_url = "https://www.pdtolmin.si/odseki/grstolmin?start={}"
    post_urls = []
    start = 0
    step = 11

    max_start = 132 

    print("Phase 1: Collecting post URLs...")

    while start < max_start:
        url = base_url.format(start)
        print(f"Scanning page: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all articles on the page
            articles = soup.find_all('article', class_='uk-article')
            
            if not articles:
                print("No articles found on this page. Stopping.")
                break
            
            new_urls_found = False
            for article in articles:
                # Find the title link
                title_tag = article.find('h1', class_='uk-article-title')
                if title_tag:
                    a_tag = title_tag.find('a')
                    if a_tag and a_tag.get('href'):
                        full_url = "https://www.pdtolmin.si" + a_tag.get('href')
                        if full_url not in post_urls:
                            post_urls.append(full_url)
                            new_urls_found = True
            
            if not new_urls_found:
                print("No new URLs found on this page. Stopping.")
                break
                
            start += step
            time.sleep(0.5) # Be polite
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            break
            
    print(f"Found {len(post_urls)} unique post URLs.")
    return post_urls

def scrape_post(url):
    print(f"Scraping post: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article = soup.find('article', class_='uk-article')
        if not article:
            print(f"No article content found for {url}")
            return None
            
        # Extract Title
        title_tag = article.find('h1', class_='uk-article-title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract Date
        date_text = ""
        meta_tag = article.find('p', class_='uk-article-meta')
        if meta_tag:
            time_tag = meta_tag.find('time')
            if time_tag:
                if time_tag.has_attr('datetime'):
                    date_text = time_tag['datetime']
                else:
                    date_text = time_tag.get_text(strip=True)
        
        # Extract Content
        # We want to get text from the article, but exclude title, meta, and footer links
        content_parts = []
        
        # Iterate over children of article
        for child in article.children:
            if child.name == 'h1' and 'uk-article-title' in child.get('class', []):
                continue
            if child.name == 'p' and 'uk-article-meta' in child.get('class', []):
                continue
            if child.name == 'ul' and 'uk-pagination' in child.get('class', []):
                continue
            
            # Check for the print/email paragraph at the bottom
            if child.name == 'p':
                if child.find('a', title=lambda x: x and 'Tiskanje prispevka' in x):
                    continue
            
            if child.name in ['p', 'div']:
                text = child.get_text(separator='\n', strip=True)
                if text:
                    content_parts.append(text)
            elif isinstance(child, str) and child.strip():
                content_parts.append(child.strip())
                
        full_text = "\n\n".join(content_parts)
        
        # Combine title and text
        final_post_text = f"{title}\n\n{full_text}"
        
        return {
            'url': url,
            'date': date_text,
            'post_text': final_post_text
        }

    except Exception as e:
        print(f"Error scraping post {url}: {e}")
        return None

def main():
    # Phase 1: Get all URLs
    urls = get_post_urls()
    
    # Phase 2: Scrape each post
    posts_data = []
    print("Phase 2: Scraping individual posts...")
    
    for i, url in enumerate(urls):
        print(f"Processing {i+1}/{len(urls)}...")
        post_data = scrape_post(url)
        if post_data:
            posts_data.append(post_data)
        time.sleep(0.5) # Be polite
        
    if posts_data:
        df = pd.DataFrame(posts_data)
        output_file = 'posts_grs_tolmin.xlsx'
        df.to_excel(output_file, index=False)
        print(f"Successfully saved {len(posts_data)} posts to {output_file}")
    else:
        print("No posts collected.")

if __name__ == "__main__":
    main()
