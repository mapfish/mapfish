# 
# Copyright (C) 2009  Camptocamp
#  
# This file is part of MapFish Server
#  
# MapFish Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# MapFish Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with MapFish Server.  If not, see <http://www.gnu.org/licenses/>.
#


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
