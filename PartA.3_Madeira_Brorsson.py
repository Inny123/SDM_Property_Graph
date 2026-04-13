from neo4j import GraphDatabase
import os

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = os.environ.get("NEO4J_PASSWORD")


def create_constraints(tx):
    tx.run("""
        CREATE CONSTRAINT review_id IF NOT EXISTS
        FOR (r:Review) REQUIRE r.id IS UNIQUE
    """)
    tx.run("""
        CREATE CONSTRAINT organization_id IF NOT EXISTS
        FOR (o:Organization) REQUIRE o.id IS UNIQUE
    """)


def set_required_reviews(tx):
    tx.run("""
        MATCH (v)
        WHERE v:Conference OR v:Workshop OR v:Journal
        SET v.requiredReviews = 3
    """)


def migrate_review_relationships(tx):
    tx.run("""
        MATCH (a:Author)-[old:REVIEWS]->(p:Paper)
        WITH a, old, p,
             CASE
                 WHEN rand() < 0.999 THEN "accept"
                 ELSE "reject"
             END AS generatedDecision
        CREATE (rev:Review {
            id: randomUUID(),
            content: CASE
                WHEN generatedDecision = "accept"
                THEN "Synthetic review: the paper is relevant and should be accepted."
                ELSE "Synthetic review: the paper needs improvement and should be rejected."
            END,
            decision: generatedDecision
        })
        CREATE (a)-[:SUBMITS_REVIEW]->(rev)
        CREATE (rev)-[:REVIEWS]->(p)
        DELETE old
    """)


def create_synthetic_organizations(tx):
    tx.run("""
        UNWIND [
            {id: "org_001", name: "Stanford University", type: "university"},
            {id: "org_002", name: "MIT", type: "university"},
            {id: "org_003", name: "Oxford University", type: "university"},
            {id: "org_004", name: "Google", type: "company"},
            {id: "org_005", name: "Microsoft", type: "company"},
            {id: "org_006", name: "Amazon", type: "company"},
            {id: "org_007", name: "Meta", type: "company"}
        ] AS org
        MERGE (o:Organization {id: org.id})
        SET o.name = org.name,
            o.type = org.type
    """)


def assign_authors_to_organizations(tx):
    tx.run("""
        MATCH (a:Author)
        WHERE NOT (a)-[:AFFILIATED_WITH]->(:Organization)
        WITH a, toInteger(rand() * 7) AS idx
        MATCH (o:Organization)
        WITH a, idx, o
        ORDER BY o.id
        WITH a, idx, collect(o) AS orgs
        WITH a, orgs[idx] AS org
        MERGE (a)-[:AFFILIATED_WITH]->(org)
    """)


def remove_publication_for_invalid_papers(tx):
    tx.run("""
        MATCH (p:Paper)-[pub:PUBLISHED_IN]->(container)
        OPTIONAL MATCH (p)<-[:REVIEWS]-(r:Review)

        OPTIONAL MATCH (container)<-[:PUBLISHES]-(e:Edition)<-[:HAS_EDITION]-(venue1)
        WHERE venue1:Conference OR venue1:Workshop

        OPTIONAL MATCH (container)<-[:HAS_VOLUME]-(venue2:Journal)

        WITH p, pub,
             count(r) AS reviewCount,
             sum(CASE WHEN r.decision = "accept" THEN 1 ELSE 0 END) AS acceptCount,
             coalesce(venue1.requiredReviews, venue2.requiredReviews, 3) AS requiredReviews
        WHERE reviewCount < requiredReviews
           OR acceptCount <= reviewCount - acceptCount
        DELETE pub
    """)


def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:
        session.execute_write(create_constraints)
        session.execute_write(set_required_reviews)
        session.execute_write(migrate_review_relationships)
        session.execute_write(create_synthetic_organizations)
        session.execute_write(assign_authors_to_organizations)
        session.execute_write(remove_publication_for_invalid_papers)

    driver.close()


if __name__ == "__main__":
    main()