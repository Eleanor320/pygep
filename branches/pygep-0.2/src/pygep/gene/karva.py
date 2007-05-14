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
from copy import copy
from pygep.util import memoize


class KarvaGene(object):
    '''
    Represents a single gene that is evaluated as Karva language.  These are
    intended only for internal use by the Chromosome class, which will
    generate the gene contents and link together one or more genes.  Genes,
    in turn, are responsible for generating and caching evaluation results.
    '''
    def __init__(self, alleles, head):
        '''
        
        @param alleles: individual loci for a given chromosome
        @param head:    head length
        '''
        self.alleles = alleles
        self.head    = head
        
        self._find_coding()

    
    @memoize
    def __call__(self, obj):
        '''
        Evaluates a Karva gene against some instance.  The string terminals in 
        the gene are assumed to be attributes on the object instance.  Numeric
        constants are left as is, and functions are evaluated.

        @param obj: some object instance
        @return:    result of evaluating the gene
        '''
        # TODO: currently we cache by object identities.  Perhaps we should
        #       memoize on the relevant object attributes instead?
        
        # Prepare our evaluation list -> results of expression evaluation
        def _value(allele):
            if callable(allele):
                return None
            elif not isinstance(allele, str):
                # could be a number
                return allele
            else:
                return getattr(obj, allele)
        
        evaluation = [_value(a) for a in self.alleles]

        # Evaluate the gene against obj in reverse
        index = self.coding + 1
        for i in reversed(xrange(index)):
            allele = self.alleles[i]

            if callable(allele):
                num  = allele.func_code.co_argcount
                args = evaluation[index-num:index]

                # Replace the operation in eval with its return val
                evaluation[i] = allele(*args)
                index -= num

        # Expression results will always be stored in the first index
        return evaluation[0]


    def __repr__(self):
        s = ''
        for allele in self.alleles:
            # Differentiate between functions and terminals
            try:
                name = allele.symbol
            except AttributeError:
                try:
                    name = allele.__name__
                except AttributeError:
                    name = str(allele)

            # If the name is not one char, surround it with { }
            s += name if len(name) == 1 else '{%s}' % name

        return s

    
    def __len__(self):
        return len(self.alleles)
    
    
    def __iter__(self):
        return iter(self.alleles)
    
    
    def __getitem__(self, i):
        return self.alleles[i]
    
    def __getslice__(self, i, j):
        return self.alleles[i:j]
    
    
    def _find_coding(self):
        '''Assigns the last coding index to self.coding'''
        # How to find the length of a single coding region:
        #
        # Start at the first gene and determine how many args it
        # requires. Then move forward that many args and sum their
        # required args. Continue this until there are no more
        # required args. The resulting index will be one gene past
        # the coding region for the current gene
        index, args = 0, 1
        while args:
            next_args = 0
            for _ in xrange(args):
                if callable(self.alleles[index]):
                    next_args += self.alleles[index].func_code.co_argcount
                index += 1

            args = next_args

        self.coding = index - 1
    
    
    def derive(self, changes):
        '''
        Derives a gene from self.  If the coding region remains unchanged,
        then the new gene keep the memoized evaluations of its parent. For 
        instance, replacing allele 0 with 'x' and allele 3 with a function
        add via point mutation would look like:
                        
            gene.derive([(0, ['x']), (3, [add]))
        
        Whereas replacing a block of alleles in crossover would like like:
        
            gene.derive([(5, [add, 'x', 'y'])])

        @param changes: sequence of (index, alleles) tuples
        @return: new KarvaGene
        '''
        new  = None # new gene
        same = True # whether or not the coding region is the same
        for index, alleles in changes:
            l = len(alleles)
            
            if self[index:index+l] != alleles:
                # Copy the alleles on first change
                if not new:
                    new = self[:index] + alleles + self[index+l:]
                else:
                    new[index:index+l] = alleles
                
                # Does this change the coding region?
                if same and index <= self.coding:
                    same = False
            
        if not new: # Nothing changed!
            return self
        
        # Create the new gene
        gene = copy(self)
        gene.alleles = new
        
        if not same: # Recalculate coding region & kill memoized results
            gene._find_coding()
            try:
                delattr(gene, self.__call__.memo)
            except AttributeError:
                pass
            
        return gene
