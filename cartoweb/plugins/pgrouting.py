# SELECT * FROM shortest_path('SELECT gid AS id, node1_id::int4 AS source, node2_id::int4 AS target, 1.0::float8 AS cost FROM lines2', 0, 0, false, false);
def shortest_path(engine, sql, source_id, target_id,
                  directed = False, has_reverse_cost = False):
    # return array of: step, vertex_id, edge_id, cost

    return engine.execute("SELECT * FROM \
                           shortest_path('%(sql)s', %(source_id)s, %(target_id)s, \
                                          %(directed)s, %(has_reverse_cost)s) ORDER BY step"
                          %{'sql': sql.replace("'", r"\'"),
                            'source_id': source_id,
                            'target_id': target_id,
                            'directed': directed,
                            'has_reverse_cost': has_reverse_cost}
                          )

def shortest_path_astar(engine, sql, source_id, target_id,
                        directed, has_reverse_cost):
    raise NotImplementedError

def shortest_path_shooting_star(engine, sql, source_id, target_id,
                                directed, has_reverse_cost):
    raise NotImplementedError

def tsp(engine, sql, ids, source_id):
    raise NotImplementedError

def driving_distance(engine, sql, source_id, distance):
    raise NotImplementedError
