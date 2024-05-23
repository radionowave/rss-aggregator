import os
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
import gradio as gr

# Створення та підключення до бази даних
def initialize_db():
    if not os.path.exists('news_aggregator.db'):
        conn = sqlite3.connect('news_aggregator.db')
        c = conn.cursor()

        # Таблиця для збереження RSS-джерел
        c.execute('''CREATE TABLE IF NOT EXISTS rss_sources (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )''')

        # Таблиця для збереження шаблонів новинних сайтів
        c.execute('''CREATE TABLE IF NOT EXISTS news_sites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            title_selector TEXT NOT NULL,
            body_selector TEXT NOT NULL,
            link_selector TEXT NOT NULL
        )''')

        conn.commit()
        conn.close()

def fetch_rss_feed(url, num_articles=5):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:num_articles]:
        articles.append({
            "title": entry.title,
            "link": entry.link
        })
    return articles

def fetch_news_site(url, title_selector, body_selector, link_selector, num_articles=5):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = []
    titles = soup.select(title_selector)[:num_articles]
    bodies = soup.select(body_selector)[:num_articles]
    links = soup.select(link_selector)[:num_articles]
    
    for title, body, link in zip(titles, bodies, links):
        articles.append({
            "title": title.get_text(),
            "body": body.get_text(),
            "link": link['href']
        })
    return articles

def get_sources():
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM rss_sources")
    rss_sources = c.fetchall()
    
    c.execute("SELECT * FROM news_sites")
    news_sites = c.fetchall()
    
    conn.close()
    
    return rss_sources, news_sites

def fetch_news(num_articles=5, auto_update=False):
    rss_sources, news_sites = get_sources()
    news = []
    
    for source in rss_sources:
        news.extend(fetch_rss_feed(source[2], num_articles))
    
    for site in news_sites:
        news.extend(fetch_news_site(site[2], site[3], site[4], site[5], num_articles))
    
    return news

def add_rss_source(name, url):
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO rss_sources (name, url) VALUES (?, ?)", (name, url))
    
    conn.commit()
    conn.close()
    
    return "RSS джерело додано!"

def add_news_site(name, url, title_selector, body_selector, link_selector):
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO news_sites (name, url, title_selector, body_selector, link_selector) VALUES (?, ?, ?, ?, ?)", 
              (name, url, title_selector, body_selector, link_selector))
    
    conn.commit()
    conn.close()
    
    return "Новинний сайт додано!"

# Ініціалізація бази даних
initialize_db()

rss_interface = gr.Interface(fn=fetch_news, 
                             inputs=["number", gr.Checkbox(label="Авто оновлення")], 
                             outputs="json",
                             live=True)

add_rss_interface = gr.Interface(fn=add_rss_source, 
                                 inputs=["text", "text"], 
                                 outputs="text")

add_news_site_interface = gr.Interface(fn=add_news_site, 
                                       inputs=["text", "text", "text", "text", "text"], 
                                       outputs="text")

gr.TabbedInterface([rss_interface, add_rss_interface, add_news_site_interface], ["Отримати новини", "Додати RSS джерело", "Додати новинний сайт"]).launch()
