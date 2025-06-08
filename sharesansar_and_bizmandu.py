from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import requests
import subprocess
import re
from selenium.webdriver.chrome.options import Options
from datetime import datetime

def sharesansar_news():
    options = Options()
    options.add_argument("--headless")  # Headless mode for GitHub Actions
    options.add_argument("--no-sandbox")  # Required for Docker/Linux environments
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get('https://www.sharesansar.com/category/latest')

    blank_list = []
    total_pages = 4

    for i in range(total_pages):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'newslist'))
            )

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            news_container = soup.find('div', class_='newslist')

            for item in news_container.find_all('div', class_='featured-news-list margin-bottom-15'):
                date_tag = item.find('span', class_='text-org')
                title_a_tag = item.find('a', title=True)
                title_tag = title_a_tag.find('h4', class_='featured-news-title') if title_a_tag else None

                result = {
                    'Published Date': date_tag.text.strip() if date_tag else '',
                    'News': title_tag.text.strip() if title_tag else '',
                    'URL': title_a_tag['href'] if title_a_tag else ''
                }
                blank_list.append(result)

            print(f"Scraped Page {i + 1}")

            if i < total_pages - 1:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, 'Next »'))
                )
                next_button.click()
                time.sleep(2)

        except (NoSuchElementException, TimeoutException):
            print("No more pages or timeout.")
            break
        except Exception as e:
            print(f"Error on page {i + 1}: {e}")
            break

    driver.quit()

    # Create DataFrame
    sharesansar_news_df = pd.DataFrame(blank_list)
    sharesansar_news_df['Published Date'] = pd.to_datetime(
        sharesansar_news_df['Published Date'].str.strip(),
        format='%A, %B %d, %Y',
        errors='coerce'
    )

    today = pd.Timestamp.today().normalize()
    sharesansar_today = sharesansar_news_df[
        sharesansar_news_df['Published Date'].dt.normalize() == today
    ]
    return sharesansar_today




def bizmandu_news():
  # Target URL
  url = 'https://bizmandu.com/content/category/market.html'

  # Send request
  response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
  soup = BeautifulSoup(response.text, 'html.parser')

  # Container for news data
  news_list = []

  # Loop through each news block
  news_blocks = soup.find_all('div', class_='news-title md-title')

  for block in news_blocks:
      try:
          a_tag = block.find('h1', class_='title-lg').find('a')
          title = a_tag.text.strip()
          link = a_tag['href'].strip()

          # Extract date from URL (assumes format like /content/YYYYMMDDHHMMSS.html)
          date_str = link.split('/')[-1].replace('.html', '')[:8]  # Get YYYYMMDD
          formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

          news_list.append({
              'News': title,
              'URL': link,
              'Published Date': formatted_date
          })
      except Exception as e:
          print(f"Skipping a block due to error: {e}")
          continue

  # Convert to DataFrame
  bizmandu_news = pd.DataFrame(news_list)
  bizmandu_news = bizmandu_news[['Published Date', 'News', 'URL']]    # Ensure 'Published Date' is in datetime format
  bizmandu_news['Published Date'] = pd.to_datetime(bizmandu_news['Published Date'], errors='coerce')
  # Filter for today's news
  today = pd.to_datetime(datetime.today().date())
  bizmandu_news_today = bizmandu_news[bizmandu_news['Published Date'].dt.date == today.date()]
  # Select only relevant columns
  bizmandu_news_today = bizmandu_news_today[['Published Date', 'News', 'URL']]
  return bizmandu_news_today


def tomorrow_events():
    # Today's date
    today = pd.to_datetime("today").date()

    # Generate upcoming 5 event dates
    upcoming_event_dates = [today + pd.to_timedelta(i, unit="D") for i in range(1, 3)]

    five_days_events = []

    # Loop over each of the next 5 days
    for date in upcoming_event_dates:
        url = f'https://www.sharesansar.com/events/{date}'
        req = requests.get(url)
        soup = BeautifulSoup(req.content, 'html.parser')

        # Parse events
        for company_event in soup.find_all('div', class_='featured-news-list margin-bottom-15'):
            a_tag = company_event.find('a')

            if a_tag:
                event_url = a_tag['href'].strip()
                event_title = a_tag['title'].strip() if a_tag.has_attr('title') else a_tag.text.strip()

                five_days_events.append({
                    'Upcoming events': event_title,
                    'URL': event_url,
                    'Date': date.isoformat()
                })

    # Convert to DataFrame
    upcoming_events = pd.DataFrame(five_days_events)
    return upcoming_events


def merolagani_announcement():
    # URL of the announcements page
    base_url = "https://merolagani.com"
    url = f"{base_url}/AnnouncementList.aspx"

    # Send a GET request to the website
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }


    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all announcement items
    announcements = []
    announcement_divs = soup.find_all('div', class_='media')

    for div in announcement_divs:
        # Extract date
        date_element = div.find('small', class_='text-muted')
        date = date_element.text.strip() if date_element else 'N/A'
        
        # Extract announcement text
        announcement_element = div.find('div', class_='media-body').find('a')
        announcement = announcement_element.text.strip() if announcement_element else 'N/A'
        
        # Extract announcement URL (from either the icon link or text link)
        url_element = div.find('div', class_='pull-left').find('a')  # The icon link
        if not url_element:
            url_element = div.find('div', class_='media-body').find('a')  # Fallback to text link
            
        relative_url = url_element['href'] if url_element and url_element.has_attr('href') else 'N/A'
        full_url = f"{base_url}{relative_url}" if relative_url != 'N/A' else 'N/A'
        
        announcements.append({
            'Date': date,
            'Announcement': announcement,
            'URL': full_url
        })

    # Create a DataFrame and save to CSV
    merolagani_announcement = pd.DataFrame(announcements)
    merolagani_announcement['Date'] = pd.to_datetime(
        merolagani_announcement['Date'].astype(str).str.strip(),
        format='%b %d, %Y',
        errors='coerce'  # Sets unparseable values to NaT
    )
    today = pd.to_datetime("today").date()
    announcement_today = merolagani_announcement[merolagani_announcement['Date'].dt.date == today]
    return announcement_today
