"""
Genetic Algorithm for solving Selective Travelling Salesman Problem.

:Author: Fabio Scala <fabio.scala@gmail.com>
"""


import logging
import random
import time

import numpy


class GaSolver(object):

    """ Genetic algorithm based on `A. Piwonska and J. Koszelew selective travelling salesman algorithm <http://dl.acm.org/citation.cfm?id=2029846>`_
    :param start: The index of the tour starting point in distances.
    :type start: int

    :param end: The index of the tour ending point in distances. If end equals start, a different approach for generation of the initial tours (population) is used.
    :type end: int

    :param distances: A distance matrix for all the available points.
    :type distances: numpy.ndarray

    :param max_cost: The maximum cost (sum of distances) a tour is allowed to have.
    :type max_cost: float

    :param profits: Optional profits associated with each point in the distance matrix. No profits are used (equal) if omitted.
    :type profits: numpy.ndarray

    :param population_size: The number of solutions to be used during calculation. A higher number can lead to better results but will run longer.
    :type populaiton_size: int

    :param tournament_size: The group size of random individuals for selection. The higher this value, the faster it will converge but also comes with less different solutions and a greater chance to get stuck in local minimas.
    :type tournament_size: int

    :param min_generations: The minimum number of iterations to run the algorithm for.
    :type min_generations: int

    :param max_generation: The maximum number of iterations to run the algorithm for.
    :type max_generation: int

    :param termination_threshold: If fitness in terms of costs does no longer improve more than the specified value, the algorithm will stop. (1 = 100%). E.g. with termination_threshold = 0.01 if the costs do no improve at least 1% it will stop.
    :type termination_threshold: float

    :param max_runtime: Maximum runtime in milliseconds before stopping the algorithm regardless of a good or bad fitness.
    :type termination_threshold: int
    """

    def __init__(self, start, end, distances, max_cost, profits=None, population_size=1000, tournament_size=5, min_generations=5, max_generations=200, termination_threshold=.01, max_runtime=10000):
        self.start = start
        self.end = end
        self.distances = distances
        self.max_cost = max_cost
        self.profits = profits
        self.population_size = population_size
        self.tournament_size = tournament_size
        self.min_generations = min_generations
        self.max_generations = max_generations
        self.termination_threshold = termination_threshold
        self.max_runtime = max_runtime

        self._init_population = self._init_population_loop if start == end else self._init_population_tour

    def _init_population_loop(self):
        """ Generates initial population for the "tsp" (loop) version (start equals end)
            * Start from the specified starting point
            * Add random points to the tour until the cost max_cost/2 is reached
            * Return back to the start using the same points
        """
        max_init_cost = 0.5 * self.max_cost

        paths = self.population['path']
        costs = self.population['cost']

        for i in xrange(self.population_size):
            path = [self.start]
            c = 0
            ind_last = 0
            while True:
                d_from = self.distances[ind_last, :]
                cands = numpy.where((d_from != 0) & (d_from < max_init_cost - c))[0]
                if cands.shape[0] != 0:
                    # ind_next = numpy.random.choice(numpy.argsort(d_from)[:5])
                    ind_next = random.choice(cands)
                    # ind_next = np.random.randint(0, n_pois)
                    if ind_last != ind_next or cands.shape[0] == 1:  # relax condition
                        c += d_from[ind_next]
                        # hop to next
                        path.append(ind_next)
                        ind_last = ind_next
                else:
                    break

            # go back the way we came
            paths[i] = path + path[::-1][-max(0, len(path) - 1):]

            costs[i] = 2 * c

    def _init_population_tour(self):
        """ Generates initial population for the "tour" version (start and end are different point)
            * Fix start end end point
            * Add random points from a set of candidates (candidate to end cannot exceed maximum cost) until no further points can be added
            * Do this for the half of the population and the opposite (from end to start) for the other half.
        """
        paths = self.population['path']
        costs = self.population['cost']
        distances = self.distances

        mid = self.population_size / 2
        for i_from, i_to, start, end in ((0, mid, self.start, self.end), (mid, self.population_size, self.end, self.start)):
            is_reverse = start != self.start

            for i in xrange(i_from, i_to):
                individual = [start]
                c = 0
                ind_last = start

                while True:  # we break manually
                    d_from = distances[ind_last, :]
                    max_cost = self.max_cost - c
                    # only hopping to these points would not exceed max_cost
                    cands = numpy.where((distances[ind_last] + distances[end]) <= max_cost)[0]
                    cands = cands[(cands != end) & (cands != ind_last)]
                    if cands.shape[0] != 0:
                        ind_next = random.choice(cands)
                        if ind_last != ind_next:
                            c += d_from[ind_next]
                            individual.append(ind_next)
                            ind_last = ind_next
                    else:
                        c += d_from[end]
                        individual.append(end)
                        break

                if is_reverse:
                    # if we started from "end", reverse the tour
                    individual = individual[::-1]

                paths[i] = individual
                costs[i] = c

    def _calc_fitness(self, population):
        """ Calculates the fitness for a given population so that it would sort equivalent to: path length descending, cost ascending
        :param population: Population
        :type population: structured population numpy.ndarray
        """
        paths = population['path']
        costs = population['cost']

        path_lens = numpy.array([len(path) for path in paths], int)
        # same as lexsort cost, -len (len desc, cost asc)
        if self.profits is not None:
            profits = [numpy.take(self.profits, p).sum() for p in paths]
            fitness = (profits + path_lens) * self.max_cost
        else:
            fitness = path_lens * self.max_cost

        fitness -= costs

        return fitness

    def _unique_path(self, path):
        """ Removes duplicate points in a tour respecting start and end.
        :param path: Path encoded as list of integers
        :return: List with duplicates removed
        """
        # Tested, faster than numpy.unique
        # http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
        seen = {self.start, self.end}
        seen_add = seen.add
        return [self.start] + [x for x in path[1:-1] if not (x in seen or seen_add(x))] + [self.end]

    def _do_selection(self):
        """ Does the "selection" part of the genetic algorithm.
            * Pick random <tournament_size> indiduals from the population and replace the current individual the fittest of those.
            * Do this for each individual in the population
        """
        population = self.population
        self.offspring = offspring = numpy.zeros(self.population_size, population.dtype)
        population['fitness'] = fitness = self._calc_fitness(population)

        n = self.population_size

        self.fittest[self.current_generation] = tuple(self.population[fitness.argmax()])

        for i, i_samples in ((j, numpy.random.randint(0, n, 10)) for j in xrange(n)):
            fittest = population[i_samples[numpy.argmax(fitness[i_samples])]]
            offspring[i] = tuple(fittest)

        self.population = offspring

    def _iter_couples(self):
        """ Helper generator function to iterate over random couples of the population having used each one only once
        :return: Generator (index, individual)
        """
        n = self.population_size
        population = self.population
        a = range(n)
        random.shuffle(a)
        for i in xrange(0, n, 2):
            i1 = a[i]
            i2 = a[i + 1]
            yield (i1, population[i1]), (i2, population[i2])

    def _do_crossover(self):
        """ Crosses random couples of the population and replaces the individual if the cost constraints of the child is still met.
            * Find common genes in both indivudals
            * Pick a random common gene
            * Switch the parts from the common gene to the end of both individuals
        """
        population = self.population

        for (i_individual, individual), (i_partner, partner) in self._iter_couples():
            common_genes = set(individual['path']).intersection(partner['path']).difference({self.start, self.end})
            if common_genes:
                crossing_gene = random.sample(common_genes, 1)[0]
                # index after crossing point
                i_cross_individual = individual['path'].index(crossing_gene) + 1
                i_cross_partner = partner['path'].index(crossing_gene) + 1

                first_child = individual['path'][:i_cross_individual] + partner['path'][i_cross_partner:]
                second_child = partner['path'][:i_cross_partner] + individual['path'][i_cross_individual:]

                child_cost = self.distances[first_child[:-1], first_child[1:]].sum()
                if child_cost < self.max_cost:
                    population[i_individual]['cost'] = child_cost
                    population[i_individual]['path'] = first_child

                child_cost = self.distances[second_child[:-1], second_child[1:]].sum()
                if child_cost < self.max_cost:
                    population[i_partner]['cost'] = child_cost
                    population[i_partner]['path'] = second_child

    def _do_mutation(self):
        """ Mutates each individual of the population:
            * Remove duplicate points
            * Delete a random gene (point)
            * Pick a random gene
            * Insert as many points as possible while still meeting the cost constraints
        """
        population = self.population

        paths = population['path']
        costs = population['cost']

        for i in xrange(self.population_size):
            path = paths[i]

            if len(path) > 2:
                # remove dups
                path_new = self._unique_path(path)

                cost_new = self.distances[path_new[:-1], path_new[1:]].sum()
                costs[i] = cost_new
                paths[i] = path = path_new

                # remove random point
                i_remove = random.randint(1, len(path) - 2)

                costs[i] = self.distances[path[:-1], path[1:]].sum()
                del path[i_remove]

            i_insert = random.randint(1, len(path) - 1)

            from_ = path[i_insert - 1]

            increments = self.distances[from_, :]
            if self.profits is not None:
                # we have given weights
                i_sorted = numpy.lexsort([increments, -self.profits])
            else:
                i_sorted = numpy.argsort(increments)

            for ins_cand in i_sorted:
                if ins_cand not in path:
                    path_new = list(path)
                    path_new.insert(i_insert, ins_cand)
                    c_temp = self.distances[path_new[:-1], path_new[1:]].sum()
                    if c_temp < self.max_cost:
                        paths[i] = path = path_new
                        costs[i] = c_temp
                    else:
                        break

    def _init(self):
        self.fittest = numpy.zeros(self.max_generations, [('path', 'O'), ('cost', 'f'), ('fitness', 'f')])
        self.population = numpy.zeros(self.population_size, [('path', 'O'), ('cost', 'f'), ('fitness', 'f')])

    def calc_tour(self, last_ng=None):
        """ Runs the genetic algorithm and returns the best tour
        .. warning:: Never use all generations for comparisons. The first generation is usually very good in its fitness because of the symmetries of the initial population.

        :param last_ng: The last n generations to compare
        :type  param: int
        :return: Ordered indices of the tour points in the distance matrix
        :rtype: list
        """
        if self.max_cost < self.distances[self.start, self.end]:
            return [], 0

        self._init()
        self._run()
        last_ng = last_ng or self.current_generation
        group = self.fittest[self.current_generation - last_ng:self.current_generation]
        fittest = group[group['fitness'].argmax()]
        return fittest['path'], fittest['cost']

    def _iter_generations(self):
        """ Generator which controls number of generations/iterations based on fitness improvement/convergence and maximum number of iterations or runtime.
        """
        max_runtime_s = self.max_runtime / 1000.0
        start_time = time.time()
        compare_generations = min(self.min_generations, 5)
        for generation in xrange(self.max_generations):
            if time.time() - start_time > max_runtime_s:
                logging.info('Ending Genetic Algorithnm after {}ms'.format(self.max_runtime))
                break

            if generation > self.min_generations:
                # basically compare the fittest of last compare_generations with all others and see if fitness has improves

                last_ng = self.fittest[generation - compare_generations - 1:generation - 1]
                fittest_ng = last_ng[last_ng['fitness'].argmax()]

                # rest but at least 1, so no -1 in index
                compare_to = self.fittest[:generation - compare_generations]
                fittest_compare_to = compare_to[compare_to['fitness'].argmax()]

                delta_fitness = fittest_ng['fitness'] - fittest_compare_to['fitness']
                delta_cost = last_ng['cost'].max() - last_ng['cost'].min()

                # fitness improvement is less than max_cost -> path length remained the same. see _calc_fitness()
                # path len constant & costs did not improve (lowered) in the last compare_generations iterations, stop!
                if delta_fitness < self.max_cost and (delta_cost / self.max_cost < self.termination_threshold):
                    logging.info('Ending Genetic Algorithm after desired convergence {}, {}'.format(delta_fitness, delta_cost / self.max_cost))
                    break

            yield generation

    def _run(self):
        """ Runs the main loop (generations) of the genetic algorithm. Should not be called directly.
        """
        self._init_population()
        self.current_generation = 0
        self._do_selection()

        for generation in self._iter_generations():
            self.current_generation = generation
            self._do_crossover()
            self._do_mutation()
            # we do selection at the end, which is at the same time the start of a potentially next generation
            # like this we have a "good" generation with updated fitness values at the end of the algorithm
            self._do_selection()


# testing & dev. playground
if __name__ == '__main__':
    def plot_tour(path, points):
        import matplotlib.pyplot as plt

        x = []
        y = []

        for i in path:
            x.append(points[i][0])
            y.append(points[i][1])

        plt.plot(*zip(*points[1:]), marker='o', color='b', ls='')
        plt.plot(x, y, 'go')

        arrow_scale = float(max(x)) / float(100)

        for i in range(0, len(x) - 1):
            plt.arrow(x[i], y[i], (x[i + 1] - x[i]), (y[i + 1] - y[i]), head_width=arrow_scale,
                      color='g', length_includes_head=True)

        plt.plot(points[path[0]][0], points[path[0]][1], marker='o', color='r', ls='')
        plt.plot(points[path[-1]][0], points[path[-1]][1], marker='o', color='r', ls='')
#         plt.xlim(0, max(x) * 1.1)
#         plt.ylim(0, max(y) * 1.1)

        plt.show()

    def test(start=0, end=0, t_size=5, population_size=1000, n_coords=500, n_points=400, max_cost=1000, plot=False, plot_convergence=False, termination_threshold=.01):
        import scipy.spatial.distance as distance

        points = numpy.random.randint(0, n_coords, (n_points, 2))

        distances = distance.squareform(distance.pdist(points))
        ga = GaSolver(population_size=population_size, tournament_size=t_size,
                      max_cost=max_cost, start=start, end=end, distances=distances, termination_threshold=termination_threshold)

        path = ga.calc_tour()

        numpy.testing.assert_array_less(ga.population['cost'], max_cost)
        numpy.testing.assert_array_less(ga.fittest['cost'], max_cost)
        assert all([p[0] == start for p in ga.population['path']])
        assert all([p[-1] == end for p in ga.population['path']])

#         lens = numpy.array([len(ind['path']) for ind in ga.population])
#         costs = numpy.array([ind['cost'] for ind in ga.population])
#         len_winner = numpy.lexsort([costs, -lens])[0]

        if plot:
            print ga.fittest[ga.current_generation]
            plot_tour(path, points)

        if plot_convergence:
            import matplotlib.pyplot as plt
            plt.plot(ga.fittest['fitness'])
            plt.show()

        return ga
