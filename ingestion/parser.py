import pdfplumber
import re

class ResumeParser:
    def parse_pdf(self, file_path: str) -> list[str]:
        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        return self.clean_text(text)
    
    def extract_github_link(self, text: str) -> str | None:
        match = re.search(r'github\.com\/([a-zA-Z0-9_-]+)', text)
        if match:
            return match.group(1)
        return None
        
    def clean_text(self, text: str) -> list[str]:
        text = text.replace("\n", " ")
        text = " ".join(text.split())
        return self.split_text(text)
    
    def split_text(self, text: str, chunk_size=500, overlap=100) -> list[str]:
        chunks = []
    
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks
