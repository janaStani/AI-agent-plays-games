#!/usr/bin/env python3
from csp_templates import Constraint, BooleanCSP
from typing import List, Optional


class Solver:
    """
    Class for solving BooleanCSP.

    Main methods:
    - forward_check
    - solve
    - infer_var
    """

    def __init__(self):
        pass

    
    def forward_check(self, csp: BooleanCSP) -> Optional[List[int]]:
        inferred = []
        assigned_here = set()

        while csp.unchecked:       # go until no more constraints to check
            constraint = csp.unchecked.pop()
            vars_ = constraint.vars          # variables involved
            k = constraint.count             # num of var that must be true in constraint

            true_count = 0         # count true vars
            unknown = []           # collect unknowns

            for v in vars_:                   
                if csp.value[v] is True:        
                    true_count += 1
                elif csp.value[v] is None:
                    unknown.append(v)
 
            if true_count > k or true_count + len(unknown) < k:  # contradiction check
                for v in assigned_here:                     # too many trues, cannot satisfy constraint
                    csp.value[v] = None
                return None

            if true_count == k:             # all others must be false
                for v in unknown:           
                    csp.set(v, False)
                    inferred.append(v)
                    assigned_here.add(v)

            elif true_count + len(unknown) == k:  # of sum of unknwn and true is k
                for v in unknown:                  # all unknowns must be true
                    csp.set(v, True)
                    inferred.append(v)
                    assigned_here.add(v)

        return inferred

    
    def solve(self, csp: BooleanCSP) -> Optional[List[int]]:
        """
        Backtracking search with forward checking.
        Returns list of variables assigned in this call, or None if unsolvable.
        """
        # create a copy, avoid changing original
        csp_copy = BooleanCSP(csp.num_vars)
        csp_copy.value = csp.value[:]
        csp_copy.constraints = list(csp.constraints)
        
        # var_constraints might be a list, not a dict
        if hasattr(csp, 'var_constraints'):
            if isinstance(csp.var_constraints, dict):
                csp_copy.var_constraints = {k: set(v) for k, v in csp.var_constraints.items()}
            else:
                csp_copy.var_constraints = list(csp.var_constraints)
        else:
            csp_copy.var_constraints = []
            
        csp_copy.unchecked = list(csp.unchecked)   # copy unchecked constraints
        
        # call recursive solver, to search for solution
        result = self._solve_recursive(csp_copy)
        if result is not None:
            # if solution found, copy back to original csp
            for i in range(csp.num_vars):
                csp.value[i] = csp_copy.value[i]
        return result
    
    # recursive helper for solve
    def _solve_recursive(self, csp: BooleanCSP) -> Optional[List[int]]:
        
        # first do forward checking
        inferred = self.forward_check(csp)
        if inferred is None:
            return None

        # check if all constrained variables are assigned
        unassigned = []
        for v in range(csp.num_vars):
            if csp.value[v] is None:     
                has_constraints = False   
                for constraint in csp.constraints:   # check if variable has any constraints
                    if v in constraint.vars:         
                        has_constraints = True
                        break
                if has_constraints:
                    unassigned.append(v)
                    
        if not unassigned:
            # if all var are assigned, check if all constraints are satisfied
            for constraint in csp.constraints:
                true_count = 0
                for v in constraint.vars:    #
                    if csp.value[v] is True:
                        true_count += 1
                if true_count != constraint.count:
                    return None
            # return all assigned variables
            return [v for v in range(csp.num_vars) if csp.value[v] is not None]

        # pick unassigned variable that appears in the most constraints
        var_degrees = {}
        for v in unassigned:
            degree = 0
            for constraint in csp.constraints:
                if v in constraint.vars:
                    degree += 1
            var_degrees[v] = degree
        
        var = max(var_degrees.keys(), key=lambda v: var_degrees[v])

        for value in (True, False):
            
            old_values = csp.value[:]           # save state, before trying each value
            old_unchecked = list(csp.unchecked)

            csp.set(var, value)      

            result = self._solve_recursive(csp)    # if recursive call succeeds, return solution
            if result is not None:
                return result

            # otherwise, restoore state
            csp.value = old_values
            csp.unchecked = old_unchecked

        return None


    def infer_var(self, csp: BooleanCSP) -> int:
        """
        Infer the value of a single variable using proof by contradiction.
        Returns the variable index if inferred, else -1.
        """
        # save original state
        original_values = csp.value[:]
        original_unchecked = list(csp.unchecked)
        
        # get variables with constraints, sorted by descending degree
        vars_with_constraints = []
        for v in range(csp.num_vars):
            if csp.value[v] is None:
                # check if variable has any constraints
                has_constraints = False
                for constraint in csp.constraints:
                    if v in constraint.vars:
                        has_constraints = True
                        break
                if has_constraints:
                    vars_with_constraints.append(v)
        
        # sort by degree, count constraints for each var
        var_degrees = {}
        for v in vars_with_constraints:
            degree = 0
            for constraint in csp.constraints:
                if v in constraint.vars:
                    degree += 1
            var_degrees[v] = degree
        
        vars_by_degree = sorted(vars_with_constraints, key=lambda v: var_degrees[v], reverse=True)

        for var in vars_by_degree:
            for trial_value in (True, False):
                # restore original state for each trial
                csp.value = original_values[:]
                csp.unchecked = list(original_unchecked)
                
                csp.set(var, trial_value)
                
                # try to solve with assignment
                if self.solve(csp) is None:
                    # contradiction, opposite value must be true
                    csp.value = original_values[:]
                    csp.unchecked = list(original_unchecked)
                    
                    # set opposite value
                    csp.set(var, not trial_value)
                    return var

        # restore original state
        csp.value = original_values[:]
        csp.unchecked = list(original_unchecked)
        return -1