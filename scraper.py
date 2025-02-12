from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urlparse

def extract_subject_code(url):
    """Extract subject code from URL"""
    path = urlparse(url).path
    return path.split('/')[-1]

def parse_prerequisites(text):
    """Parse prerequisites text to separate prerequisites and corequisites"""
    if not text:
        return None, None
    
    text = clean_text(text)
    
    if any(phrase in text.lower() for phrase in ['no prerequisites', 'none', 'n/a']):
        return None, None
    
    prereqs = None
    coreqs = None
    
    coreq_patterns = [
        r'Co-requisites?:?\s*([^\.]+)',
        r'must be taken alongside:?\s*([^\.]+)',
        r'concurrent enrollment:?\s*([^\.]+)'
    ]
    
    for pattern in coreq_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            coreqs = clean_text(match.group(1))
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    prereq_patterns = [
        r'Pre-requisites?:?\s*([^\.]+)',
        r'must have completed:?\s*([^\.]+)',
        r'requires:?\s*([^\.]+)'
    ]
    
    for pattern in prereq_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prereqs = clean_text(match.group(1))
            break
    
    if not prereqs and text and not any(phrase in text.lower() for phrase in ['no prerequisites', 'none', 'n/a']):
        prereqs = clean_text(text)
    
    return prereqs, coreqs

def clean_text(text):
    """Clean extracted text by removing extra whitespace and newlines"""
    if not text:
        return None
    return re.sub(r'\s+', ' ', text).strip()

def scrape_course_requirements(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            page.goto(url)
            page.wait_for_load_state('networkidle')
            
            undefined_section = page.get_by_label("undefined accordions")
            undefined_section.wait_for()
            
            expand_button = undefined_section.get_by_role("button", name="Expand all")
            expand_button.wait_for(state='visible')
            expand_button.click()
            
            time.sleep(2)
            
            content = undefined_section.inner_html()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            subject_code = extract_subject_code(url)
            
            prereq_section = soup.find(id='Pre-Requisite')
            prereq_text = prereq_section.get_text(strip=True) if prereq_section else None
            
            prerequisites, corequisites = parse_prerequisites(prereq_text)
            
            return {
                'subject_code': subject_code,
                'prerequisites': prerequisites,
                'corequisites': corequisites
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {
                'subject_code': extract_subject_code(url),
                'prerequisites': None,
                'corequisites': None
            }
        
        finally:
            browser.close()

def write_to_csv(courses_data, filename='course_requirements.csv'):
    """Write course data to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['subject_code', 'prerequisites', 'corequisites']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for course in courses_data:
            writer.writerow(course)

def main(): courses
    course_codes = ['CSIT321', 'CSIT314', 'CSIT226']
    base_url = "https://courses.uow.edu.au/subjects/2025/"
    
    courses_data = []
    for code in course_codes:
        url = base_url + code
        print(f"Scraping {code}...")
        course_data = scrape_course_requirements(url)
        courses_data.append(course_data)
        print(f"Completed {code}")
    
    write_to_csv(courses_data)
    print(f"\nData written to course_requirements.csv")
    
    print("\nExtracted Data Preview:")
    for course in courses_data:
        print(f"\nSubject: {course['subject_code']}")
        print(f"Prerequisites: {course['prerequisites'] or 'None'}")
        print(f"Corequisites: {course['corequisites'] or 'None'}")

if __name__ == "__main__":
    main()