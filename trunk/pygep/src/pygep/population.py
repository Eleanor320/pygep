# PyGEP: Gene Expression Programming for Python
# Copyright (C) 2007  Ryan J. O'Neil
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
from itertools import izip
from operator import attrgetter
import random, string


class Population(object):
    def __init__(self, cls, size, head, genes=1, linker=lambda x: x):
        '''
        Generates a population of some chromsome class
        @param cls:    Chromosome type
        @param size:   population size
        @param head:   chromosome head length
        @param genes:  number of genes
        @param linker: multigenic results linker function
        '''
        self.size   = size
        self.head   = head
        self.genes  = genes
        self.linker = linker

        self.__age = 1

        # Start an initial population
        self.population = [i for _, i in izip(xrange(size),
                           cls.generate(head, genes, linker))]
        self._next_pop = [None] * size # placeholder for next generation

        # Header for display purposes
        try:
            l = len(self.population[0])
            self.header = string.digits * (l / len(string.digits)) + \
                          string.digits[:(l % len(string.digits))]
            self.header += '\n' + '-' * len(self.header)
        except IndexError:
            raise ValueError('Empty populations are meaningless!')


    def __repr__(self):
        return '\n'.join([str(i) for i in [self.header] + self.population])


    def __iter__(self):
        return iter(self.population)


    age  = property(lambda self: self.__age, doc='Generation number')
    best = property(
        lambda self: max(self.population, key=attrgetter('fitness')), 
        doc='The best Chromosome of the current generation'
    )


    def solve(self, generations):
        '''Cycles a number of generations. Stops if chrom.solved()'''
        pass


    def cycle(self):
        '''Selects and recombines the next generation'''
        # Copy the best individual via simple elitism
        self._next_pop[0] = self.best

        # Randomly fill in the rest.  TODO: use fitness scaling here
        for i in xrange(1, self.size):
            self._next_pop[i] = random.choice(self.population)

        # Switch to the next generation and increment age
        self._next_pop, self.population = self.population, self._next_pop
        self.__age += 1

