import streamlit as st
from playwright.sync_api import sync_playwright
import time
from lxml import html, etree
import subprocess
import sys
import os

# Function to check if Playwright is installed and install it if not
def ensure_playwright_installed():
    try:
        import playwright
    except ImportError:
        st.warning("Playwright is not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        os.system('playwright install')
        os.system('playwright install-deps')
        st.success("Playwright installed successfully.")

# Function to fetch HTML content with Playwright
def fetch_html_with_playwright(url, delay, load_js):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        if load_js:
            page.goto(url)
        else:
            page.goto(url, wait_until='domcontentloaded')
        
        time.sleep(delay)
        html_content = page.content()
        browser.close()
        return html_content

# Function to clean HTML content
def clean_html(html_content):
    tree = html.fromstring(html_content)
    
    # Remove unnecessary elements
    for bad in tree.xpath("//script|//style|//svg|//comment()"):
        bad.getparent().remove(bad)
    
    # Remove attributes that are not useful for scraping
    for element in tree.iter():
        for attr in list(element.attrib):
            if attr not in ['href', 'src', 'alt', 'title']:
                del element.attrib[attr]
    
    return html.tostring(tree, pretty_print=True).decode('utf-8')

# Function to extract divs and their data
def extract_divs(html_content):
    tree = html.fromstring(html_content)
    divs = tree.xpath('//div')
    div_data = []
    for div in divs:
        div_info = {
            'text': div.text_content().strip() if div.text_content() else "",
            'links': [a.get('href') for a in div.xpath('.//a')],
            'xpath': tree.getpath(div),
            'css_selector': xpath_to_css(tree.getpath(div))
        }
        div_data.append(div_info)
    return div_data

# Function to convert XPath to CSS selector
def xpath_to_css(xpath):
    css_selector = xpath.replace('/', ' > ').replace('[@', '[')
    css_selector = css_selector.replace(']', '').replace('[', '[')
    css_selector = css_selector.replace('=', '=')
    return css_selector

# Ensure Playwright is installed
ensure_playwright_installed()

# Streamlit app
st.title("XPath and CSS Selector Extractor")

# Input URL
url = st.text_input("Enter URL to scrape:")

# Delay option
delay = st.number_input("Delay (in seconds) before fetching HTML:", min_value=0, value=0)

# JavaScript load option
load_js = st.checkbox("Load JavaScript?")

if url:
    html_content = fetch_html_with_playwright(url, delay, load_js)
    if html_content:
        cleaned_html = clean_html(html_content)
        div_data = extract_divs(cleaned_html)

        # Display divs and their data
        st.header("Select Elements by Div")
        selected_divs = []
        for div in div_data:
            st.subheader(f"Div XPath: {div['xpath']}")
            st.write(f"**Text:** {div['text']}")
            st.write(f"**Links:** {', '.join(div['links'])}")
            if st.checkbox(f"Select this div ({div['xpath']})"):
                selected_divs.append(div)

        # Display selected divs' XPaths and CSS selectors
        if selected_divs:
            st.header("Selected Divs")
            for div in selected_divs:
                st.write(f"**Text:** {div['text']}")
                st.write(f"**Links:** {', '.join(div['links'])}")
                st.write(f"**XPath:** {div['xpath']}")
                st.write(f"**CSS Selector:** {div['css_selector']}")
                st.write("---")
