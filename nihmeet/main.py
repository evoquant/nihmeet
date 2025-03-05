import requests
from datetime import datetime
from nihmeet.pxml import parse_meetings

import json
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_existing_hashes():
    d = set()
    with open("data.json", "r") as f:
        for line in f:
            parsed = json.loads(line)
            d.add(parsed["hash"])
    return d

def get_most_recent_pages(num_pages=2):
    data = []
    for i in range(1, num_pages):
        url = f"https://www.federalregister.gov/api/v1/documents?conditions%5Bagency_ids%5D%5B%5D=353&format=json&order=newest&page={str(i)}"
        response = requests.get(url)
        temp = response.json()
        temp = temp["results"]
        data.extend(temp)
    return data


def get_xml_url(document_number):
    response = requests.get(
        f"https://www.federalregister.gov/api/v1/documents/{document_number}"
    )
    data = response.json()
    return data["full_text_xml_url"]


def get_xml_text(url):
    response = requests.get(url)
    return response.text

def get_meetings():
    existing_data = get_existing_hashes()
    print(f"Existing data hashes: {existing_data}")  # Log existing hashes
    for result in get_most_recent_pages():
        if result["type"] == "Notice" and "Notice of Closed Meeting" in result["title"]:
            publication_date = result["publication_date"]
            # check if publication date is feb 2025 or after
            publication_date = datetime.strptime(publication_date, "%Y-%m-%d")
            if publication_date < datetime(2025, 2, 1):
                break
            publication_date = publication_date.strftime("%Y-%m-%d")
            publication_date = str(publication_date)
            xml_url = get_xml_url(result["document_number"])
            for meeting in parse_meetings(get_xml_text(xml_url), publication_date):
                if meeting.hash not in existing_data:
                    yield meeting
                else:
                    logging.info(
                        f"Skipping data that already exists: {meeting.committee} - {meeting.date}"
                    )

if __name__ == "__main__":
    with open("data.jsonl", "a") as f:
        for i in get_meetings():
            js = i.to_json()
            f.write(js + "\n")
