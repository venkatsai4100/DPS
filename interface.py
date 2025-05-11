from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        # Use bolt:// for a direct connection.
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def bfs(self, start_node, target_node):
        """
        Compute a BFS using Neo4j's shortestPath function.
        
        Args:
            start_node (int): The starting location ID.
            target_node (int): The target location ID.
        
        Returns:
            List of records with the 'path' (a list of location names) and 'hops' count.
        """
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (start:Location {name: $start_node}), (target:Location {name: $target_node})
                MATCH p = shortestPath((start)-[:TRIP*]-(target))
                RETURN [n IN nodes(p) | n.name] AS path, length(p) AS hops
                """, start_node=start_node, target_node=target_node)
            return result.data()

    def pagerank(self, max_iterations, weight_property):
        """
        Compute PageRank using the Neo4j Graph Data Science (GDS) library.
        
        Args:
            max_iterations (int): Maximum iterations for PageRank.
            weight_property (str): The relationship property to use as the weight.
        
        Returns:
            A list of dictionaries with 'name' (location ID) and 'score'.
        """
        with self._driver.session() as session:
            # Inline the weight_property and max_iterations into the query.
            # Note: we add "type: 'TRIP'" inside the relationshipProjection for the TRIP relationship.
            query = f"""
                CALL gds.pageRank.stream({{
                    nodeProjection: 'Location',
                    relationshipProjection: {{
                        TRIP: {{
                            type: 'TRIP',
                            properties: '{weight_property}'
                        }}
                    }},
                    maxIterations: {max_iterations},
                    dampingFactor: 0.85
                }})
                YIELD nodeId, score
                RETURN toInteger(gds.util.asNode(nodeId).name) AS name, score
                ORDER BY score DESC
            """
            result = session.run(query)
            return result.data()

# If run directly, perform simple tests.
if __name__ == "__main__":
    iface = Interface("bolt://localhost:7687", "neo4j", "project1phase1")
    bfs_result = iface.bfs(159, 212)
    if bfs_result:
        print("BFS result:", bfs_result)
    pr_result = iface.pagerank(20, "distance")
    if pr_result:
        print("PageRank highest:", pr_result[0])
        print("PageRank lowest:", pr_result[-1])
    iface.close()