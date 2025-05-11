from neo4j import GraphDatabase

class Interface:

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def deleteProjection(self):
        query = """CALL gds.graph.drop('TripGraph') YIELD graphName;"""
        with self._driver.session() as session:
            session.run(query)

    def pagerank(self, max_iter, weight_property):
        query1 = """CALL gds.graph.project(
                        'TripGraph',
                        'Location',
                        {
                            TRIP: {
                                properties: 'distance'
                            }
                        })"""
        with self._driver.session() as session:
            session.run(query1)

        query2 = f"""
            CALL gds.pageRank.stream('TripGraph', {{
                maxIterations: {max_iter},
                dampingFactor: 0.85,
                relationshipWeightProperty: '{weight_property}'
            }})
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS name, score
            ORDER BY score DESC, name ASC
        """

        scores = None

        with self._driver.session() as session:
            response = session.run(query2)
            scores = [i for i in response]

        self.deleteProjection()

        if scores and len(scores) > 0:
            max_score_node = scores[0]
            min_score_node = scores[-1]
            return max_score_node, min_score_node
        else:
            return None, None

    def bfs(self, start_node, end_node):
        with self._driver.session() as session:
            queue = [(start_node, [{'name': start_node}])]
            visited = set()

            while queue:
                current_node, path = queue.pop(0)
                if current_node == end_node:
                    return [{'path': path}]

                visited.add(current_node)

                query = """
                    MATCH ({name: $current_node})-[:TRIP]->(neighbor)
                    RETURN neighbor.name AS neighbor_name
                """
                result = session.run(query, current_node=current_node)

                for record in result:
                    neighbor = record["neighbor_name"]
                    if neighbor not in visited:
                        queue.append((neighbor, path + [{'name': neighbor}]))
                        visited.add(neighbor)

        return []
