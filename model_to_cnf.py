import json
import sys
from sympy import symbols
from sympy.logic.boolalg import to_cnf
from sympy.parsing.sympy_parser import parse_expr
import re

state_to_type={}

def parse_json_file(file_path):
    """
    Parse the JSON file and extract the system attributes: states, transitions, init, safety.
    :param file_path: Path to the JSON file.
    :return: Parsed states, transitions, init, and safety as dictionaries.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Parse states
        states = data.get('states', {})
        
        # Parse transitions
        transitions = data.get('transitions', {})
        
        # Parse initial conditions
        init = data.get('init', {})
        
        # Parse safety properties
        safety = data.get('safety', [])
        
        return states, transitions, init, safety
    
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error parsing JSON in file {file_path}. Ensure the file is a valid JSON format.")
        sys.exit(1)



def create_state_to_cnf_vars(steps, states, vars):
    state_to_cnf_vars = {}
    idx = 0
    for t in range(steps + 1):  
        state_to_cnf_vars[t] = {}  
        for data_type, data in states.items():
            for state, values in data.items():
                if data_type == 'boolean':
                    state_to_cnf_vars[t][(state, 'boolean', None)] = vars[idx]
                    idx += 1
                    if state not in state_to_type:
                        state_to_type [state] = 'boolean'
                else:
                    for val in values:
                        state_to_cnf_vars[t][(state, 'int', val)] = vars[idx]
                        idx += 1
                    if state not in state_to_type:
                        state_to_type [state] = 'int' 
    return state_to_cnf_vars






def init_cond_to_cnf(clauses, state_vars, init):
    time_step_0_vars = state_vars[0]  
    for init_state, val in init.items():
        for (state, data_type, data_value), cnf_var in time_step_0_vars.items():
            if state == init_state:
                if data_type == 'boolean' and data_value is None:
                    if val == 'true':
                        clauses.append(str(cnf_var) + " 0")  
                    elif val == 'false':
                        clauses.append(str(-cnf_var) + " 0")  
                elif data_type == 'int' and data_value == val:
                    clauses.append(str(cnf_var) + " 0")
        

def vars_for_cnf(states, steps):
    nvars = 0
    for data_type, data in states.items():
        for state, values in data.items():
            if data_type == 'boolean':
                nvars += 1 * (steps + 1)
            else:
                nvars += len(values) * (steps + 1)
    
    vars = list(range(1, nvars + 1))

    return vars

def get_bool_val (pval):

    if flag == 'true':
        return 'false'
    else:
        return 'true'


    

        
def transitions_to_implications (transitions):
    implications = []
    for transition_rule, transition_body in transitions.items ():
        preconditions = transition_body ['preconditions']
        effects = transition_body ['effects']
        premise = [(p, v) for p, v in preconditions.items ()]
        conclusion = [(e, v) for e, v in effects.items()]
        implications.append ([premise, conclusion])
    return implications

def to_sat_lits (sentence, state_vars, t):
    vars = []
    for s in sentence:
        typ = state_to_type [s[0]]
        key1 = t
        key2 = []
        if typ == 'boolean':
            key2 = (s[0], 'boolean', None)
        else:
            key2 = (s[0], 'int', s[1])
       
        var = state_vars [key1] [key2]
        if typ == 'boolean' and s [1] == 'false':
            var = -var
        vars.append (var)
    return vars 

def negate_vars (vars):
    return [-v for v in vars]

def normalize_formula (formula):
    nf = []
    for f in formula: 
        state_names = re.findall(r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*)\b', f)
        state_names = list(set(state_names))
        symbols(state_names)
        f = parse_expr("~("+f+")")
        f = to_cnf(f)
        nf.append (f)
    return nf 

def normalize_implications (pr, cn):
    clauses = []
    for c in cn:
        cl=""
        for p in pr:
            cl += str(p)+" " 
        cl += str(c)+" 0"
        clauses.append (cl)
    return clauses

def transitions_to_clauses (clauses, state_vars, implications, steps):
    for imp in implications:
        premise = imp [0]
        conclusion = imp [1]
        for t in range (0, steps):
            premise_sat_vars = to_sat_lits (premise, state_vars, t) 
            conclusion_sat_vars = to_sat_lits (conclusion, state_vars, t+1)
            premise_sat_vars = negate_vars (premise_sat_vars)
            cls_set = normalize_implications (premise_sat_vars, conclusion_sat_vars)            
            clauses.extend (cls_set)

# def safety_to_clauses (clauses, state_vars, init, safety):
#     for s in safety:
#         s = normalize_formula (s)
#         for t in range (0, steps+1):

def lit2val (lit):
    return re.findall(r'\((.*?)\)', lit)

def safety_to_clauses (clauses, nf, state_vars, steps):
    for t in range (0, steps+1):
        key1 = t
        key2 = []
        for f in nf:
            f = str (f)
            f = f.split ('&')
            for cls in f:
                cls = cls.split ('|')
                temp = ''
                for lit in cls:
                    state = lit.lstrip ('-').strip(' ')
                    if state_to_type [state] == 'boolean':
                        key2 = (state, 'boolean', None)
                    else:
                        key2 = (state,'int', lit2val(lit))
                    var = state_vars [key1] [key2]
                    if '-' in lit:
                        var = -var
                    temp+=str (var)+" "
                temp+="0"
                clauses.append (temp)

def to_cnf_ (states, transitions, init, safety, steps):
    vars = vars_for_cnf (states, steps)
    state_vars = create_state_to_cnf_vars (steps, states, vars)
    clauses = []
    init_cond_to_cnf (clauses, state_vars, init)
    transition_implications = transitions_to_implications (transitions)
    transitions_to_clauses (clauses, state_vars, transition_implications, steps)
    #safety_to_clauses (clauses, state_vars, safety, steps)
    nf = normalize_formula (safety)
    safety_to_clauses (clauses, nf, state_vars, steps)
    return [len(vars), clauses]

def save_to_file(header, clauses, file_name):
    with open(file_name, 'w') as f:
        f.write(header + '\n')
        for clause in clauses:
            f.write(clause + ' \n')

file_path = sys.argv[1]
steps = int (sys.argv [2])

# Parse the JSON file and extract the attributes
states, transitions, init, safety = parse_json_file(file_path)
[nvars, clauses] = to_cnf_ (states, transitions, init, safety, steps)
save_to_file ("p cnf "+str (nvars)+" "+str(len(clauses)), clauses, file_path.strip('.JSON')+"_k"+str(steps)+".cnf")


#print_parsed_data(states, transitions, init, safety)
