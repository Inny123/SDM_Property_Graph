from neo4j import GraphDatabase
import random

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Fuckth1ssh1t"

ORGANIZATIONS = [
    "MIT", "Stanford University", "UC Berkeley", "Carnegie Mellon University",
    "Oxford University", "ETH Zurich", "Google Research", "Microsoft Research",
    "Meta AI Research", "OpenAI"
]

class Neo4jEvolution:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def transform_reviews_to_nodes(self):
        """Transform (Author)-[:REVIEWS]->(Paper) to (Author)-[:SUBMITS_REVIEW]->(Review)-[:REVIEWS]->(Paper)"""
        with self.driver.session() as session:
            print("Creating Review nodes from existing REVIEWS relationships...")
            session.execute_write(self._create_review_nodes_from_relationships)
            print("Deleting old REVIEWS relationships...")
            session.execute_write(self._delete_old_reviews)
    
    @staticmethod
    def _create_review_nodes_from_relationships(tx):
        query = """
        MATCH (reviewer:Author)-[old:REVIEWS]->(paper:Paper)
        
        WITH reviewer, paper, 
             ['accept', 'reject', 'revise'] AS decisions
        
        CREATE (review:Review {
            reviewId: reviewer.authorId + '_review_' + paper.paperId,
            content: 'Review of "' + paper.title + '" by ' + reviewer.name + '. This paper presents interesting work in the field.',
            decision: decisions[toInteger(rand() * size(decisions))]
        })
        
        CREATE (reviewer)-[:SUBMITS_REVIEW]->(review)
        CREATE (review)-[:REVIEWS]->(paper)
        
        RETURN count(review) AS reviewsCreated
        """
        result = tx.run(query)
        record = result.single()
        print(f"Created {record['reviewsCreated']} Review nodes")
    
    @staticmethod
    def _delete_old_reviews(tx):
        query = """
        MATCH (reviewer:Author)-[old:REVIEWS]->(paper:Paper)
        DELETE old
        RETURN count(old) AS deletedRelationships
        """
        result = tx.run(query)
        record = result.single()
        print(f"Deleted {record['deletedRelationships']} old REVIEWS relationships")
    
    def add_organizations(self):
        with self.driver.session() as session:
            print("Creating Organization nodes...")
            session.execute_write(self._create_organization_nodes)
            print("Linking authors to organizations...")
            session.execute_write(self._link_authors_to_organizations)
    
    @staticmethod
    def _create_organization_nodes(tx):
        for org in ORGANIZATIONS:
            query = """
            CREATE (o:Organization {
                organizationId: $org_id,
                name: $name,
                type: CASE 
                    WHEN $name CONTAINS 'University' THEN 'university'
                    ELSE 'company'
                END
            })
            """
            tx.run(query, 
                   org_id=f"org::{org.lower().replace(' ', '_')}", 
                   name=org)
        print(f"Created {len(ORGANIZATIONS)} organizations")
    
    @staticmethod
    def _link_authors_to_organizations(tx):
        query = """
        MATCH (a:Author)
        MATCH (o:Organization)
        WITH a, o, rand() AS r
        WHERE r < 0.3
        CREATE (a)-[:AFFILIATED_WITH]->(o)
        RETURN count(*) AS affiliations
        """
        result = tx.run(query)
        record = result.single()
        print(f"Created {record['affiliations']} AFFILIATED_WITH relationships")

def main():
    db = Neo4jEvolution(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("=== Starting Schema Evolution (Part A.3) ===\n")
        
        print("Step 1: Transform review model...")
        db.transform_reviews_to_nodes()
        
        print("\nStep 2: Add organizations and affiliations...")
        db.add_organizations()
        
        print("\n=== Schema evolution complete! ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()