import os
import requests
import csv
import time
from pathlib import Path
from collections import defaultdict

API_KEY = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
BASE_URL = "https://api.semanticscholar.org/graph/v1"
DATA_DIR = Path("neo4j_data")
RATE_LIMIT = 1.0

class SemanticScholarClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'x-api-key': api_key} if api_key else {}
        self.last_request = 0
    
    def wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < RATE_LIMIT:
            time.sleep(RATE_LIMIT - elapsed)
        self.last_request = time.time()
    
    def search_papers(self, query, limit=100, offset=0):
        self.wait_for_rate_limit()
        url = f"{BASE_URL}/paper/search"
        params = {
            'query': query,
            'limit': limit,
            'offset': offset,
            'fields': 'paperId,title,year,abstract,authors,venue,externalIds,citations,references,s2FieldsOfStudy'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    
    def get_paper_details(self, paper_id):
        self.wait_for_rate_limit()
        url = f"{BASE_URL}/paper/{paper_id}"
        params = {
            'fields': 'paperId,title,year,abstract,authors,venue,externalIds,citations,references,s2FieldsOfStudy'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None

def collect_papers(client, num_papers=500):
    topics = [
        "data management",
        "indexing",
        "data modeling",
        "big data",
        "data processing",
        "data storage",
        "data querying"
    ]
    
    papers = {}
    papers_per_topic = 150
    
    for topic in topics:
        print(f"Searching for papers on: {topic}")
        results = client.search_papers(topic, limit=papers_per_topic)
        for paper in results:
            if paper.get('paperId'):
                papers[paper['paperId']] = paper
    
    collected = list(papers.values())
    print(f"Total unique papers collected: {len(collected)}")
    return collected

def extract_citations(papers):
    all_cited_ids = set()
    for paper in papers:
        citations = paper.get('citations', [])
        for citation in citations:
            if citation.get('paperId'):
                all_cited_ids.add(citation['paperId'])
    
    existing_ids = {p.get('paperId') for p in papers}
    return all_cited_ids - existing_ids

def fetch_top_cited_papers(client, papers, top_n=100):
    paper_ids = {p.get('paperId') for p in papers}
    citation_counts = defaultdict(int)
    
    for paper in papers:
        references = paper.get('references') or []
        for ref in references:
            ref_id = ref.get('paperId')
            if ref_id and ref_id not in paper_ids:
                citation_counts[ref_id] += 1
    
    if not citation_counts:
        print("No new referenced papers found")
        return []
    
    top_cited = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    enriched = []
    for i, (paper_id, count) in enumerate(top_cited, 1):
        print(f"Fetching referenced paper {i}/{len(top_cited)} (referenced {count} times)...")
        paper_data = client.get_paper_details(paper_id)
        if paper_data:
            enriched.append(paper_data)
    
    return enriched

def generate_csv_files(papers):
    DATA_DIR.mkdir(exist_ok=True)
    
    authors = {}
    conferences = {}
    journals = {}
    workshops = {}
    editions = {}
    proceedings = {}
    volumes = {}
    topics = {}
    papers_data = {}

    wrote_edges = []
    cites_edges = []
    about_edges = []
    published_in_proceeding = []
    published_in_volume = []
    has_edition_edges = []
    has_volume_edges = []
    publishes_edges = []
    
    for paper in papers:
        paper_id = paper.get('paperId')
        abstract = paper.get('abstract')
        doi = paper.get('externalIds', {}).get('DOI')
        if not paper_id or not abstract or not doi:
            continue
        
        papers_data[paper_id] = {
            'paperId': paper_id,
            'title': paper.get('title', ''),
            'year': paper.get('year', ''),
            'abstract': abstract,
            'doi': doi
        }
        
        author_list = paper.get('authors', [])
        for idx, author in enumerate(author_list):
            author_id = author.get('authorId')
            if author_id:
                authors[author_id] = {
                    'authorId': author_id,
                    'name': author.get('name', '')
                }
                wrote_edges.append({
                    'from': author_id,
                    'to': paper_id,
                    'corresponding': 'true' if idx == 0 else 'false'
                })
        
        s2_fields = paper.get('s2FieldsOfStudy', [])
        for field in s2_fields:
            if field and isinstance(field, dict):
                category = field.get('category', '')
                if category:
                    topic_id = f"topic::{category.lower()}"
                    topics[topic_id] = {
                        'topicId': topic_id,
                        'name': category
                    }
                    about_edges.append({
                        'from': paper_id,
                        'to': topic_id
                    })
        
        venue = paper.get('venue', '')
        year = paper.get('year', '')
        if venue and year:
            if 'workshop' in venue.lower():
                workshop_id = f"workshop::{venue.lower()}"
                workshops[workshop_id] = {'workshopId': workshop_id, 'name': venue}
                
                edition_id = f"edition::{venue.lower()}::{year}"
                editions[edition_id] = {
                    'editionId': edition_id,
                    'editionNumber': year,
                    'year': year,
                    'city': ''
                }
                
                proc_id = f"proceeding::{venue.lower()}::{year}"
                proceedings[proc_id] = {'proceedingId': proc_id}
                
                has_edition_edges.append({'from': workshop_id, 'to': edition_id})
                publishes_edges.append({'from': edition_id, 'to': proc_id})
                published_in_proceeding.append({'from': paper_id, 'to': proc_id})
                
            elif 'conference' in venue.lower() or 'symposium' in venue.lower():
                conf_id = f"conference::{venue.lower()}"
                conferences[conf_id] = {'conferenceId': conf_id, 'name': venue}
                
                edition_id = f"edition::{venue.lower()}::{year}"
                editions[edition_id] = {
                    'editionId': edition_id,
                    'editionNumber': year,
                    'year': year,
                    'city': ''
                }
                
                proc_id = f"proceeding::{venue.lower()}::{year}"
                proceedings[proc_id] = {'proceedingId': proc_id}
                
                has_edition_edges.append({'from': conf_id, 'to': edition_id})
                publishes_edges.append({'from': edition_id, 'to': proc_id})
                published_in_proceeding.append({'from': paper_id, 'to': proc_id})
                
            else:
                journal_id = f"journal::{venue.lower()}"
                journals[journal_id] = {'journalId': journal_id, 'name': venue}
                
                vol_id = f"volume::{venue.lower()}::{year}"
                volumes[vol_id] = {
                    'volumeId': vol_id,
                    'volumeNumber': year,
                    'year': year
                }
                has_volume_edges.append({'from': journal_id, 'to': vol_id})
                published_in_volume.append({'from': paper_id, 'to': vol_id})
        
        for ref in (paper.get('references') or []):
            ref_id = ref.get('paperId')
            if ref_id:
                cites_edges.append({'from': paper_id, 'to': ref_id})
    
    write_csv('authors_nodes.csv', list(authors.values()), ['authorId', 'name'])
    write_csv('papers_nodes.csv', list(papers_data.values()), ['paperId', 'title', 'year', 'abstract', 'doi'])    
    write_csv('conferences_nodes.csv', list(conferences.values()), ['conferenceId', 'name'])
    write_csv('journals_nodes.csv', list(journals.values()), ['journalId', 'name'])
    write_csv('workshops_nodes.csv', list(workshops.values()), ['workshopId', 'name'])
    write_csv('editions_nodes.csv', list(editions.values()), ['editionId', 'editionNumber', 'year', 'city'])
    write_csv('proceedings_nodes.csv', list(proceedings.values()), ['proceedingId'])
    write_csv('volumes_nodes.csv', list(volumes.values()), ['volumeId', 'volumeNumber', 'year'])
    write_csv('topics_nodes.csv', list(topics.values()), ['topicId', 'name'])
    
    write_csv('wrote_edges.csv', wrote_edges, ['from', 'to', 'corresponding'])
    write_csv('cites_edges.csv', cites_edges, ['from', 'to'])
    write_csv('about_edges.csv', about_edges, ['from', 'to'])
    write_csv('published_in_proceeding_edges.csv', published_in_proceeding, ['from', 'to'])
    write_csv('published_in_volume_edges.csv', published_in_volume, ['from', 'to'])
    write_csv('has_edition_edges.csv', has_edition_edges, ['from', 'to'])
    write_csv('has_volume_edges.csv', has_volume_edges, ['from', 'to'])
    write_csv('publishes_edges.csv', publishes_edges, ['from', 'to'])

def write_csv(filename, data, fieldnames):
    if not data:
        return
    
    filepath = DATA_DIR / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    client = SemanticScholarClient(API_KEY)
    
    print("Collecting papers...")
    papers = collect_papers(client, num_papers=500)
    print(f"Collected {len(papers)} papers")
    
    paper_map = {p['paperId']: p for p in papers if p.get('paperId')}

    for iteration in range(1, 15):
        print(f"\nIteration {iteration}: Fetching top 125 most-referenced papers...")
        new_papers = fetch_top_cited_papers(client, list(paper_map.values()), top_n=125)

        added_count = 0
        for paper in new_papers:
            paper_id = paper.get('paperId')
            if paper_id and paper_id not in paper_map:
                paper_map[paper_id] = paper
                added_count += 1

        print(f"Added {added_count} highly referenced papers")
        print(f"Total papers after iteration {iteration}: {len(paper_map)}")

    current_set = list(paper_map.values())
    
    print(f"\nFinal total papers: {len(current_set)}")
    if (len(current_set) < 1000):
        main()  # Restart if we haven't reached 1000 papers because of network outages or API issues
        
    else:
        print("\nGenerating CSV files...")
        generate_csv_files(current_set)
        print("CSV files generated successfully")

if __name__ == "__main__":
    main()