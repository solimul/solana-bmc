import json
import sys
from sympy import symbols
from sympy.logic.boolalg import to_cnf, Or, And, Not, Implies, Equivalent
from sympy.parsing.sympy_parser import parse_expr
import re




   

class FileHandler:
    def __init__(self, input_file, output_file):
        self.__input_file = input_file
        self.__output_file = output_file
        self.data = []

    def read_file (self):
        data = []
        with open(self.__input_file, 'r') as f:
            data = json.load(f)
            
            states = data.get('states', {})
            init = data.get('init', {})            
            transitions = data.get('transitions', {})
            safety = data.get('safety', [])
    
        self.data = [states, init, transitions, safety]

    def save_to_file(self, header, clauses):
        with open(self.__output_file, 'w') as f:
            f.write(header + '\n')
            for clause in clauses:
                clause = ' '.join(map(str, clause))
                f.write(clause + ' 0\n') 

class Atom ():
    def __init__ (self,symbol, type, domain):
        self.symbol = symbol
        self.type = type
        self.domain = self.parse_domain (type, domain) 
    
    def parse_domain (self, type, domain):
        if type == 'boolean':
            return [0, 1]
        else:
            return domain

class Specification:
    def __init__ (self, steps, data):
        self.state_variables = data [0]
        self.initial_state = data [1]
        self.initial_state = self.initial_state.split (',')
        self.transition_relations = data [2]
        self.safety_property = data [3]
        self.steps = steps
        self.state_atoms = []
        self.initial_state_constraints = []
        self.transition_constraints = {}
        self.safety_violation_constraints = []
        self.symbol_atom_map = {}
        self.create_state_atoms ()
        self.build_initial_state_constraints ()
        self.build_transition_constraints ()
        self.build_safety_constraints ()

    def create_state_atoms (self):
        for type, states in self.state_variables.items():
            for symbol, val in states.items():
                atom = Atom (symbol, type, val)
                self.state_atoms.append (atom)
                self.symbol_atom_map [symbol] = atom 

    def get_var (self, s):
        return re.findall(r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*)\b', s)[0]
    
    def get_val (self, var):
        var = var.rsplit('_', 1)[-1]
        val = var [len (var)-1]
        if val.isdigit() == False:
            return None
        else:
            return int (val)

    def normalize_formula (self, formula):
        state_names = re.findall(r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*)\b', formula)
        state_names = list(set(state_names)) 
        symbols(state_names)
        formula = parse_expr(formula)
        formula = to_cnf(formula)
        formula = str(formula).replace(" ","")
        return formula

    def build_initial_state_constraints (self):
        for formula in self.initial_state:
            formula = self.normalize_formula (formula)
            self.initial_state_constraints.append (formula)

    def build_transition_constraints (self):
        for rule_name, rule in self.transition_relations.items():
            p =  " & ".join(rule ["preconditions"])
            q =  " & ".join(rule ["effects"])
            self.transition_constraints [rule_name] = self.normalize_formula ("Implies ("+p+", "+q+")")
    
    def build_safety_constraints (self):
        for formula in self.safety_property:
            formula = self.normalize_formula ("~("+formula+")")
            self.safety_violation_constraints.append (formula)


class CNFConverter (Specification):
    def __init__ (self, steps, data):
        super ().__init__ (steps, data)
        self.nvars = 0
        self.nclauses = 0
        self.vars = []
        self.state_to_cnf_vars = {}
        self.initial_state_clauses = []
        self.transition_clauses = []
        self.safety_violation_clauses = []
        self.cnf_clauses = []
        self.build_state_to_cnf_vars ()
        self.build_initial_state_cnf ()
        self.build_transition_cnf ()
        self.build_safety_violation_cnf ()
        self.merge_all_cnf_clauses ()
        
             
    def build_state_to_cnf_vars(self):
        idx = 0
        for t in range(0, self.steps + 1):  
            self.state_to_cnf_vars[t] = {}  
            for atom in self.state_atoms:
                self.state_to_cnf_vars[t] [atom.symbol] = []
                if atom.type == 'boolean':
                    idx = idx + 1  
                    self.state_to_cnf_vars[t] [(atom.symbol, None)] = idx
                else:
                    for val in atom.domain:
                        idx = idx + 1
                        self.state_to_cnf_vars[t] [(atom.symbol, val)] = idx
        self.nvars = idx
        self.vars = list (range (1, self.nvars+1))

    def removeval (self, symbol):
        part2 = symbol.rsplit('_', 1)[1]  #indicating a atom, which has int domain
        if part2.isdigit():
            return symbol.rsplit('_', 1)[0]
        else:
            return symbol

    def get_atom_val_type (self, lit):
        atomsymbol = self.get_var (lit)
        atomsymbol0 = self.removeval (atomsymbol)
        val = 1
        type = self.symbol_atom_map [atomsymbol0].type
        if type == 'boolean':
            if '~' in lit:
                val = 0
        else:
            val = self.get_val (atomsymbol)  
        return [atomsymbol0, val, type]
    
    def get_cnf_clause (self, formula, map, normalize):
        if normalize:
            formula = self.normalize_formula (formula)
        clauses = formula.split ("&")
        formula_clauses = []
        for clause in clauses:
            formula_clause = []
            lits = clause.split ("|")
            for lit in lits:
                [atomsymbol, val, type] = self.get_atom_val_type (lit)
                bool_var = 0 
                bool_val = 1
                if type == 'boolean':
                    bool_var = map [(atomsymbol, None)]  
                else:
                    bool_var = map [(self.removeval (atomsymbol), str(val))]   
                if '~' in lit:
                    bool_val = -1  
                formula_clause.append (bool_var*bool_val)
            formula_clauses.append (formula_clause)
        
        return formula_clauses

    def build_initial_state_cnf (self):
        init_state_bool_vars = self.state_to_cnf_vars[0]
        for formula in self.initial_state_constraints:
            clauses = self.get_cnf_clause (formula, init_state_bool_vars, True)
            for clause in clauses:
                self.initial_state_clauses.append (clause)
                self.nclauses += 1

    def build_transition_cnf (self):
        for t in range (0, self.steps+1):
            bool_vars_t = self.state_to_cnf_vars[t]
            for rule_name, formula in self.transition_constraints.items():
                clauses = self.get_cnf_clause (formula, bool_vars_t, False)
                for clause in clauses:
                    self.transition_clauses.append (clause)
                    self.nclauses += 1
    
    def build_safety_violation_cnf (self):
        for t in range (0, self.steps+1):
            bool_vars_t = self.state_to_cnf_vars[t]
            for formula in self.safety_violation_constraints:
                clauses = self.get_cnf_clause (formula, bool_vars_t, False)
                for clause in clauses:
                    self.safety_violation_clauses.append (clause)
                    self.nclauses += 1

    def merge_all_cnf_clauses (self):
        self.cnf_clauses = self.initial_state_clauses.copy()
        self.cnf_clauses.extend (self.transition_clauses)
        self.cnf_clauses.extend (self.safety_violation_clauses)
 


file = FileHandler (sys.argv [1], sys.argv [1].strip('.JSON')+"_k"+str(sys.argv [2])+".cnf")
file.read_file ()
cnfConverter = CNFConverter (int (sys.argv [2]), file.data)
file.save_to_file ("p cnf "+str(cnfConverter.nvars)+" "+str(cnfConverter.nclauses), 
                    cnfConverter.cnf_clauses)

