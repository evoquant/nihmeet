import hashlib
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Meeting:
    def __init__(
        self,
        committee=None,
        date=None,
        time=None,
        agenda=None,
        meeting_format=None,
        start_date=None,
        start_time=None,
        end_date=None,
        end_time=None,
        fed_reg_publication_date=None,
    ):
        self.committee = committee
        self.date = date
        self.time = time
        self.agenda = agenda
        self.meeting_format = meeting_format
        # New separate fields
        self.start_date = start_date
        self.start_time = start_time
        self.end_date = end_date
        self.end_time = end_time
        self.fed_reg_publication_date = fed_reg_publication_date
        try:
            self._parse_dates()
        except Exception as e:
            logging.error(f"Error parsing date and time: {e}")
        self.hash = self._hash()

    def _convert_to_24hr(self, time_str):
        """Convert time to 24-hour format"""
        # Handle a.m. and p.m. cases
        time_str = time_str.lower().strip()
        # Remove a.m. or p.m. suffix
        if time_str.endswith("a.m."):
            time_str = time_str[:-5].strip()
            # Special case for 12 a.m. (midnight)
            if time_str.startswith("12:"):
                time_str = "00:" + time_str.split(":")[1]
        elif time_str.endswith("p.m."):
            time_str = time_str[:-5].strip()
            # Convert to 24-hour format for p.m.
            if not time_str.startswith("12:"):
                hours, minutes = time_str.split(":")
                time_str = f"{int(hours) + 12}:{minutes}"
        return time_str

    def _parse_dates(self):
        """Parse and separate date and time into start and end dates"""
        if self.date:
            date_parts = self.date.split()
            month = date_parts[0]
            day = date_parts[1].replace(",", "")
            # Handle multiple days
            if "-" in day:
                start_day, end_day = day.split("-")
            else:
                start_day = end_day = day
            year = date_parts[2].replace(".", "")
            # Parse start and end dates
            start_date_obj = datetime.strptime(
                f"{month} {start_day} {year}", "%B %d %Y"
            )
            end_date_obj = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
            # Set start and end dates
            self.start_date = start_date_obj.strftime("%Y-%m-%d")
            self.end_date = end_date_obj.strftime("%Y-%m-%d")
        # Parse time
        if self.time:
            # Split time into start and end times
            if "-" in self.time:
                start_time, end_time = self.time.split("-")
            elif "to" in self.time:
                start_time, end_time = self.time.split("to")
            else:
                start_time = end_time = self.time
            # Convert to 24-hour format
            self.start_time = self._convert_to_24hr(start_time)
            self.end_time = self._convert_to_24hr(end_time)

    def __str__(self):
        return (
            f"Fed Reg Publication Date: {self.fed_reg_publication_date}\n"
            f"Committee: {self.committee}\n"
            f"Original Date: {self.date}\n"
            f"Original Time: {self.time}\n"
            f"Start Date: {self.start_date}\n"
            f"Start Time: {self.start_time}\n"
            f"End Date: {self.end_date}\n"
            f"End Time: {self.end_time}\n"
            f"Agenda: {self.agenda}\n"
            f"Meeting Format: {self.meeting_format}\n"
        )

    def _hash(self):
        hash = hashlib.md5()
        data = f"{self.fed_reg_publication_date}{self.committee}{self.start_date}{self.start_time}{self.end_date}{self.end_time}{self.agenda}{self.meeting_format}"
        hash.update(data.encode("utf-8"))
        return hash.hexdigest()

    def to_json(self):
        return json.dumps(
            {
                "fed_reg_publication_date": self.fed_reg_publication_date,
                "committee": self.committee,
                "start_date": self.start_date,
                "start_time": self.start_time,
                "end_date": self.end_date,
                "end_time": self.end_time,
                "date": self.date,
                "time": self.time,
                "agenda": self.agenda,
                "meeting_format": self.meeting_format,
                "hash": self.hash,
            }
        )


def load_xml_file(file_path: Path) -> Optional[ET.Element]:
    """Loads and parses an XML file."""
    try:
        xml_content = file_path.read_text(encoding="utf-8")
        return ET.fromstring(xml_content)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except ET.ParseError:
        logging.error(f"Error parsing XML file: {file_path}")
    return None


def parse_meetings(text, publication_date) -> List[Meeting]:
    """Parses meeting data from XML and returns a list of Meeting objects."""
    meetings = []
    root = ET.fromstring(text)
    meeting_extracts = root.findall(".//EXTRACT/P/E")
    current_meeting = {}
    for element in meeting_extracts:
        text = (element.text or "").strip()
        tail = (element.tail or "").strip()
        if element.get("T") == "03":
            if "Name of Committee" in text:
                if current_meeting:
                    meetings.append(
                        Meeting(
                            **current_meeting
                            | {"fed_reg_publication_date": publication_date}
                        )
                    )
                current_meeting = {"committee": tail}
            elif "Date:" in text:
                current_meeting["date"] = tail
            elif "Time:" in text:
                current_meeting["time"] = tail
            elif "Agenda:" in text:
                current_meeting["agenda"] = tail
            elif "Meeting Format:" in text:
                current_meeting["meeting_format"] = tail
    # Add last parsed meeting
    if current_meeting:
        meetings.append(
            Meeting(**current_meeting | {"fed_reg_publication_date": publication_date})
        )
    return meetings


