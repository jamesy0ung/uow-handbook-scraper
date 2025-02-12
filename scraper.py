import re
import csv
from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sys

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

def read_input_csv(filename):
    """Read course data from input CSV file"""
    courses = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                courses.append(row)
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found.")
        sys.exit(1)
    return courses

def scrape_course_requirements(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

def write_to_csv(input_courses, prereq_data, filename='combined_course_data.csv'):
    """Write combined course data to CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['SUBJECT CODE', 'SUBJECT NAME', 'CATEGORY', 'YEAR', 'prerequisites', 'corequisites']  # Include new fields
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for course in input_courses:
            prereq_match = next((p for p in prereq_data if p['subject_code'] == course['SUBJECT CODE']), None)

            combined_data = {
                'SUBJECT CODE': course['SUBJECT CODE'],
                'SUBJECT NAME': course['SUBJECT NAME'],
                'CATEGORY': course['CATEGORY'],
                'YEAR': course['YEAR'],
                'prerequisites': prereq_match['prerequisites'] if prereq_match else None,
                'corequisites': prereq_match['corequisites'] if prereq_match else None
            }
            writer.writerow(combined_data)


def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'input_courses.csv'

    base_url = "https://courses.uow.edu.au/subjects/{year}/{code}"

    input_courses = read_input_csv(input_file)

    courses_data = []
    for course in input_courses:
        url = base_url.format(year=course['YEAR'], code=course['SUBJECT CODE'])
        print(f"Scraping {course['SUBJECT CODE']}...")
        course_data = scrape_course_requirements(url)
        courses_data.append(course_data)
        print(f"Completed {course['SUBJECT CODE']}")


    write_to_csv(input_courses, courses_data)
    print(f"\nCombined data written to combined_course_data.csv")


if __name__ == "__main__":
    main()