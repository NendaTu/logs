from bs4 import BeautifulSoup
import re
from urllib.parse import unquote
import copy

def split_concatenated_urls(raw_url):
    """Splits strings like 'http://a.comhttp://b.com' into ['http://a.com', 'http://b.com']."""
    return [p for p in re.split(r'(?=https?://)', raw_url) if p]

def extract_all_urls(li):
    """Extracts all clean URLs from an LI element, from both hrefs and text."""
    raw_urls = []
    # From href attributes
    for a in li.find_all('a', href=True):
        raw_urls.append(a['href'])

    # From text content
    text = li.get_text(separator=' ')
    raw_urls.extend(re.findall(r'https?://[^\s<>"]+', text))

    unique_urls = []
    seen = set()
    for u in raw_urls:
        # Clean Google redirect wrapper
        if 'google.com/url?q=' in u:
            match = re.search(r'url\?q=([^&]+)', u)
            if match:
                u = unquote(match.group(1))

        # Split concatenated URLs
        for p in split_concatenated_urls(u):
            # Remove common trailing punctuation
            clean_p = p.strip().rstrip('.,;)]')
            if 'google.com/url' in clean_p:
                continue
            if clean_p and clean_p not in seen:
                unique_urls.append(clean_p)
                seen.add(clean_p)
    return unique_urls

def get_clean_description(li):
    """Returns a clean text description without URLs and leading numbers."""
    text = li.get_text(separator=' ').strip()

    # Identify all URLs and expanded versions
    all_urls = re.findall(r'https?://[^\s<>"]+', text)
    expanded_urls = []
    for u in all_urls:
        expanded_urls.extend(split_concatenated_urls(u))

    # Sort by length descending to replace longer strings first
    for u in sorted(expanded_urls, key=len, reverse=True):
        text = text.replace(u, '')
        text = text.replace(u.strip().rstrip('.,;)]'), '')

    # Remove citations like [123]
    text = re.sub(r'\[\d+\]', '', text)
    # Remove leading numbers like "1. " or "123. "
    text = re.sub(r'^\d+\.\s*', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove trailing dashes or colons that often precede links
    text = re.sub(r'\s*[\-:]\s*$', '', text)

    return text.strip()

def is_republican(text):
    """Checks if the text explicitly mentions Republican-related keywords."""
    keywords = [
        r'\brepublicans?\b',
        r'\bgop\b',
        r'\bmaga\b',
        r'\btrump\b',
        r'\brnc\b',
        r'\(R-[A-Z]+\)', # Matches (R-TX)
        r'\sR-[A-Z]+\b'   # Matches R-MA
    ]
    return any(re.search(kw, text, re.I) for kw in keywords)

def is_legal_action(text):
    """Checks if the text mentions an arrest, conviction, or sentencing."""
    keywords = [
        r'\barrest(ed)?\b',
        r'\bconvict(ed|ion)\b',
        r'\bsentenc(ed|ing)\b',
        r'\bindict(ed|ment)\b',
        r'\bcharged\b',
        r'\bguilty\b',
        r'\bno contest\b',
        r'\bprison\b',
        r'\bjail\b',
        r'\bprobation\b',
        r'\bpleaded\b',
        r'\bpled\b',
        r'\bfined\b',
        r'\bplea deal\b',
        r'\bsurrendered to police\b',
        r'\bfound guilty\b',
        r'\bsex offender registry\b'
    ]
    return any(re.search(kw, text, re.I) for kw in keywords)

def process():
    with open('full_content.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    all_items = soup.find_all('li')
    filtered_results = []

    for li in all_items:
        raw_text = li.get_text(separator=' ').strip()

        if is_republican(raw_text) and is_legal_action(raw_text):
            description = get_clean_description(li)
            # Skip if cleaning left nothing meaningful
            if not any(c.isalpha() for c in description):
                continue

            sources = extract_all_urls(li)

            filtered_results.append({
                'description': description,
                'sources': sources
            })

    # Generate the markdown file as an ordered list
    with open('republican_incidents.md', 'w', encoding='utf-8') as f:
        if not filtered_results:
            f.write("No incidents found matching the criteria.\n")
        else:
            for i, item in enumerate(filtered_results, 1):
                f.write(f"{i}. {item['description']}\n")
                for src in item['sources']:
                    f.write(f"   - {src}\n")
                f.write("\n")

    print(f"Total entries processed: {len(all_items)}")
    print(f"Total filtered entries: {len(filtered_results)}")

if __name__ == "__main__":
    process()
