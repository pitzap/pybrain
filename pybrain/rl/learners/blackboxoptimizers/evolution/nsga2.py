from scipy import array
from pybrain.rl.learners.blackboxoptimizers.evolution.ga import GA
import collections

__author__ = 'Justin Bayer, Tom Schaul, {justin,tom}@idsia.ch'

# TODO: not very elegant, because of the conversions between tuples and arrays all the time...

class MultiObjectiveGA(GA):
    """ Multi-objective Genetic Algorithm: the fitness is a vector with one entry per objective.
    By default we use NSGA-II selection. """
    
    topproportion = 0.5
    elitism = True
    
    popsize = 100
    mutationStdDev = 1.
        
    def __init__(self, *args, **kwargs):
        """ x0 is assumed to be an array, but then converted to a tuple. 
        The algorithm returns all individuals in the Pareto-front (and their fitnesses). """
        GA.__init__(self, *args, **kwargs)
        self.bestEvaluation = []
        self.bestEvaluable = [tuple(self.x0)]
        self.fitnesses = {}    
    
    def stoppingCriterion(self):
        # TODO: what can be put here?
        return False
    
    def initPopulation(self):
        GA.initPopulation(self)
        self.currentpop = map(tuple, self.currentpop)
         
    def mutated(self, indiv):
        return tuple(GA.mutated(self,array(indiv)))
     
    def oneGeneration(self):
        """ do one generation step """
        # evaluate fitness
        for indiv in self.currentpop:
            if indiv not in self.fitnesses:
                self.fitnesses[indiv] = self.evaluator(array(indiv))
                self.steps += 1
        
        self.allgenerations.append((self.currentpop))
        if self.elitism:    
            self.bestEvaluable = list(non_dominated_front(self.currentpop,
                                                          key=lambda x: self.fitnesses[x]))
        else:
            self.bestEvaluable = list(non_dominated_front(self.currentpop+self.bestEvaluable,
                                                          key=lambda x: self.fitnesses[x]))
        self.bestEvaluation = map(lambda indiv: self.fitnesses[indiv], self.bestEvaluable)
        
        self.produceOffspring()
        
    def select(self):
        return nsga2select(self.currentpop, self.fitnesses, self.selectionSize())    
                
    

def nsga2select(population, fitnesses, survivors):
    """The NSGA-II selection strategy (Deb et al., 2002).
    The number of individuals that survive is given by the survivors parameter."""
    fronts = non_dominated_sort(population,
                                key=lambda x: fitnesses[x])
    individuals = set()
    for front in fronts:
        remaining = survivors - len(individuals)
        if not remaining > 0:
            break
        if len(front) > remaining:
            # If the current front does not fit in the spots left, use those
            # that have the biggest crowding distance.
            crowd_dist = crowding_distance(front, fitnesses)
            front = sorted(front, key=lambda x: crowd_dist[x], reverse=True)
            front = set(front[:remaining])
        individuals |= front
    
    return list(individuals)
 
def crowding_distance(individuals, fitnesses):
    """ Crowding distance-measure for multiple objectives. """
    distances = collections.defaultdict(lambda: 0)
    individuals = list(individuals)
    # Infer the number of objectives by looking at the fitness of the first.
    n_obj = len(fitnesses[individuals[0]])
    for i in xrange(n_obj):
        individuals.sort(key=lambda x: fitnesses[x][i])
        # normalization between 0 and 1.
        normalization = float(fitnesses[individuals[0]][i] - fitnesses[individuals[-1]][i])
        # Make sure the boundary points are always selected.
        distances[individuals[0]] = 1e100
        distances[individuals[-1]] = 1e100
        tripled = zip(individuals, individuals[1:-1], individuals[2:])
        for pre, ind, post in tripled:
            distances[ind] += (fitnesses[pre][i] - fitnesses[post][i]) / normalization
    return distances
 
 
def non_dominated_front(iterable, key=lambda x: x):
    """Return a subset of items from iterable which are not dominated by any
    other item in iterable."""
    items = list(iterable)
    keys = dict((i, key(i)) for i in items)
    dim = len(keys.values()[0])
    if any(dim != len(k) for k in keys.values()):
        raise ValueError("Wrong tuple size.")
 
    # Make a dictionary that holds the items another item dominates.
    dominations = collections.defaultdict(lambda: [])
    for i in items:
        for j in items:
            if all(keys[i][k] < keys[j][k] for k in xrange(dim)):
                dominations[i].append(j)
 
    dominates = lambda i, j: j in dominations[i]
 
    res = set()
    items = set(items)
    for i in items:
        res.add(i)
        for j in list(res):
            if i is j:
                continue
            if dominates(j, i):
                res.remove(i)
                break
            elif dominates(i, j):
                res.remove(j)
    return res
 
    
def non_dominated_sort(iterable, key=lambda x: x):
    """Return a list that is sorted in a non-dominating fashion.
    Keys have to be n-tuple."""
    items = set(iterable)
    fronts = []
    while items:
        front = non_dominated_front(items, key)
        items -= front
        fronts.append(front)
    return fronts

