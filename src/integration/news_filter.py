import requests
import pandas as pd
from datetime import datetime, timedelta

class NewsFilter:
    def __init__(self, api_key, symbols, impact_levels=['high']):
        self.api_key = api_key
        self.symbols = symbols
        self.impact_levels = impact_levels
        self.news_data = None

    def fetch_news(self):
        url = f"https://newsapi.org/v2/everything?q=forex&apiKey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            self.news_data = response.json().get('articles', [])
        else:
            print("Failed to fetch news data.")

    def filter_high_impact_news(self):
        if self.news_data is None:
            self.fetch_news()
        
        filtered_news = []
        for article in self.news_data:
            if any(impact in article['title'].lower() for impact in self.impact_levels):
                filtered_news.append(article)
        
        return filtered_news

    def get_upcoming_news(self, days_ahead=1):
        upcoming_news = []
        today = datetime.now()
        for article in self.filter_high_impact_news():
            news_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
            if today <= news_date <= today + timedelta(days=days_ahead):
                upcoming_news.append(article)
        
        return upcoming_news

    def display_news(self, news_list):
        for news in news_list:
            print(f"Title: {news['title']}")
            print(f"Published At: {news['publishedAt']}")
            print(f"Source: {news['source']['name']}")
            print(f"Link: {news['url']}\n")