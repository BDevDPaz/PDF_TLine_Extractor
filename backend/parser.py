import fitz # PyMuPDF
from models import SessionLocal, Line, CallEvent, TextEvent, DataEvent
from datetime import datetime
import re

COLUMN_BOUNDARIES_X = {
    'TALK': { 'when': 30, 'who': 130, 'description': 250, 'type': 470, 'min': 500 },
    'TEXT': { 'when': 30, 'who': 130, 'destination': 250, 'type': 470 },
    'DATA': { 'when': 30, 'mb': 200 }
}
MONTH_MAP = { "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12, "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6 }

class PDFParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self.session = SessionLocal()
        self.processed_lines = set()
        try:
            self.current_year = int(re.search(r'Bill issue date\s+\w+\s+\d{1,2},\s+(\d{4})', self.doc[0].get_text()).group(1))
        except:
            self.current_year = datetime.now().year

    def _parse_timestamp(self, when_str):
        match = re.search(r'(\w{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2})\s+(AM|PM)', when_str, re.IGNORECASE)
        if not match: return datetime.now()
        
        month_str, day_str, hour_str, min_str, am_pm = match.groups()
        month = MONTH_MAP.get(month_str, 1); day = int(day_str); hour = int(hour_str); minute = int(min_str)
        
        if am_pm.upper() == 'PM' and hour != 12: hour += 12
        if am_pm.upper() == 'AM' and hour == 12: hour = 0
            
        return datetime(self.current_year, month, day, hour, minute)

    def _parse_page(self, page):
        page_text = page.get_text("text")
        
        phone_match = re.search(r'(\(\d{3}\) \d{3}-\d{4})', page_text)
        current_event_type = None
        if "TALK" in page_text: current_event_type = "TALK"
        elif "TEXT" in page_text: current_event_type = "TEXT"
        elif "DATA" in page_text: current_event_type = "DATA"

        if phone_match and current_event_type:
            phone_number = phone_match.group(0)
            line = self.session.query(Line).filter_by(phone_number=phone_number).first()
            if not line:
                line = Line(phone_number=phone_number)
                self.session.add(line); self.session.flush()

            if phone_number not in self.processed_lines:
                print(f"Borrando datos antiguos para {phone_number}...")
                self.session.query(CallEvent).filter_by(line_id=line.id).delete()
                self.session.query(TextEvent).filter_by(line_id=line.id).delete()
                self.session.query(DataEvent).filter_by(line_id=line.id).delete()
                self.processed_lines.add(phone_number)
            
            words = page.get_text("words")
            lines = {}
            for x0, y0, x1, y1, word, _, _, _ in words:
                y_key = round(y0);
                if y_key not in lines: lines[y_key] = []
                lines[y_key].append((x0, word))

            bounds = COLUMN_BOUNDARIES_X.get(current_event_type)
            if not bounds: return

            for y_key in sorted(lines.keys()):
                line_words = sorted(lines[y_key], key=lambda x: x[0])
                full_line_text = " ".join(w for _, w in line_words)
                if any(h in full_line_text for h in ["When", "Who", "Totals", "Description", "...CONTINUED"]): continue

                if current_event_type == "TALK":
                    try:
                        who = " ".join(w for x, w in line_words if bounds['who'] <= x < bounds['description'])
                        desc = " ".join(w for x, w in line_words if bounds['description'] <= x < bounds['type'])
                        typ = " ".join(w for x, w in line_words if bounds['type'] <= x < bounds['min'])
                        minutes = "".join(w for x, w in line_words if x >= bounds['min']).strip()
                        
                        if who and minutes.isdigit():
                            self.session.add(CallEvent(
                                line_id=line.id, timestamp=self._parse_timestamp(full_line_text),
                                counterpart_number=who.strip(), description=desc.strip(),
                                call_type=typ.strip(), duration_minutes=int(minutes)
                            ))
                    except Exception as e:
                        print(f"Error procesando fila TALK: {full_line_text} | Error: {e}")

    def run_extraction(self):
        start_page = 4
        end_page = len(self.doc) - 2
        for page_num in range(start_page - 1, end_page):
            self._parse_page(self.doc[page_num])
        try:
            self.session.commit()
            print("Extracción completada y guardada.")
        except Exception as e:
            self.session.rollback(); print(f"Error al guardar en DB: {e}")
        finally:
            self.session.close()