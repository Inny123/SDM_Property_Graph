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
        # First try to drop if it exists
        try:
            with self.driver.session() as session:
                session.run("CALL gds.graph.drop('citation-graph', false)")
                print("Dropped existing projection 'citation-graph'")
        except:
            pass  # Projection doesn't exist, that's fine
        
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
    
    def run_pagerank(self, limit=10):
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
    
    def run_louvain_syntactic(self, limit=5):
        """Louvain with syntactic community IDs (arbitrary numbers)"""
        query = """
        CALL gds.louvain.stream('citation-graph')
        YIELD nodeId, communityId
        WITH communityId, collect(gds.util.asNode(nodeId)) AS nodes
        WITH communityId, 
             nodes,
             size(nodes) AS paperCount,
             [n IN nodes | n.title][0..5] AS samplePapers
        ORDER BY paperCount DESC
        LIMIT $limit
        RETURN 'Community ' + toString(communityId) AS CommunityLabel,
               paperCount AS PaperCount,
               samplePapers AS SamplePapers
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def run_louvain_semantic(self, limit=5):
        """Louvain with semantic labels (most common topic per community)"""
        query = """
        CALL gds.louvain.stream('citation-graph')
        YIELD nodeId, communityId
        WITH communityId, gds.util.asNode(nodeId) AS paper
        // Get all topics for papers in this community
        OPTIONAL MATCH (paper)-[:ABOUT]->(topic:Topic)
        // Collect DISTINCT papers first (prevents duplication)
        WITH communityId, 
             collect(DISTINCT paper.title) AS paperTitles,
             collect(topic.name) AS allTopics
        
        WITH communityId,
             paperTitles,
             size(paperTitles) AS paperCount,
             allTopics
        
        WITH communityId,
             paperCount,
             paperTitles,
             head([t IN allTopics WHERE t IS NOT NULL]) AS dominantTopic
        
        ORDER BY paperCount DESC
        LIMIT $limit
        
        RETURN COALESCE(dominantTopic, 'Community ' + toString(communityId)) AS CommunityTopic,
               paperCount AS PaperCount,
               paperTitles[0..5] AS SamplePapers
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
        
        print("\n" + "="*60)
        print("PAGERANK ALGORITHM")
        print("="*60)
        pagerank_results = gds.run_pagerank()
        print(json.dumps(pagerank_results, indent=2))
        
        print("\n" + "="*60)
        print("LOUVAIN COMMUNITY DETECTION - SYNTACTIC (Community IDs)")
        print("="*60)
        louvain_syntactic = gds.run_louvain_syntactic()
        print(json.dumps(louvain_syntactic, indent=2))
        
        print("\n" + "="*60)
        print("LOUVAIN COMMUNITY DETECTION - SEMANTIC (Topic Labels)")
        print("="*60)
        louvain_semantic = gds.run_louvain_semantic()
        print(json.dumps(louvain_semantic, indent=2))
        
        print("\n" + "="*60)
        print("CLEANUP")
        print("="*60)
        drop_info = gds.drop_graph_projection()
        print(json.dumps(drop_info, indent=2))
        
    finally:
        gds.close()
 
if __name__ == "__main__":
    main()