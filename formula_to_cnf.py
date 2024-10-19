from sympy import symbols
from sympy.logic.boolalg import to_cnf
from sympy.parsing.sympy_parser import parse_expr

# Define your Boolean variables
door_open, elevator_moving = symbols('door_open elevator_moving')

# Define a Boolean formula as a string
# This example includes both variables in a more complex formula
formula_str = "Equivalent (door_open, elevator_moving)"

# Parse the string into a SymPy expression
parsed_formula = parse_expr(formula_str)

# Convert to CNF
cnf_formula = to_cnf(parsed_formula)

# Print the CNF
print(cnf_formula)

