import ctypes
from ctypes import c_int, c_char_p, POINTER

cadical = ctypes.CDLL("./cadical-lib/libcadical.so")

cadical.ipasir_signature.restype = c_char_p
cadical.ipasir_init.restype = ctypes.c_void_p
cadical.ipasir_add.argtypes = [ctypes.c_void_p, c_int]
cadical.ipasir_assume.argtypes = [ctypes.c_void_p, c_int]
cadical.ipasir_solve.argtypes = [ctypes.c_void_p]
cadical.ipasir_solve.restype = c_int
cadical.ipasir_val.argtypes = [ctypes.c_void_p, c_int]
cadical.ipasir_val.restype = c_int
cadical.ipasir_failed.argtypes = [ctypes.c_void_p, c_int]
cadical.ipasir_failed.restype = c_int
cadical.ipasir_release.argtypes = [ctypes.c_void_p]

solver = cadical.ipasir_init()


clauses = []
assumptions = []
numvars = 0

def add_clauses(clauses):
    for clause in clauses:
        add_clause(clause)

def add_clause(clause):
    for literal in clause:
        cadical.ipasir_add(solver, literal)
    cadical.ipasir_add(solver, 0)

def add_assmuptions (current_assumptions):
    for assumption in current_assumptions:
        cadical.ipasir_assume(solver, assumption)

def get_formula(formulapath):
    with open(formulapath, 'r') as file:
        clauses = []
        nvars = nclauses = 0

        for line in file:
            if line.startswith('c') or line.strip() == '':
                continue
            if line.startswith('p'):
                parts = line.split()
                nvars = int(parts[2])
                nclauses = int(parts[3])
            else:
                clause = list(map(int, line.strip().split()[:-1]))
                clauses.append(clause)
    
    return [nvars, nclauses, clauses]

def get_assumptions(assumptionspath):
    with open(assumptionspath, 'r') as file:
        line = file.readline().strip()
        a = list(map(int, line.split(',')))
    return a

    
def print_result (result, i):
    if result == 10:
        print(f"")
        print ("Assignments")
        print ("-----")
        for var in range(1, numvars+1):
            value = cadical.ipasir_val(solver, var)
            print(f"x{var} = {'True' if value > 0 else 'False'}", end=', ')
        print("-----")
        print ("-----")
        print (f"SATISFIABLE. The property does not hold at step {i+1}")
        return 10
    elif result == 20:
        print(f"UNSATISFIABLE up to step {i + 1}. The property holds!")
        return 20
    else:
        print(f"UNKNOWN or UNSOLVED up to step {i + 1}")
        return 0

def release ():
    cadical.ipasir_release(solver)


def solve (formulapath, assumptionspath):
    [nv, nc, clauses] = get_formula (formulapath)
    numvars = nv
    assumptions = get_assumptions (assumptionspath)
    #print (clauses)
    #print (assumptions)
    add_clauses(clauses)
    current_assumtions = []
    for i, assumption in enumerate(assumptions):
        current_assumtions.append (assumption)
        add_assmuptions (current_assumtions)
        result = cadical.ipasir_solve(solver)
        print_result (result, i)
        if result != 20:
            return 
