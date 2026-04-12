from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

class PartBQueries:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def query_b1_top_cited_papers(self):
        query = """
        MATCH (venue)-[:HAS_EDITION]->(proceeding:Proceeding)
        WHERE venue:Conference OR venue:Workshop
        
        MATCH (proceeding)<-[:PUBLISHED_IN]-(paper:Paper)
        
        OPTIONAL MATCH (paper)<-[:CITES]-(citing:Paper)
        
        WITH venue, proceeding, paper, count(citing) as citationCount
        ORDER BY venue.name, proceeding.year, citationCount DESC
        
        WITH venue, proceeding, collect({
            title: paper.title,
            year: paper.year,
            citations: citationCount
        })[0..3] as topPapers
        
        RETURN venue.name as Venue,
               proceeding.year as Year,
               proceeding.city as City,
               topPapers as Top3Papers
        ORDER BY Venue, Year
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b2_community_authors(self):
        query = """
        MATCH (author:Author)-[:WRITES]->(paper:Paper)-[:PUBLISHED_IN]->(proceeding:Proceeding)
        MATCH (venue)-[:HAS_EDITION]->(proceeding)
        WHERE venue:Conference OR venue:Workshop
        
        WITH author, venue, collect(DISTINCT proceeding.year) as years
        WHERE size(years) >= 4
        
        RETURN author.name as Author,
               venue.name as Venue,
               size(years) as EditionCount,
               years as Years
        ORDER BY EditionCount DESC, Author
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b3_journal_impact_factor(self):
        query = """
        WITH 2020 as targetYear
        MATCH (journal:Journal)-[:HAS_VOLUME]->(volume:Volume)
        WHERE volume.year IN [targetYear - 1, targetYear - 2]
        
        MATCH (volume)<-[:PUBLISHED_IN]-(paper:Paper)
        
        OPTIONAL MATCH (paper)<-[:CITES]-(citing:Paper)
        WHERE citing.year = targetYear
        
        WITH journal, 
             count(DISTINCT paper) as papersPublished,
             count(citing) as citationsReceived
        WHERE papersPublished > 0
        
        RETURN journal.name as Journal,
               papersPublished as Papers_2018_2019,
               citationsReceived as Citations_2020,
               round(toFloat(citationsReceived) / papersPublished, 2) as ImpactFactor
        ORDER BY ImpactFactor DESC
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_b4_author_h_index(self):
        query = """
        MATCH (author:Author)-[:WRITES]->(paper:Paper)
        OPTIONAL MATCH (paper)<-[:CITES]-(citing:Paper)
        
        WITH author, paper, count(citing) as citations
        ORDER BY author.name, citations DESC
        
        WITH author, collect(citations) as citationList
        
        WITH author, citationList,
             [i IN range(0, size(citationList)-1) | 
              CASE WHEN citationList[i] >= i+1 THEN 1 ELSE 0 END] as hList
        
        RETURN author.name as Author,
               reduce(s = 0, x IN hList | s + x) as hIndex
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
