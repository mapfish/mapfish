# 
# Copyright (c) 2008-2011 Camptocamp.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Camptocamp nor the names of its contributors may 
#    be used to endorse or promote products derived from this software 
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# SELECT * FROM shortest_path('SELECT gid AS id, node1_id::int4 AS source, node2_id::int4 AS target, 1.0::float8 AS cost FROM lines2', 0, 0, false, false);
def shortest_path(engine, sql, source_id, target_id,
                  directed = False, has_reverse_cost = False):
    """Calculates the shortest path using the Dijkstra algorithm of the library pgrouting.
    Returns an array of: vertex_id, edge_id, cost
    
    see: http://pgrouting.postlbs.org/wiki/Dijkstra
    """
    return engine.execute("SELECT * FROM \
                           shortest_path('%(sql)s', %(source_id)s, %(target_id)s, \
                                          %(directed)s, %(has_reverse_cost)s)"
                          %{'sql': sql.replace("'", r"''"),
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
