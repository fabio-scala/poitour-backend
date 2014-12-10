"""
Unit tests for genetic algorithm

:Author:  Fabio Scala <fabio.scala@gmail.com>
"""
import time
import unittest

import numpy

from app.routing import stsp
import scipy.spatial.distance as distance


class GeneticAlgorithmTestCase(unittest.TestCase):

    START = 0
    END = 1
    MAX_GENERATIONS = 200
    T_SIZE = 5
    POPULATION_SIZE = 500
    N_POINTS = 200
    N_COORDS = 400
    MAX_COST = 1000

    def create_ga(self, start=START, end=END, max_generations=MAX_GENERATIONS, t_size=T_SIZE, population_size=POPULATION_SIZE, n_coords=N_COORDS, n_points=N_POINTS, max_cost=MAX_COST, points=None, **kw):
        if not points:
            points = numpy.random.randint(0, n_coords, (n_points, 2))

        distances = distance.squareform(distance.pdist(points))

        return stsp.GaSolver(population_size=population_size, tournament_size=t_size,
                             max_cost=max_cost, start=start, end=end, distances=distances, max_generations=max_generations, **kw)

    def test_init_tour(self):
        ga = self.create_ga(start=0, end=1)
        assert ga._init_population == ga._init_population_tour, 'Use the tour initialization method'
        ga._init()
        ga._init_population()
        assert len(ga.population) == self.POPULATION_SIZE, 'Correct population size'
        numpy.testing.assert_array_less(ga.population['cost'], self.MAX_COST, 'Max. cost constraint satisfied')
        assert all([path[0] == 0 for path in ga.population['path']]), 'Correct start point'
        assert all([path[-1] == 1 for path in ga.population['path']]), 'Correct end point'

    def test_init_loop(self):
        ga = self.create_ga(start=0, end=0)
        assert ga._init_population == ga._init_population_loop, 'Uses the TSP/loop initialization method'
        ga._init()
        ga._init_population()
        assert len(ga.population) == self.POPULATION_SIZE, 'Correct population size'
        numpy.testing.assert_array_less(ga.population['cost'], self.MAX_COST, 'Max. cost constraint satisfied')
        assert all([path[0] == 0 for path in ga.population['path']]), 'Correct starting point'
        assert all([path[-1] == 0 for path in ga.population['path']]), 'Correct end point'

    def test_unique_path(self):
        ga = self.create_ga(start=0, end=0)
        assert tuple(ga._unique_path([0, 1, 0, 3, 1, 4, 9, 5, 3, 0])) == (0, 1, 3, 4, 9, 5, 0), 'Path contains no duplicates'

        ga = self.create_ga(start=0, end=1)
        assert tuple(ga._unique_path([0, 1, 1, 0, 3, 1, 4, 9, 5, 3, 1])) == (0, 3, 4, 9, 5, 1), 'Path contains no duplicates'

    def test_calc_fitness(self):
        ga = self.create_ga(start=0, end=0, population_size=1, max_cost=100)
        ga._init()
        ga.population['path'][0] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 0]
        ga.population['cost'][0] = 100
        ga._calc_fitness(ga.population)

    def test_calc_tour(self):
        """ Overall test """
        ga = self.create_ga()
        ga.calc_tour(1)
        numpy.testing.assert_array_less(ga.population['cost'], self.MAX_COST)
        numpy.testing.assert_array_less(ga.fittest['cost'], self.MAX_COST)
        assert all([path[0] == self.START for path in ga.population['path']])
        assert all([path[-1] == self.END for path in ga.population['path']])

    def test_max_runtime(self):
        ga = self.create_ga(max_runtime=1000)
        start = time.time()
        ga.calc_tour()
        end = time.time()
        # 2x grace, overheads
        assert end - start < 2, 'Should not run longer that max_runtime'


if __name__ == "__main__":
    # import sys;sys.argv = ['', '-v']
    unittest.main()
