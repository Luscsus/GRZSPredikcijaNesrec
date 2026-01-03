from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import time
import pandas as pd
from PIL import Image
import pytesseract
import io
import os


class FacebookScraperPlaywright:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def initialize_browser(self, headless=False, user_data_dir=None):
        self.playwright = sync_playwright().start()
        
        # Launch browser with persistent context if user_data_dir provided
        if user_data_dir:
            # Use persistent context to save login session
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.browser = None  # Not used in persistent context
        else:
            # Regular browser launch
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # Create context with realistic viewport and user agent
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            
            # Create new page
            self.page = self.context.new_page()
        
        # Hide webdriver detection
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    def wait_for_manual_login(self):
        print("log in")

        self.page.goto("https://www.facebook.com/")
        
        input("press enter after login")

    def navigate_to_profile(self, profile_url):
        self.page.goto(profile_url)
        self.page.wait_for_timeout(4000)

    def open_post_filters(self):
        try:
            # Wait for and click the filter button
            filter_button = self.page.locator("//span[contains(text(), 'Filtri')]")
            filter_button.click(timeout=10000)
            self.page.wait_for_timeout(2000)
            print("Opened filter menu")
        except Exception as e:
            print(f"Could not open Filters menu: {e}")

    def open_dropdown(self):
        try:
            # Click the year filter dropdown
            year_button = self.page.locator("//span[contains(text(), 'Leto')]")
            year_button.click(timeout=10000)
            self.page.wait_for_timeout(2000)
            print("Opened year dropdown")
        except Exception as e:
            print(f"Could not open year dropdown: {e}")

    def select_year(self, year):
        try:
            year_button = self.page.locator(f"//span[contains(text(), '{year}')]")
            year_button.click(timeout=10000)
            self.page.wait_for_timeout(3000)
            print(f"Selected year {year}")
        except Exception as e:
            print(f"Year {year} not found: {e}")

    def confirm_year(self):
        try:
            confirm_button = self.page.locator("//span[contains(text(), 'Končano')]").nth(1)
            # Scroll into view and force click
            confirm_button.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)
            confirm_button.click(force=True, timeout=10000)
            self.page.wait_for_timeout(2000)
            print("Confirmed year selection")
        except Exception as e:
            print(f"Could not click confirm: {e}")

    def slow_scroll(self, step=1000):
        self.page.evaluate(f"window.scrollBy(0, {step})")
        self.page.wait_for_timeout(2000)

    def get_post_links(self):
        try:
            # Find all post links - Facebook posts typically have links with /posts/ or /permalink/ in them
            posts_links = self.page.locator("a[href*='/posts/']").all()
            permalink_links = self.page.locator("a[href*='/permalink/']").all()
            permalink_php_links = self.page.locator("a[href*='permalink.php']").all()
            
            # Extract the href attributes
            post_urls = []
            for link in posts_links + permalink_links + permalink_php_links:
                try:
                    href = link.get_attribute('href')
                    if href and ('/posts/' in href or '/permalink/' in href or 'permalink.php' in href):
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = f"https://www.facebook.com{href}"
                        if 'permalink.php' in href:
                            post_urls.append(href)
                        else:
                            # Remove any query parameters for deduplication
                            base_url = href.split('?')[0]
                            if base_url not in post_urls:
                                post_urls.append(base_url)
                except:
                    continue
            
            return post_urls
        except Exception as e:
            print(f"Error getting post links: {e}")
            return []

    def extract_post_content_from_modal(self):
        try:
            self.page.wait_for_timeout(2000)  # Wait for modal to load
        
            Vsebina = ""
            Datum = None
            
            #main_content = self.page.locator("[role='main']")
            selector = "div[data-ad-comet-preview='message']"
            
            elements = []
            
            if not elements:
                elements = self.page.locator(selector).all()
            
            candidates = []
            for el in elements:
                if el.is_visible():
                    text = el.inner_text() # inner_text gets visible text
                    if text and text.strip():
                        candidates.append(text.strip())
            
            if candidates:
                # Filter candidates based on page title
                page_title = self.page.title()
                
                # Remove notification count (e.g. "(1) ")
                import re
                page_title = re.sub(r'^\(\d+\)\s+', '', page_title)
                
                clean_title = page_title.split(" | ")[0].replace("...", "").strip() # Remove " | Facebook" and "..."
                
                print(f"Page title: {clean_title}")
                
                # Helper function to remove emojis and normalize text
                def remove_emojis(text):
                    # Remove emojis using regex pattern
                    emoji_pattern = re.compile("["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        u"\U00002702-\U000027B0"
                        u"\U000024C2-\U0001F251"
                        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                        u"\U00002600-\U000027BF"  # Miscellaneous Symbols
                        "]+", flags=re.UNICODE)
                    return emoji_pattern.sub(r'', text).strip()
                
                # Split title by " - " to handle "Author - Content" format
                # We check if any significant part of the title is present in the candidate text
                title_parts = [p.strip() for p in clean_title.split("-") if len(p.strip()) > 3]
                if not title_parts:
                    title_parts = [clean_title]
                
                valid_candidates = []
                for cand in candidates:
                    is_match = False
                    # Normalize candidate text for comparison (replace newlines with spaces)
                    cand_normalized = " ".join(cand.split())
                    cand_no_emoji = remove_emojis(cand_normalized)
                    
                    print("kandidat:", cand[:50])
                    print("naslov:", title_parts)
                    
                    # Check if any title part is in the candidate text
                    for part in title_parts:
                        part_normalized = " ".join(part.split())
                        part_no_emoji = remove_emojis(part_normalized)
                        
                        # Try matching with and without emojis
                        if (part_normalized in cand_normalized or 
                            part_no_emoji in cand_no_emoji or
                            (len(part_no_emoji) > 5 and part_no_emoji in cand_normalized)):
                            is_match = True
                            break
                    
                    # Also check if candidate is in title (for short posts)
                    if not is_match:
                        clean_title_normalized = " ".join(clean_title.split())
                        clean_title_no_emoji = remove_emojis(clean_title_normalized)
                        
                        if (cand_normalized in clean_title_normalized or
                            cand_no_emoji in clean_title_no_emoji or
                            (len(cand_no_emoji) > 5 and cand_no_emoji in clean_title_normalized)):
                            is_match = True
                        
                    if is_match:
                        valid_candidates.append(cand)
                
                if valid_candidates:
                    # Sort by length descending
                    valid_candidates.sort(key=len, reverse=True)
                    Vsebina = valid_candidates[0]
                    print(f"Found {len(valid_candidates)} matching text blocks. Selected: {Vsebina[:50]}...")
                else:
                    print("No text blocks matched the page title.")
                    Vsebina = ""
            
            self.page.wait_for_timeout(1000)
            
            # Take a screenshot of the modal
            screenshot_bytes = self.page.screenshot()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Use OCR to extract text from the image
            ocr_text = pytesseract.image_to_string(image, lang='eng')
            # Look for date patterns in the OCR text
            import re
            # Pattern for various date formats
            date_patterns = [
                r'\d{1,2}[.,]\s+(?:januar|februar|marec|april|maj|junij|julij|avgust|september|oktober|november|december)\s+\d{4}',
                r'\d{1,2}[.,]\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
                r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, ocr_text, re.IGNORECASE)
                if match:
                    Datum = match.group(0)
                    print(f"Extracted date from OCR: {Datum}")
                    break
            
            return {
                "Datum": Datum,
                "Vsebina": Vsebina
            }
            
        except Exception as e:
            print(f"Error extracting post content from modal: {e}")
            return {
                "Datum": None,
                "Vsebina": ""
            }

    def close_post_modal(self):
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            
            # if Escape didn't work, try clicking close button
            try:
                close_button = self.page.locator("div[aria-label='Close'], div[aria-label='Zapri']").first
                if close_button.is_visible(timeout=1000):
                    close_button.click()
                    self.page.wait_for_timeout(1000)
            except:
                pass
                
        except Exception as e:
            print(f"Error closing modal: {e}")

    def collect_permalinks_while_scrolling(self, max_scrolls=20, stop_after_no_new=10):
        all_permalinks = set()
        scrolls_without_new = 0
        
        print(f"Collecting permalinks with max {max_scrolls} scrolls...")
        print(f"Will stop early if no new permalinks found in {stop_after_no_new} consecutive scrolls")
        
        for scroll_count in range(max_scrolls):
            print(f"  Scroll {scroll_count + 1}/{max_scrolls}...")
            
            # Get post links from current view
            post_links = self.get_post_links()
            
            # Track new links added in this iteration
            new_links_count = 0
            
            # Add new links to the set (only if they don't already exist)
            for link in post_links:
                if link not in all_permalinks:
                    all_permalinks.add(link)
                    new_links_count += 1
            
            print(f"    New permalinks found: {new_links_count}")
            print(f"    Total unique permalinks collected: {len(all_permalinks)}")
            
            # Check if we found new permalinks
            if new_links_count == 0:
                scrolls_without_new += 1
                print(f"No new permalinks ({scrolls_without_new}/{stop_after_no_new} scrolls without new)")
                
                # Stop if we haven't found new permalinks in the last N scrolls
                if scrolls_without_new >= stop_after_no_new:
                    print(f"\n Stopping early: No new permalinks in last {stop_after_no_new} scrolls")
                    break
            else:
                # Reset counter if we found new permalinks
                scrolls_without_new = 0
            
            # Scroll to load more content
            self.slow_scroll()
        
        return list(all_permalinks)
    
    def save_permalinks_to_file(self, permalinks, username):
        filename = f"permalinks_{username}.txt"
        filepath = os.path.join("permalinks", filename)
        
        # Ensure directory exists
        os.makedirs("permalinks", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            for link in permalinks:
                f.write(link + "\n")
        print(f"✓ Saved {len(permalinks)} permalinks → {filepath}")
        return filename
    
    def load_permalinks_from_file(self, filename):
        try:
            # Construct path if not already provided
            if os.path.dirname(filename) == "":
                filepath = os.path.join("permalinks", filename)
            else:
                filepath = filename
                
            with open(filepath, "r", encoding="utf-8") as f:
                permalinks = [line.strip() for line in f if line.strip()]
            print(f"✓ Loaded {len(permalinks)} permalinks from {filepath}")
            return permalinks
        except Exception as e:
            print(f"Error loading permalinks: {e}")
            return []
    
    def extract_posts_from_permalinks(self, permalinks):
        posts_data = []
        total = len(permalinks)
        
        print(f"\nExtracting content from {total} permalinks...")
        
        for idx, post_url in enumerate(permalinks):
            try:
                print(f"  Processing post {idx + 1}/{total}...")
                
                # Clean URL to remove comment_id and other parameters if needed
                if "comment_id=" in post_url:
                    import re
                    # Remove comment_id parameter
                    post_url = re.sub(r'&comment_id=\d+', '', post_url)
                    post_url = re.sub(r'\?comment_id=\d+&?', '?', post_url)
                
                # Navigate to the post
                try:
                    self.page.goto(post_url, timeout=30000)
                except Exception as nav_error:
                    print(f"    Navigation error: {nav_error}")
                    raise nav_error

                self.page.wait_for_timeout(2000)
                
                # Extract content from the opened post
                post_data = self.extract_post_content_from_modal()
                
                if post_data["Vsebina"] or post_data["Datum"]:
                    posts_data.append(post_data)
                    print(f"    ✓ Extracted ({len(posts_data)} successful so far)")
                else:
                    print(f"    ✗ No content found")
                
            except Exception as e:
                print(f"    Error processing post {idx + 1}: {e}")
                # Try to completely restart browser and navigate to the URL that failed
                self.recover_page(url=post_url, user_data_dir="./facebook_browser_data")
                
                # Retry extraction after recovery
                try:
                    print(f"    Retrying post {idx + 1} after browser restart...")
                    post_data = self.extract_post_content_from_modal()
                    
                    if post_data["Vsebina"] or post_data["Datum"]:
                        posts_data.append(post_data)
                        print(f"    ✓ Extracted after restart ({len(posts_data)} successful so far)")
                    else:
                        print(f"    ✗ No content found after restart")
                except Exception as retry_error:
                    print(f"    ✗ Retry failed: {retry_error}")
        
        return posts_data

    def remove_duplicates(self, data_list):
        seen = set()
        unique_data = []
        for data in data_list:
            data_tuple = tuple(data.items())
            if data_tuple not in seen:
                seen.add(data_tuple)
                unique_data.append(data)
        return unique_data

    def collect_user_permalinks(self, username, profile_url, max_scrolls=200):
        print(f"\n========== COLLECTING PERMALINKS FOR USER: {username} ==========")
        
        # Navigate to the profile
        self.navigate_to_profile(profile_url)
        
        # Set filter to 2024
        print(f"\n--- Setting initial year filter to 2024 ---")
        self.open_post_filters()
        self.open_dropdown()
        self.select_year(2024)
        self.confirm_year()
        
        # Collect all permalinks by scrolling continuously
        print(f"\n--- Collecting All Permalinks (Max {max_scrolls} scrolls) ---")
        all_permalinks = self.collect_permalinks_while_scrolling(max_scrolls)
        
        # Save all permalinks to file
        permalinks_file = self.save_permalinks_to_file(all_permalinks, username)
        
        print(f"\n✓ Total unique permalinks collected for {username}: {len(all_permalinks)}")
        
        return all_permalinks

    def scrape_user_posts_from_permalinks(self, username, permalinks):
        print(f"\n========== EXTRACTING POSTS FOR USER: {username} ==========")
        
        # Remove duplicate permalinks
        original_count = len(permalinks)
        permalinks = list(set(permalinks))  # Convert to set and back to list to remove duplicates
        duplicates_removed = original_count - len(permalinks)
        
        if duplicates_removed > 0:
            print(f"\n⚠ Removed {duplicates_removed} duplicate permalink(s)")
        print(f"✓ Processing {len(permalinks)} unique permalinks")
        
        # Extract content from each permalink
        print(f"\n--- Extracting Post Content from {len(permalinks)} Permalinks ---")
        user_posts = self.extract_posts_from_permalinks(permalinks)
        
        # Remove duplicates
        user_posts = self.remove_duplicates(user_posts)
        
        print(f"\nTotal unique posts extracted for {username}: {len(user_posts)}")
        
        return user_posts

    def save_to_excel(self, posts, username):
        if not posts:
            print(f"No posts found for {username}. Skipping Excel generation.")
            return

        filename = f"facebook_posts_{username}.xlsx"
        filepath = os.path.join("facebookPosts", filename)
        
        # Ensure directory exists
        os.makedirs("facebookPosts", exist_ok=True)
        
        # Convert posts to DataFrame
        df = pd.DataFrame(posts, columns=["Datum", "Vsebina"])
        
        # Save to Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        print(f"✓ Saved {len(posts)} posts for {username} → {filepath}")

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def recover_page(self, url=None, user_data_dir=None):
        try:
            print("\n" + "="*60)
            print("BROWSER FAILURE DETECTED - RESTARTING COMPLETELY")
            print("="*60)
            
            # Close everything
            print("Closing existing browser session...")
            try:
                if self.page:
                    self.page.close()
            except:
                pass
            
            try:
                if self.context:
                    self.context.close()
            except:
                pass
            
            try:
                if self.browser:
                    self.browser.close()
            except:
                pass
                
            try:
                if self.playwright:
                    self.playwright.stop()
            except:
                pass
            
            # Wait a bit for cleanup
            time.sleep(2)
            
            # Reinitialize completely
            print("Reinitializing browser from scratch...")
            self.initialize_browser(headless=False, user_data_dir=user_data_dir)
            
            print("✓ Browser restarted successfully")
            
            # Navigate to the URL if provided
            if url:
                print(f"Navigating to: {url}")
                self.page.goto(url, timeout=30000)
                self.page.wait_for_timeout(3000)
                print("✓ Successfully navigated to URL after restart")
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"✗ Complete restart failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    scraper = FacebookScraperPlaywright()

    try:
        print("\nWhich phase would you like to run?")
        print("1 - Phase 1 only (Collect permalinks)")
        print("2 - Phase 2 only (Extract post content)")
        print("3 - Both phases (Complete scraping)")
        
        phase_choice = input("\nEnter your choice (1/2/3): ")

        # Validate input
        if phase_choice not in ['1', '2', '3']:
            print("Invalid choice. Exiting...")
            exit(1)
        
        run_phase1 = phase_choice in ['1', '3']
        run_phase2 = phase_choice in ['2', '3']
        
        scraper.initialize_browser(headless=False, user_data_dir="./facebook_browser_data")
        
        scraper.wait_for_manual_login()
        
        users = [
            # {
            #     "username": "grs.bohinj",
            #     "url": "https://www.facebook.com/grs.bohinj"
            # },
            # {
            #     "username": "grskamnik",
            #     "url": "https://www.facebook.com/grskamnik"
            # }, 
            # {
            #     "username": "GRSLjubljana",
            #     "url": "https://www.facebook.com/GRSLjubljana"
            # },
            # {
            #     "username": "skofja-loka",
            #     "url": "https://www.facebook.com/profile.php?id=100063451581084"
            # },
            # {
            #     "username": "jesenice",
            #     "url": "https://www.facebook.com/profile.php?id=100083151739889"
            # },
            # {
            #     "username": "GRSRadovljica",
            #     "url": "https://www.facebook.com/GRSRadovljica"
            # },
            # {
            #     "username": "kranj",
            #     "url": "https://www.facebook.com/profile.php?id=100063951316700"
            # },
            # {
            #     "username": "grsmaribor",
            #     "url": "https://www.facebook.com/grsmaribor"
            # },
            # {
            #     "username": "jezersko",
            #     "url": "https://www.facebook.com/profile.php?id=100064582726882"
            # },
            #             {
            #     "username": "tržič",
            #     "url": "https://www.facebook.com/profile.php?id=61555294874786"
            # },
            # {
            #     "username": "koroška",
            #     "url": "https://www.facebook.com/profile.php?id=61566762417019"
            # },
            # {
            #     "username": "grzs",
            #     "url": "https://www.facebook.com/profile.php?id=100064380982130"
            # }
        ]
        
        if run_phase1:
            print("\n" + "="*60)
            print("PHASE 1: COLLECTING PERMALINKS FOR ALL USERS")
            print("="*60)
            
            for user in users:
                username = user["username"]
                profile_url = user["url"]
                
                # Collect permalinks for this user (saves to file automatically)
                permalinks = scraper.collect_user_permalinks(
                    username=username,
                    profile_url=profile_url,
                    max_scrolls=500
                )
            
            print("\n" + "="*60)
            print("✓ PHASE 1 COMPLETE: All permalinks collected and saved to files!")
            print("="*60)
        
        if run_phase2:
            print("\n" + "="*60)
            print("PHASE 2: EXTRACTING POST CONTENT FOR ALL USERS")
            print("="*60)
            
            for user in users:
                username = user["username"]
                
                # Load permalinks from file
                permalinks_file = f"permalinks_{username}.txt"
                permalinks = scraper.load_permalinks_from_file(permalinks_file)
                
                if not permalinks:
                    print(f"\n⚠ No permalinks found for {username}, skipping...")
                    continue
                
                #permalinks = permalinks[:5]
                
                # Extract posts from permalinks
                posts = scraper.scrape_user_posts_from_permalinks(
                    username=username,
                    permalinks=permalinks
                )
                
                # Save to Excel
                scraper.save_to_excel(posts, username)
                
                print(f"\nCompleted scraping for {username}!")
            
            print("\n" + "="*60)
            print("PHASE 2 COMPLETE: All posts extracted and saved!")
            print("="*60)

        # Final summary
        if run_phase1 and run_phase2:
            print("\n" + "="*60)
            print("ALL PHASES COMPLETE: All users scraped successfully!")
            print("="*60)
        elif run_phase1:
            print("\nPhase 1 completed. Run with option 2 to extract post content.")
        elif run_phase2:
            print("\nPhase 2 completed. All post content extracted.")

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        scraper.close()
