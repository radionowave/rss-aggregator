import os
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
import streamlit as st

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
            link_selector TEXT NOT NULL
        )''')

        conn.commit()
        conn.close()

def fetch_rss_feed(url, num_articles=5):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:num_articles]:
        articles.append({
            "source": feed.feed.title,
            "time": entry.published,
            "title": entry.title,
            "link": entry.link
        })
    return articles

def fetch_news_site(url, title_selector, link_selector, num_articles=5):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = []
    titles = soup.select(title_selector)[:num_articles]
    links = soup.select(link_selector)[:num_articles]
    
    for title, link in zip(titles, links):
        articles.append({
            "source": url,
            "time": "N/A",
            "title": title.get_text(),
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

def fetch_news(num_articles=5):
    rss_sources, news_sites = get_sources()
    news = []
    
    for source in rss_sources:
        news.extend(fetch_rss_feed(source[2], num_articles))
    
    for site in news_sites:
        news.extend(fetch_news_site(site[2], site[3], site[4], num_articles))
    
    return news

def add_rss_source(name, url):
    if not name or not url:
        return "Назва та URL не можуть бути порожніми"
    
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO rss_sources (name, url) VALUES (?, ?)", (name, url))
    
    conn.commit()
    conn.close()
    
    return "RSS джерело додано!"

def add_news_site(name, url, title_selector, link_selector):
    if not name or not url or not title_selector or not link_selector:
        return "Жодне поле не може бути порожнім"
    
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO news_sites (name, url, title_selector, link_selector) VALUES (?, ?, ?, ?)", 
              (name, url, title_selector, link_selector))
    
    conn.commit()
    conn.close()
    
    return "Новинний сайт додано!"

def update_rss_source(id, name, url):
    if not name or not url:
        return "Назва та URL не можуть бути порожніми"
    
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("UPDATE rss_sources SET name = ?, url = ? WHERE id = ?", (name, url, id))
    
    conn.commit()
    conn.close()
    
    return "RSS джерело оновлено!"

def update_news_site(id, name, url, title_selector, link_selector):
    if not name or not url or not title_selector or not link_selector:
        return "Жодне поле не може бути порожніми"
    
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("UPDATE news_sites SET name = ?, url = ?, title_selector = ?, link_selector = ? WHERE id = ?", 
              (name, url, title_selector, link_selector, id))
    
    conn.commit()
    conn.close()
    
    return "Новинний сайт оновлено!"

def delete_rss_source(id):
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM rss_sources WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()
    
    return "RSS джерело видалено!"

def delete_news_site(id):
    conn = sqlite3.connect('news_aggregator.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM news_sites WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()
    
    return "Новинний сайт видалено!"

def format_news(news):
    formatted_news = []
    for article in news:
        formatted_news.append({
            "source": article['source'],
            "time": article['time'],
            "title": f"<a href='{article['link']}' target='_blank'>{article['title']}</a>",
            "link": article['link']
        })
    return formatted_news

# Ініціалізація бази даних
initialize_db()

st.title("Агрегатор новин")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Отримати новини", 
    "Додати RSS джерело", 
    "Додати новинний сайт", 
    "Редагувати RSS джерело", 
    "Редагувати новинний сайт", 
    "Видалити RSS джерело", 
    "Видалити новинний сайт"
])

with tab1:
    num_articles = st.number_input("Кількість новин з кожного джерела", min_value=1, max_value=20, value=5)
    if st.button("Отримати новини"):
        news = format_news(fetch_news(num_articles))
        for article in news:
            st.markdown(f"**{article['source']} - {article['time']}**")
            st.markdown(article['title'], unsafe_allow_html=True)

with tab2:
    name = st.text_input("Назва RSS джерела")
    url = st.text_input("URL RSS джерела")
    if st.button("Додати RSS джерело"):
        message = add_rss_source(name, url)
        st.success(message)

with tab3:
    name = st.text_input("Назва новинного сайту")
    url = st.text_input("URL новинного сайту")
    title_selector = st.text_input("CSS селектор для заголовку")
    link_selector = st.text_input("CSS селектор для посилання")
    if st.button("Додати новинний сайт"):
        message = add_news_site(name, url, title_selector, link_selector)
        st.success(message)

with tab4:
    sources = get_rss_sources()
    if sources:
        source_id = st.selectbox("Виберіть RSS джерело для редагування", [f"{src[0]}: {src[1]}" for src in sources])
        selected_source = [src for src in sources if f"{src[0]}: {src[1]}" == source_id][0]
        new_name = st.text_input("Назва RSS джерела", value=selected_source[1])
        new_url = st.text_input("URL RSS джерела", value=selected_source[2])
        if st.button("Оновити RSS джерело"):
            message = update_rss_source(selected_source[0], new_name, new_url)
            st.success(message)

with tab5:
    sites = get_news_sites()
    if sites:
        site_id = st.selectbox("Виберіть новинний сайт для редагування", [f"{site[0]}: {site[1]}" for site in sites])
        selected_site = [site for site in sites if f"{site[0]}: {site[1]}" == site_id][0]
        new_name = st.text_input("Назва новинного сайту", value=selected_site[1])
        new_url = st.text_input("URL новинного сайту", value=selected_site[2])
        new_title_selector = st.text_input("CSS селектор для заголовку", value=selected_site[3])
        new_link_selector = st.text_input("CSS селектор для посилання", value=selected_site[4])
        if st.button("Оновити новинний сайт"):
            message = update_news_site(selected_site[0], new_name, new_url, new_title_selector, new_link_selector)
            st.success(message)

with tab6:
    sources = get_rss_sources()
    if sources:
        source_id = st.selectbox("Виберіть RSS джерело для видалення", [f"{src[0]}: {src[1]}" for src in sources])
        selected_source = [src for src in sources if f"{src[0]}: {src[1]}" == source_id][0]
        if st.button("Видалити RSS джерело"):
            message = delete_rss_source(selected_source[0])
            st.success(message)

with tab7:
    sites = get_news_sites()
    if sites:
        site_id = st.selectbox("Виберіть новинний сайт для видалення", [f"{site[0]}: {site[1]}" for site in sites])
        selected_site = [site for site in sites if f"{site[0]}: {site[1]}" == site_id][0]
        if st.button("Видалити новинний сайт"):
            message = delete_news_site(selected_site[0])
            st.success(message)
