import os

from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

class GraphAlgorithms:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_graph_projection(self):
        query = """
        CALL gds.graph.project(
            'citation-graph',
            'Paper',
            'CITES'
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return dict(result.single())
    
    def run_pagerank(self, limit=20):
        query = """
        CALL gds.pageRank.stream('citation-graph')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).title AS Paper,
               gds.util.asNode(nodeId).year AS Year,
               score AS InfluenceScore
        ORDER BY score DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def run_louvain(self, limit=10):
        query = """
        CALL gds.louvain.stream('citation-graph')
        YIELD nodeId, communityId
        WITH communityId, collect(gds.util.asNode(nodeId).title) AS papers
        RETURN communityId AS CommunityID,
               size(papers) AS PaperCount,
               papers[0..5] AS SamplePapers
        ORDER BY PaperCount DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def drop_graph_projection(self):
        query = """
        CALL gds.graph.drop('citation-graph')
        YIELD graphName
        RETURN graphName
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return dict(result.single())

def main():
    gds = GraphAlgorithms(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("Creating graph projection...")
        projection_info = gds.create_graph_projection()
        print(json.dumps(projection_info, indent=2))
        
        print("\nRunning PageRank algorithm...")
        pagerank_results = gds.run_pagerank(limit=20)
        print(json.dumps(pagerank_results, indent=2))
        
        print("\nRunning Louvain community detection...")
        louvain_results = gds.run_louvain(limit=10)
        print(json.dumps(louvain_results, indent=2))
        
        print("\nDropping graph projection...")
        drop_info = gds.drop_graph_projection()
        print(json.dumps(drop_info, indent=2))
        
    finally:
        gds.close()

if __name__ == "__main__":
    main()
