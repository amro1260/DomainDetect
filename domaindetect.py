import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.error import HTTPError
from tld import get_tld


def google_search(query, num_results=20):
    """
    Perform a Google search for the query and return a list of URLs.
    
    :param query: Search query string
    :param num_results: Number of search results to return
    :return: List of URLs
    """
    results = []
    try:
        for url in search(query, num=num_results, stop=num_results, pause=2):
            results.append(url)
    except HTTPError as e:
        print(f"Error during Google search: {e}")
    return results


def clean_query(query):
    """
    Clean the query by removing non-alphanumeric characters and splitting it into words.
    
    :param query: Search query string
    :return: List of cleaned query words
    """
    return re.sub(r'[^a-zA-Z0-9]', ' ', query).split()


def exclude_unwanted_domains(urls):
    """
    Filter out unwanted domains from the list of URLs.
    
    :param urls: List of URLs
    :return: Filtered list of URLs
    """
    exclude_domains_pattern = re.compile(
        ".*(linkedin.com|twitter|owler|youtube|manta.com|cbinsights.com|opensecrets.org|pitchbook.com"
        "|buzzfile.com|massinvestordatabase.com|bciq.biocentury.com|facebook|finance.yahoo.com|wikipedia"
        "|google|bloomberg.com|marketwatch.com|ft.com|cnn.com|wsj.com|economist.com|crunchbase.com"
        "|xing|glassdoor|jobs|workable.com|github.com)", re.IGNORECASE)
    return [url for url in urls if not exclude_domains_pattern.match(url)]


def extract_domains(urls):
    """
    Extract domains from a list of URLs using the `tld` library.
    
    :param urls: List of URLs
    :return: List of cleaned domains
    """
    domains = []
    for url in urls:
        try:
            tld_info = get_tld(url, as_object=True)
            domains.append(re.sub(r'[^a-zA-Z0-9]', '', tld_info.domain))
        except Exception as e:
            print(f"Error processing domain for URL {url}: {e}")
    return domains


def find_best_match(domains, query_cleaned):
    """
    Find the best matching domain based on exact, semi, or letter matching.
    
    :param domains: List of domains extracted from URLs
    :param query_cleaned: Cleaned query list
    :return: Tuple (Best matching domain, Match type)
    """
    exact_matches = [domain for domain in domains if re.match(r'^' + ''.join(query_cleaned), domain, re.IGNORECASE)]
    semi_matches = [domain for domain in domains if re.match(r'^' + ''.join(query_cleaned[:2]), domain, re.IGNORECASE)]
    letter_matches = [domain for domain in domains if re.match(r'^' + query_cleaned[0], domain, re.IGNORECASE)]

    if exact_matches:
        return exact_matches[0], "exact match"
    elif semi_matches:
        return semi_matches[0], "semi match"
    elif letter_matches:
        return letter_matches[0], "letter match"
    else:
        return "-", "no result"


def validate_html_title(url, query_cleaned):
    """
    Validate if the HTML title of the URL contains the query string.
    
    :param url: URL to validate
    :param query_cleaned: Cleaned query list
    :return: Tuple (URL, validation status)
    """
    try:
        html_title = BeautifulSoup(requests.get(url).content, "lxml").title.string
        html_title_cleaned = re.sub(r'[\t\r\n\x8f]', '', html_title)
    except Exception as e:
        print(f"Error retrieving HTML title: {e}")
        return url, "check"

    if re.search(query_cleaned[0], html_title_cleaned, re.IGNORECASE):
        return url, "fine"
    else:
        return url, "check"


def find_url(query):
    """
    Main function that takes a search query and returns the most relevant URL that matches the query.
    
    :param query: Search query string
    :return: Tuple (Best matching URL, Match type)
    """
    # Step 1: Clean the query
    query_cleaned = clean_query(query)

    # Step 2: Perform a Google search
    search_results = google_search(' '.join(query_cleaned))

    if not search_results:
        return "-", "no result"

    # Step 3: Filter unwanted domains
    filtered_results = exclude_unwanted_domains(search_results)

    # Step 4: Extract domains from the filtered URLs
    domains = extract_domains(filtered_results)

    # Step 5: Find the best match
    best_domain, match_type = find_best_match(domains, query_cleaned)

    if best_domain == "-":
        return "-", "no result"

    # Step 6: Validate the HTML title of the best matching URL
    best_url = filtered_results[domains.index(best_domain)]
    return validate_html_title(best_url, query_cleaned)


# Example usage
if __name__ == "__main__":
    query = "example company name"  # insert the company name here
    result, match_type = find_url(query)
    print(f"Result: {result}, Match Type: {match_type}")
