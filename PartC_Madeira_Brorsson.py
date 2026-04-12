from neo4j import GraphDatabase
import os

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = os.environ["NEO4J_PASSWORD"]

def define_constraints(tx):
    tx.run("""
        CREATE CONSTRAINT community_name IF NOT EXISTS
        FOR (c:Community) REQUIRE c.name IS UNIQUE
    """)
    tx.run("""
        CREATE CONSTRAINT topic_name IF NOT EXISTS
        FOR (t:Topic) REQUIRE t.name IS UNIQUE
    """)

def define_database_community(tx):
    tx.run("""
        MERGE (c:Community {name: "Database"})
        WITH c, [
            "data management",
            "indexing",
            "data modeling",
            "big data",
            "data processing",
            "data storage",
            "data querying"
        ] AS dbTopics
        UNWIND dbTopics AS topicName
        MERGE (t:Topic {name: topicName})
        MERGE (c)-[:DEFINED_BY]->(t)
        WITH t, toLower(t.name) AS keyword
        MATCH (p:Paper)
        WHERE p.abstract IS NOT NULL
        AND (toLower(p.title) CONTAINS keyword OR toLower(p.abstract) CONTAINS keyword)
        MERGE (p)-[:ABOUT]->(t);
    """)


def identify_database_venues(tx):
    tx.run("""
        MATCH (c:Community {name: "Database"})
        CALL (c){
            WITH c
            MATCH (v)
            WHERE v:Conference OR v:Workshop
            MATCH (v)-[:HAS_EDITION]->(:Edition)-[:PUBLISHES]->(pr:Proceeding)
            MATCH (p:Paper)-[:PUBLISHED_IN]->(pr)
            OPTIONAL MATCH (p)-[:ABOUT]->(t:Topic)<-[:DEFINED_BY]-(c)
            WITH c, v,
                count(DISTINCT p) AS totalPapers,
                count(DISTINCT CASE WHEN t IS NOT NULL THEN p END) AS communityPapers
            WHERE totalPapers > 0 AND (1.0 * communityPapers / totalPapers) >= 0.9
            MERGE (v)-[r:BELONGS_TO_COMMUNITY]->(c)
            RETURN count(*) AS venueAssignments
        }
        WITH c, coalesce(venueAssignments, 0) AS venueAssignments
        CALL (c){
            WITH c
            MATCH (j:Journal)-[:HAS_VOLUME]->(vol:Volume)
            MATCH (p:Paper)-[:PUBLISHED_IN]->(vol)
            OPTIONAL MATCH (p)-[:ABOUT]->(t:Topic)<-[:DEFINED_BY]-(c)
            WITH c, j,
                count(DISTINCT p) AS totalPapers,
                count(DISTINCT CASE WHEN t IS NOT NULL THEN p END) AS communityPapers
            WHERE totalPapers > 0 AND (1.0 * communityPapers / totalPapers) >= 0.9
            MERGE (j)-[r:BELONGS_TO_COMMUNITY]->(c)
            RETURN count(*) AS journalAssignments
        }
        RETURN venueAssignments,
            coalesce(journalAssignments, 0) AS journalAssignments;
    """)


def identify_top_100_database_papers(tx):
    tx.run("""
        MATCH (c:Community {name: "Database"})
        CALL (c) {
            WITH c
            MATCH (v)-[:BELONGS_TO_COMMUNITY]->(c)
            WHERE v:Conference OR v:Workshop
            MATCH (v)-[:HAS_EDITION]->(:Edition)-[:PUBLISHES]->(pr:Proceeding)
            MATCH (p:Paper)-[:PUBLISHED_IN]->(pr)
            RETURN DISTINCT p
            UNION
            WITH c
            MATCH (j:Journal)-[:BELONGS_TO_COMMUNITY]->(c)
            MATCH (j)-[:HAS_VOLUME]->(vol:Volume)
            MATCH (p:Paper)-[:PUBLISHED_IN]->(vol)
            RETURN DISTINCT p
        }
        WITH c, collect(DISTINCT p) AS communityPapers
        UNWIND communityPapers AS p
        OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
        WHERE citing IN communityPapers
        WITH c, p, count(DISTINCT citing) AS communityCitationCount
        ORDER BY communityCitationCount DESC, p.title ASC
        LIMIT 100
        WITH c, collect({paper: p, cites: communityCitationCount}) AS topPapers
        UNWIND range(0, size(topPapers) - 1) AS i
        WITH c, i, topPapers[i] AS row
        WITH c, i, row.paper AS p, row.cites AS cites
        MERGE (p)-[r:IN_TOP_COMMUNITY_PAPERS]->(c)
        SET r.rank = i + 1
        RETURN p.title AS paper,
            cites AS communityCitationCount,
            i + 1 AS rank
        ORDER BY rank;
    """)

def identify_reviewer_candidates_and_gurus(tx):
    tx.run("""
        MATCH (c:Community {name: "Database"})
        MATCH (a:Author)-[:WRITES]->(p:Paper)-[:IN_TOP_COMMUNITY_PAPERS]->(c)
        WITH c, a, count(DISTINCT p) AS topPaperCount
        MERGE (a)-[r:GOOD_REVIEWER_MATCH_FOR]->(c)
        SET r.topPaperCount = topPaperCount
        FOREACH (_ IN CASE WHEN topPaperCount >= 2 THEN [1] ELSE [] END |
            MERGE (a)-[g:GURU_IN]->(c)
            SET g.topPaperCount = topPaperCount
        )
        RETURN count(DISTINCT a) AS processed;
    """)


def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:
        session.execute_write(define_constraints)
        session.execute_write(define_database_community)
        session.execute_write(identify_database_venues)
        session.execute_write(identify_top_100_database_papers)
        session.execute_write(identify_reviewer_candidates_and_gurus)

    driver.close()


if __name__ == "__main__":
    main()