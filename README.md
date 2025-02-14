# UOW Handbook Scraper

This script scrapes subject details from the University of Wollongong (UOW) handbook.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jamesy0ung/uow-handbook-scraper.git
   cd uow-handbook-scraper
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Install Playwright:
   ```bash
   playwright install
   ```

## Usage

Run the scraper with:
   ```bash
   python3 scraper.py [input_filename]
   ```

- If no filename is passed, the script defaults to `input_courses.csv`.
- The input file must be a CSV with the following columns:
  - `SUBJECT CODE`
  - `SUBJECT NAME`
  - `CATEGORY`
  - `YEAR`
- Example input files: `2024.csv`, `2025.csv` (for Computer Science requirements).

## Example

To scrape data using `2025.csv`:
   ```bash
   python3 scraper.py 2025.csv
   ```

## Output

The scraper retrieves subject details (currently prerequisites and corequisites, though it can easily be modified) and saves them in an output file.
