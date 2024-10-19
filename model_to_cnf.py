import json
import sys
from sympy import symbols
from sympy.logic.boolalg import to_cnf
from sympy.parsing.sympy_parser import parse_expr
import re

class Helper:
    def __init__ (self):
        self.i = 0
    
    '''
        constraint template ['atom_1,type (atom_1),value_1', ....., 'atom_n,type(atom_n),value_n']
    '''
    def to_clause_template (self, constraints_template):
        clause_templates = []
        constraints_template = constraints_template.replace(' ', '')
        constraints_template = constraints_template.split ('&')
        for cls in constraints_template:
            temp = ''
            cls = cls.replace (' ','')
            cls = cls.split ('|')
            for lit in cls:
                temp+=str (lit)+" "
            clause_templates.append (temp.rstrip())
        return clause_templates

    def get_val (self, type, val):
        if type == 'boolean':
            return None 
        else:
            return val

    def to_constraint_template (self, constraints):
        constraints_template = []
        for _c,_val in constraints.items():
            constraints_template.append (_c+','+self.state_type_map [_c]+','+_val)
        return ' & '.join(constraints_template)
 

class FileHandler ():
    def __init__(self, input_file, output_file):
        self.__input_file = input_file
        self.__output_file = output_file
        self.data = []

    def read_file (self):
        data = []
        with open(self.__input_file, 'r') as f:
            data = json.load(f)
            
            states = data.get('states', {})
            transitions = data.get('transitions', {})
            init = data.get('init', {})            
            safety = data.get('safety', [])
    
        self.data = [states, transitions, init, safety]

class Specification (Helper):
    def __init__ (self, data):
        self.states = data [0]
        self.transitions = data [1]
        self.initial_state = data [2]
        self.safety_constraints = data [3]   
        self.state_type_map = {}

    
    
        

class Unroller (Specification, Helper):
        def __init__ (self, steps, data):
            super().__init__ (data)
            Helper.__init__(self)
            self.nvars = 0
            self.nclauses = 0
            self.steps = steps
            self.vars = []
            self.state_bool_vars_map = {}
            self.vars_for_cnf ()
            self.map_bool_vars ()

        def vars_for_cnf(self):
            for state_type, state_data in self.states.items():
                for state, values in state_data.items():
                    if state_type == 'boolean':
                        self.nvars += 1 * (self.steps + 1)
                    else:
                        self.nvars += len(values) * (self.steps + 1)           
            self.vars = list(range(1, self.nvars + 1))

        def map_bool_vars(self):
            idx = 0
            for t in range(self.steps + 1):  
                self.state_bool_vars_map[t] = {}  
                for state_type, state_data in self.states.items():
                    for state, values in state_data.items():
                        if state_type == 'boolean':
                            self.state_bool_vars_map[t][state+',boolean,'+'None'] = self.vars[idx]
                            idx += 1
                            if state not in self.state_type_map:
                                self.state_type_map [state] = 'boolean'
                        else:
                            for val in values:
                                self.state_bool_vars_map[t][state+',int,'+str(val)] = self.vars[idx]
                                idx += 1
                            if state not in self.state_type_map:
                                self.state_type_map [state] = 'int' 

        def to_clause_template (self, constraints):
            ct = Helper.to_constraint_template (self, constraints)
            return Helper.to_clause_template (self, ct)

        def get_constraints (self, ctype):
            if ctype == 'initial_state':
                return self.initial_state

class Converter (Unroller):
    def __init__(self, steps, data):
        super().__init__ (steps, data)
        self.init_clauses = []
        self.transition_clauses = []
        self.safety_clauses = []

    def to_bool_var (self, t, atom):
        atom = atom.replace(' ','')
        return self.state_bool_vars_map [t] [atom]

    def handle_bool_case (self, atom):
        atom = atom.split (',')
        if atom [1] == 'boolean':
            atom [2] = 'None'
        return ','.join(atom)
    
    def atom_to_lit (self, t, atom):
        var = self.to_bool_var (t, self.handle_bool_case (atom))
        atoml = atom.split (',')
        val = atoml[2]
        if val == 'false':
            var = -var
        return var 

    def ct_to_clause (self, t, ct):
        clause = ''
        ct = ct.split ("|")
        for atom in ct:
            lit = self.atom_to_lit (t, atom)
            clause += str(lit)+" "
        return clause+"0"
           
    def to_clauses (self, t, constraints_template):
        clauses = []
        for ct in constraints_template:
            clauses.append (self.ct_to_clause (t, ct))
        return clauses
        
    def create_init_clauses (self):
        isct = self.to_clause_template (super().get_constraints ('initial_state'))
        self.init_clauses = self.to_clauses (0, isct)
        print (self.init_clauses)        
        
                




file_handler = FileHandler  (sys.argv[1], '')
file_handler.read_file ()

converter = Converter (int(sys.argv [2]), file_handler.data)
converter.create_init_clauses ()





# state_to_type={}

# def parse_json_file(file_path):
#     """
#     Parse the JSON file and extract the system attributes: states, transitions, init, safety.
#     :param file_path: Path to the JSON file.
#     :return: Parsed states, transitions, init, and safety as dictionaries.
#     """
#     try:
#         with open(file_path, 'r') as f:
#             data = json.load(f)
        
#         # Parse states
#         states = data.get('states', {})
        
#         # Parse transitions
#         transitions = data.get('transitions', {})
        
#         # Parse initial conditions
#         init = data.get('init', {})
        
#         # Parse safety properties
#         safety = data.get('safety', [])
        
#         return states, transitions, init, safety
    
#     except FileNotFoundError:
#         print(f"File {file_path} not found.")
#         sys.exit(1)
#     except json.JSONDecodeError:
#         print(f"Error parsing JSON in file {file_path}. Ensure the file is a valid JSON format.")
#         sys.exit(1)



# def create_state_to_cnf_vars(steps, states, vars):
#     state_to_cnf_vars = {}
#     idx = 0
#     for t in range(steps + 1):  
#         state_to_cnf_vars[t] = {}  
#         for data_type, data in states.items():
#             for state, values in data.items():
#                 if data_type == 'boolean':
#                     state_to_cnf_vars[t][(state, 'boolean', None)] = vars[idx]
#                     idx += 1
#                     if state not in state_to_type:
#                         state_to_type [state] = 'boolean'
#                 else:
#                     for val in values:
#                         state_to_cnf_vars[t][(state, 'int', val)] = vars[idx]
#                         idx += 1
#                     if state not in state_to_type:
#                         state_to_type [state] = 'int' 
#     return state_to_cnf_vars






# def init_cond_to_cnf(clauses, state_vars, init):
#     time_step_0_vars = state_vars[0]  
#     for init_state, val in init.items():
#         for (state, data_type, data_value), cnf_var in time_step_0_vars.items():
#             if state == init_state:
#                 if data_type == 'boolean' and data_value is None:
#                     if val == 'true':
#                         clauses.append(str(cnf_var) + " 0")  
#                     elif val == 'false':
#                         clauses.append(str(-cnf_var) + " 0")  
#                 elif data_type == 'int' and data_value == val:
#                     clauses.append(str(cnf_var) + " 0")
        

# def vars_for_cnf(states, steps):
#     nvars = 0
#     for data_type, data in states.items():
#         for state, values in data.items():
#             if data_type == 'boolean':
#                 nvars += 1 * (steps + 1)
#             else:
#                 nvars += len(values) * (steps + 1)
    
#     vars = list(range(1, nvars + 1))

#     return vars

# def get_bool_val (pval):

#     if flag == 'true':
#         return 'false'
#     else:
#         return 'true'


    

        
# def transitions_to_implications (transitions):
#     implications = []
#     for transition_rule, transition_body in transitions.items ():
#         preconditions = transition_body ['preconditions']
#         effects = transition_body ['effects']
#         premise = [(p, v) for p, v in preconditions.items ()]
#         conclusion = [(e, v) for e, v in effects.items()]
#         implications.append ([premise, conclusion])
#     return implications

# def to_sat_lits (sentence, state_vars, t):
#     vars = []
#     for s in sentence:
#         typ = state_to_type [s[0]]
#         key1 = t
#         key2 = []
#         if typ == 'boolean':
#             key2 = (s[0], 'boolean', None)
#         else:
#             key2 = (s[0], 'int', s[1])
       
#         var = state_vars [key1] [key2]
#         if typ == 'boolean' and s [1] == 'false':
#             var = -var
#         vars.append (var)
#     return vars 

# def negate_vars (vars):
#     return [-v for v in vars]

# def normalize_formula (formula):
#     nf = []
#     for f in formula: 
#         state_names = re.findall(r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*)\b', f)
#         state_names = list(set(state_names))
#         symbols(state_names)
#         f = parse_expr("~("+f+")")
#         f = to_cnf(f)
#         nf.append (f)
#     return nf 

# def normalize_implications (pr, cn):
#     clauses = []
#     for c in cn:
#         cl=""
#         for p in pr:
#             cl += str(p)+" " 
#         cl += str(c)+" 0"
#         clauses.append (cl)
#     return clauses

# def transitions_to_clauses (clauses, state_vars, implications, steps):
#     for imp in implications:
#         premise = imp [0]
#         conclusion = imp [1]
#         for t in range (0, steps):
#             premise_sat_vars = to_sat_lits (premise, state_vars, t) 
#             conclusion_sat_vars = to_sat_lits (conclusion, state_vars, t+1)
#             premise_sat_vars = negate_vars (premise_sat_vars)
#             cls_set = normalize_implications (premise_sat_vars, conclusion_sat_vars)            
#             clauses.extend (cls_set)

# # def safety_to_clauses (clauses, state_vars, init, safety):
# #     for s in safety:
# #         s = normalize_formula (s)
# #         for t in range (0, steps+1):

# def lit2val (lit):
#     return re.findall(r'\((.*?)\)', lit)

# def safety_to_clauses (clauses, nf, state_vars, steps):
#     for t in range (0, steps+1):
#         key1 = t
#         key2 = []
#         for f in nf:
#             f = str (f)
#             f = f.split ('&')
#             for cls in f:
#                 cls = cls.split ('|')
#                 temp = ''
#                 for lit in cls:
#                     state = lit.lstrip ('-').strip(' ')
#                     if state_to_type [state] == 'boolean':
#                         key2 = (state, 'boolean', None)
#                     else:
#                         key2 = (state,'int', lit2val(lit))
#                     var = state_vars [key1] [key2]
#                     if '-' in lit:
#                         var = -var
#                     temp+=str (var)+" "
#                 temp+="0"
#                 clauses.append (temp)

# def to_cnf_ (states, transitions, init, safety, steps):
#     vars = vars_for_cnf (states, steps)
#     state_vars = create_state_to_cnf_vars (steps, states, vars)
#     clauses = []
#     init_cond_to_cnf (clauses, state_vars, init)
#     transition_implications = transitions_to_implications (transitions)
#     transitions_to_clauses (clauses, state_vars, transition_implications, steps)
#     #safety_to_clauses (clauses, state_vars, safety, steps)
#     nf = normalize_formula (safety)
#     safety_to_clauses (clauses, nf, state_vars, steps)
#     return [len(vars), clauses]

# def save_to_file(header, clauses, file_name):
#     with open(file_name, 'w') as f:
#         f.write(header + '\n')
#         for clause in clauses:
#             f.write(clause + ' \n')

# file_path = sys.argv[1]
# steps = int (sys.argv [2])

# # Parse the JSON file and extract the attributes
# states, transitions, init, safety = parse_json_file(file_path)
# [nvars, clauses] = to_cnf_ (states, transitions, init, safety, steps)
# save_to_file ("p cnf "+str (nvars)+" "+str(len(clauses)), clauses, file_path.strip('.JSON')+"_k"+str(steps)+".cnf")


