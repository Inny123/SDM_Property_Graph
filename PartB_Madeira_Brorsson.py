import os

from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

class PartBQueries:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def query_b1_top_cited_papers(self):
        """Top 3 most cited papers for each edition of conferences/workshops"""
        query = """
        MATCH (venue)-[:HAS_EDITION]->(edition:Edition)
        WHERE venue:Conference OR venue:Workshop
        
        CALL (venue, edition) {
            MATCH (edition)-[:PUBLISHES]->(proceeding:Proceeding)<-[:PUBLISHED_IN]-(p:Paper)
            WITH p, COUNT { (p)<-[:CITES]-() } AS citation_count
            ORDER BY citation_count DESC, p.title ASC
            LIMIT 3
            RETURN {
                title: p.title,
                year: p.year,
                citations: citation_count
            } AS top_paper_data
        }
        
        RETURN venue.name AS Venue,
               edition.year AS Year,
               edition.city AS City,
               collect(top_paper_data) AS Top3Papers
        ORDER BY Venue, Year
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b2_community_authors(self):
        """Authors who published in 4+ different editions of the same conference/workshop"""
        query = """
        MATCH (venue)
        WHERE venue:Conference OR venue:Workshop
        
        CALL (venue) {
            MATCH (venue)-[:HAS_EDITION]->(edition:Edition)-[:PUBLISHES]->(proceeding:Proceeding)<-[:PUBLISHED_IN]-(paper:Paper)<-[:WRITES]-(author:Author)
            WITH author, collect(DISTINCT edition.year) AS years
            WHERE size(years) >= 4
            RETURN author.name AS author_name,
                   size(years) AS edition_count,
                   years AS years_published
        }
        
        RETURN author_name AS Author,
               venue.name AS Venue,
               edition_count AS EditionCount,
               years_published AS Years
        ORDER BY EditionCount DESC, Author
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b3_journal_impact_factor(self):
        """Journal impact factors based on 2018-2019 papers cited in 2020"""
        query = """
        MATCH (journal:Journal)
        
        CALL (journal) {
            MATCH (journal)-[:HAS_VOLUME]->(volume:Volume)<-[:PUBLISHED_IN]-(paper:Paper)
            WHERE volume.year IN [2018, 2019]
            
            WITH journal, paper
            OPTIONAL MATCH (paper)<-[:CITES]-(citing:Paper)
            WHERE citing.year = 2020
            
            WITH journal,
                 count(DISTINCT paper) AS papers_published,
                 count(citing) AS citations_received
            WHERE papers_published > 0
            
            RETURN papers_published,
                   citations_received,
                   round(toFloat(citations_received) / papers_published, 2) AS impact_factor
        }
        
        RETURN journal.name AS Journal,
               papers_published AS Papers_2018_2019,
               citations_received AS Citations_2020,
               impact_factor AS ImpactFactor
        ORDER BY ImpactFactor DESC
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b4_author_h_index(self):
        """Calculate h-index for top 20 authors"""
        query = """
        MATCH (author:Author)
        
        CALL (author) {
            MATCH (author)-[:WRITES]->(paper:Paper)
            WITH author, paper, COUNT { (paper)<-[:CITES]-() } AS citations
            ORDER BY citations DESC
            
            WITH author, collect(citations) AS citation_list
            
            RETURN reduce(s = 0, i IN range(0, size(citation_list)-1) | 
                          s + CASE WHEN citation_list[i] >= i+1 THEN 1 ELSE 0 END) AS h_index
        }
        
        RETURN author.name AS Author,
               h_index AS hIndex
        ORDER BY hIndex DESC
        LIMIT 20
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

def main():
    queries = PartBQueries(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("B.1 - Top 3 cited papers per conference/workshop:")
        results_b1 = queries.query_b1_top_cited_papers()
        print(json.dumps(results_b1[:5], indent=2))
        
        print("\nB.2 - Community authors (4+ editions):")
        results_b2 = queries.query_b2_community_authors()
        print(json.dumps(results_b2[:10], indent=2))
        
        print("\nB.3 - Journal impact factors:")
        results_b3 = queries.query_b3_journal_impact_factor()
        print(json.dumps(results_b3, indent=2))
        
        print("\nB.4 - Author h-index:")
        results_b4 = queries.query_b4_author_h_index()
        print(json.dumps(results_b4[:10], indent=2))
        
    finally:
        queries.close()

if __name__ == "__main__":
    main()