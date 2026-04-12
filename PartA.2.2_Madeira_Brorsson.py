from neo4j import GraphDatabase
import csv
from pathlib import Path
import random
import os

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
DATA_DIR = Path("neo4j_data")

CITIES = [
    "Barcelona", "Paris", "London", "New York", "Tokyo", "Singapore",
    "Berlin", "Amsterdam", "San Francisco", "Boston", "Seattle", 
    "Chicago", "Toronto", "Sydney", "Melbourne", "Munich"
]
 
class Neo4jDataLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")
    
    def create_constraints(self):
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.authorId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.paperId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Conference) REQUIRE c.conferenceId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (j:Journal) REQUIRE j.journalId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Workshop) REQUIRE w.workshopId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Edition) REQUIRE e.editionId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Proceeding) REQUIRE pr.proceedingId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Volume) REQUIRE v.volumeId IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.topicId IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except:
                    pass
            
            print("Constraints created")
    
    def load_nodes(self):
        with self.driver.session() as session:
            self._load_authors(session)
            self._load_papers(session)
            self._load_conferences(session)
            self._load_journals(session)
            self._load_workshops(session)
            self._load_editions(session)
            self._load_proceedings(session)
            self._load_volumes(session)
            self._load_topics(session)
    
    def _load_authors(self, session):
        file_path = DATA_DIR / "authors_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_authors_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_authors_batch, batch)
        
        print(f"Loaded authors")
    
    @staticmethod
    def _create_authors_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (a:Author {
            authorId: row.authorId,
            name: row.name
        })
        """
        tx.run(query, batch=batch)
    
    def _load_papers(self, session):
        file_path = DATA_DIR / "papers_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 500:
                    session.execute_write(self._create_papers_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_papers_batch, batch)
        
        print(f"Loaded papers")
    
    @staticmethod
    def _create_papers_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (p:Paper {
            paperId: row.paperId,
            title: row.title,
            year: toInteger(row.year),
            abstract: row.abstract,
            doi: row.doi
        })
        """
        tx.run(query, batch=batch)
    
    def _load_conferences(self, session):
        file_path = DATA_DIR / "conferences_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_conferences_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_conferences_batch, batch)
        
        print(f"Loaded conferences")
    
    @staticmethod
    def _create_conferences_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (c:Conference {
            conferenceId: row.conferenceId,
            name: row.name
        })
        """
        tx.run(query, batch=batch)
    
    def _load_journals(self, session):
        file_path = DATA_DIR / "journals_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_journals_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_journals_batch, batch)
        
        print(f"Loaded journals")
    
    @staticmethod
    def _create_journals_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (j:Journal {
            journalId: row.journalId,
            name: row.name
        })
        """
        tx.run(query, batch=batch)
    
    def _load_workshops(self, session):
        file_path = DATA_DIR / "workshops_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_workshops_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_workshops_batch, batch)
        
        print(f"Loaded workshops")
    
    @staticmethod
    def _create_workshops_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (w:Workshop {
            workshopId: row.workshopId,
            name: row.name
        })
        """
        tx.run(query, batch=batch)
    
    def _load_editions(self, session):
        file_path = DATA_DIR / "editions_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                row['city'] = random.choice(CITIES) if not row.get('city') else row['city']
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_editions_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_editions_batch, batch)
        
        print(f"Loaded editions with synthetic cities")
    
    @staticmethod
    def _create_editions_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (e:Edition {
            editionId: row.editionId,
            editionNumber: toInteger(row.editionNumber),
            year: toInteger(row.year),
            city: row.city
        })
        """
        tx.run(query, batch=batch)
    
    def _load_proceedings(self, session):
        file_path = DATA_DIR / "proceedings_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_proceedings_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_proceedings_batch, batch)
        
        print(f"Loaded proceedings")
    
    @staticmethod
    def _create_proceedings_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (p:Proceeding {
            proceedingId: row.proceedingId
        })
        """
        tx.run(query, batch=batch)
    
    def _load_volumes(self, session):
        file_path = DATA_DIR / "volumes_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_volumes_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_volumes_batch, batch)
        
        print(f"Loaded volumes")
    
    @staticmethod
    def _create_volumes_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (v:Volume {
            volumeId: row.volumeId,
            volumeNumber: toInteger(row.volumeNumber),
            year: toInteger(row.year)
        })
        """
        tx.run(query, batch=batch)
    
    def _load_topics(self, session):
        file_path = DATA_DIR / "topics_nodes.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_topics_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_topics_batch, batch)
        
        print(f"Loaded topics")
    
    @staticmethod
    def _create_topics_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        CREATE (t:Topic {
            topicId: row.topicId,
            name: row.name
        })
        """
        tx.run(query, batch=batch)
    
    def load_relationships(self):
        with self.driver.session() as session:
            self._load_wrote_edges(session)
            self._load_cites_edges(session)
            self._load_about_edges(session)
            self._load_published_in_proceeding(session)
            self._load_published_in_volume(session)
            self._load_has_edition(session)
            self._load_has_volume(session)
            self._load_publishes(session)
            self._assign_reviewers(session)
    
    def _load_wrote_edges(self, session):
        file_path = DATA_DIR / "wrote_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_wrote_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_wrote_batch, batch)
        
        print(f"Loaded WRITES relationships")
    
    @staticmethod
    def _create_wrote_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (a:Author {authorId: row.from})
        MATCH (p:Paper {paperId: row.to})
        MERGE (a)-[:WRITES {corresponding: row.corresponding = 'true'}]->(p)
        """
        tx.run(query, batch=batch)
    
    def _load_cites_edges(self, session):
        file_path = DATA_DIR / "cites_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_cites_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_cites_batch, batch)
        
        print(f"Loaded CITES relationships")
    
    @staticmethod
    def _create_cites_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (p1:Paper {paperId: row.from})
        MATCH (p2:Paper {paperId: row.to})
        MERGE (p1)-[:CITES]->(p2)
        """
        tx.run(query, batch=batch)
    
    def _load_about_edges(self, session):
        file_path = DATA_DIR / "about_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_about_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_about_batch, batch)
        
        print(f"Loaded ABOUT relationships")
    
    @staticmethod
    def _create_about_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (p:Paper {paperId: row.from})
        MATCH (t:Topic {topicId: row.to})
        MERGE (p)-[:ABOUT]->(t)
        """
        tx.run(query, batch=batch)
    
    def _load_published_in_proceeding(self, session):
        file_path = DATA_DIR / "published_in_proceeding_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_published_proceeding_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_published_proceeding_batch, batch)
        
        print(f"Loaded PUBLISHED_IN (Proceeding) relationships")
    
    @staticmethod
    def _create_published_proceeding_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (p:Paper {paperId: row.from})
        MATCH (pr:Proceeding {proceedingId: row.to})
        MERGE (p)-[:PUBLISHED_IN]->(pr)
        """
        tx.run(query, batch=batch)
    
    def _load_published_in_volume(self, session):
        file_path = DATA_DIR / "published_in_volume_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_published_volume_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_published_volume_batch, batch)
        
        print(f"Loaded PUBLISHED_IN (Volume) relationships")
    
    @staticmethod
    def _create_published_volume_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (p:Paper {paperId: row.from})
        MATCH (v:Volume {volumeId: row.to})
        MERGE (p)-[:PUBLISHED_IN]->(v)
        """
        tx.run(query, batch=batch)
    
    def _load_has_edition(self, session):
        file_path = DATA_DIR / "has_edition_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_has_edition_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_has_edition_batch, batch)
        
        print(f"Loaded HAS_EDITION relationships")
    
    @staticmethod
    def _create_has_edition_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        OPTIONAL MATCH (c:Conference {conferenceId: row.from})
        OPTIONAL MATCH (w:Workshop {workshopId: row.from})
        MATCH (e:Edition {editionId: row.to})
        FOREACH (ignoreMe IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
            MERGE (c)-[:HAS_EDITION]->(e)
        )
        FOREACH (ignoreMe IN CASE WHEN w IS NOT NULL THEN [1] ELSE [] END |
            MERGE (w)-[:HAS_EDITION]->(e)
        )
        """
        tx.run(query, batch=batch)
    
    def _load_publishes(self, session):
        file_path = DATA_DIR / "publishes_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_publishes_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_publishes_batch, batch)
        
        print(f"Loaded PUBLISHES relationships")
    
    @staticmethod
    def _create_publishes_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (e:Edition {editionId: row.from})
        MATCH (pr:Proceeding {proceedingId: row.to})
        MERGE (e)-[:PUBLISHES]->(pr)
        """
        tx.run(query, batch=batch)
    
    def _assign_reviewers(self, session):
        print("Assigning reviewers to papers...")
        session.execute_write(self._create_reviewer_relationships)
        print("Loaded REVIEWS relationships")
    
    @staticmethod
    def _create_reviewer_relationships(tx):
        query = """
        MATCH (p:Paper)
        MATCH (p)<-[:WRITES]-(paperAuthor:Author)
        WITH p, collect(DISTINCT paperAuthor) AS paperAuthors
        
        MATCH (potentialReviewer:Author)
        WHERE NOT potentialReviewer IN paperAuthors
        WITH p, potentialReviewer, rand() AS r
        ORDER BY r
        WITH p, collect(potentialReviewer)[0..3] AS reviewers
        
        UNWIND reviewers AS reviewer
        MERGE (reviewer)-[:REVIEWS]->(p)
        """
        tx.run(query)
    
    def _load_has_volume(self, session):
        file_path = DATA_DIR / "has_volume_edges.csv"
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= 1000:
                    session.execute_write(self._create_has_volume_batch, batch)
                    batch = []
            if batch:
                session.execute_write(self._create_has_volume_batch, batch)
        
        print(f"Loaded HAS_VOLUME relationships")
    
    @staticmethod
    def _create_has_volume_batch(tx, batch):
        query = """
        UNWIND $batch AS row
        MATCH (j:Journal {journalId: row.from})
        MATCH (v:Volume {volumeId: row.to})
        MERGE (j)-[:HAS_VOLUME]->(v)
        """
        tx.run(query, batch=batch)
 
def main():
    loader = Neo4jDataLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("Starting data load...")
        
        loader.clear_database()
        loader.create_constraints()
        
        print("\nLoading nodes...")
        loader.load_nodes()
        
        print("\nLoading relationships...")
        loader.load_relationships()
        
        print("\nData load complete!")
        
    finally:
        loader.close()
 
if __name__ == "__main__":
    main()