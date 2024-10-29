import json
import sys
from sympy import symbols
from sympy.logic.boolalg import to_cnf, Or, And, Not, Implies, Equivalent
from sympy.parsing.sympy_parser import parse_expr
import re, os

'''
   Hanldles File Operations
'''
class FileHandler:
    def __init__(self, input_file, output_file, additional_file):
        self.__input_file = input_file
        self.output_files = [output_file, additional_file]
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

    def save_to_file(self, file_index, header, data):
        with open(self.output_files[file_index], 'w') as f:                
            if isinstance(data[0], (int, float, str)):
                f.write(','.join(map(str, data)) + '\n')
            else:
                f.write(header + '\n')
                for item in data:
                    item = ' '.join(map(str, item))
                    f.write(item + ' 0\n')

'''
    Helper class containing helper methods
'''
class Helper:
    underscore_str = "_"
    atom_finder_pattern = r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*)\b'
    atom_finder_pattern2 = r'(~)?([a-zA-Z_]+)(_(\d+))?_(\d+)'
    state_finder_pattern = r'(?<![&|^])\b(?:~)?([a-zA-Z_]\w*|\d+)\b'
    logicalANDstr = "&"
    logicalORstr = "|"
    space_str = " "
    opening_square_brace = "("
    closing_square_brace = ")"
    comma_str = ","
    implication_str = "Implies"
    boolean_str = "boolean"
    negation_str = "~"


    '''
        gets a proposition as input, and returns the atom in the proposition
        Exacmple: 
             input: ~x_0: x does not take the value 0
             output: x_0
    '''
    def get_atom (self, s):
        return re.findall(self.atom_finder_pattern, s)[0]
    
    '''
        This function extracts the value of an atom in a proposition. The atom can belong 
        to either a non-boolean or a boolean domain. 

        - For atoms in a non-boolean domain (e.g., integer domain), the atom typically 
          includes a number as part of its name (e.g., "x_5" where "x" is the atom, 
          and "5" represents the value that the atom takes).
          In this case, the function extracts the numeric value after the last underscore.
          
        - For atoms in a boolean domain (e.g., "y", where "y" is either True or False), 
          there is no numeric value attached. In this case, the function will return None.

        The function splits the atom string from the last underscore ('_') to determine 
        if there is a numeric value (indicating a non-boolean domain). If the value is a 
        valid integer, it is returned. If the atom is boolean (no numeric value), the function 
        returns None.

        Example:
             input: "x_5"  (atom 'x' with non-boolean domain where 'x' takes the value 5)
             output: 5  (returns the integer 5)
             
             input: "y"  (atom 'y' in the boolean domain, no attached value)
             output: None  (returns None)
             
        Args:
            atom (str): The atom in string format (e.g., "x_5" or "y").

        Returns:
            int or None: The numeric value if it exists (for non-boolean atoms), 
                         otherwise None (for boolean atoms).
    '''

    def get_domain_val (self, atom):
        val = atom.rsplit('_', 1)[-1]
        if val.isdigit() == False:
            return None
        else:
            return int (val)

        '''
        This function takes a boolean formula as input, normalizes it by converting 
        it into Conjunctive Normal Form (CNF), and ensures that the state variables 
        in the formula are properly identified and parsed as symbols. It returns the 
        formula in CNF form as a string without any spaces.

        Steps involved:
        1. **Extract State Names**: 
            - Uses a regular expression to extract all variable names (state names) from 
              the formula, including negated variables (e.g., "~door_open"). 
            - The regular expression captures valid variable names that start with 
              a letter or underscore and can include alphanumeric characters or underscores.
            - The `set()` ensures that the list of state names is unique.
        
        2. **Convert to Symbols**:
            - The extracted state names are converted into symbolic variables using SymPy's 
              `symbols()` function, which ensures that they are treated as mathematical symbols.

        3. **Parse the Formula**:
            - The formula is passed to `parse_expr()` to convert it from a string into 
              a symbolic expression that SymPy can manipulate.

        4. **Convert to CNF**:
            - The symbolic expression is converted into Conjunctive Normal Form (CNF) 
              using SymPy's `to_cnf()` function, which transforms the logical expression 
              into a conjunction of clauses.

        5. **Format the Formula**:
            - The resulting CNF formula is converted back to a string.
            - All spaces in the string are removed for a more compact representation.

        6. **Return the Formula**:
            - The normalized formula in CNF form, represented as a string without spaces, 
              is returned.

        Example:
            Input: "(door_open & ~elevator_moving) & elevator_floor_0"
            Output: "(~door_open | elevator_moving) & elevator_floor_0"

        Args:
            formula (str): The input boolean formula as a string.

        Returns:
            str: The normalized formula in CNF form, with no spaces.
    '''

    def normalize_formula (self, formula):
        state_names = re.findall(self.state_finder_pattern, formula)
        state_names = list(set(state_names)) 
        symbols(state_names)
        formula = parse_expr(formula)
        formula = to_cnf(formula)
        formula = str(formula).replace(self.space_str,"")
        return formula

        '''
        This function processes a given symbol and removes the numeric value that follows 
        the last underscore (`_`), if it exists. The symbol is assumed to represent an atom 
        in either a boolean or non-boolean (e.g., integer) domain.

        - For symbols that belong to a non-boolean domain (i.e., those that have an integer 
          value appended after an underscore, such as "x_5"), this function removes the 
          numeric value and returns the base atom (e.g., "x").
          
        - For symbols that do not have a numeric value after the last underscore or do not 
          belong to a non-boolean domain, the function returns the symbol unchanged.

        Steps involved:
        1. **Identify the Part After the Last Underscore**:
            - The symbol is split at the last underscore (`_`), and the part after the last 
              underscore is stored as `part2`.
              
        2. **Check if the Part is a Number**:
            - If `part2` is composed of digits (i.e., it represents a numeric value), 
              the function removes the numeric value and returns the part before the last 
              underscore.
              
        3. **Return the Symbol**:
            - If the part after the last underscore is not numeric, or if the symbol 
              doesn't have an underscore, the function returns the symbol unchanged.

        Example:
            Input: "x_5"   (atom 'x' with non-boolean domain and value 5)
            Output: "x"    (returns the atom name without the value)
            
            Input: "y"     (atom 'y' with boolean domain)
            Output: "y"    (returns the symbol unchanged)
            
            Input: "x_var" (symbol without numeric suffix)
            Output: "x_var" (returns the symbol unchanged)

        Args:
            symbol (str): The input symbol representing an atom.

        Returns:
            str: The symbol without the numeric value if it's present, or the original 
                 symbol if no numeric value exists.
    '''

    def remove_domain_val (self, symbol):
        splitted_symbol = symbol.rsplit(self.underscore_str, 1)
        last = ''
        if len(splitted_symbol)>1:
            last = splitted_symbol [1] 
        if last.isdigit(): #indicating a atom, which has int domain
            return splitted_symbol[0]
        else:
            return symbol

        '''
        This function extracts and returns the base atom, its value, and its type 
        for a given literal (lit). The literal can represent either a boolean or 
        non-boolean (e.g., integer) atom. The function determines whether the atom 
        is negated and assigns the appropriate value based on its type.

        Steps involved:
        
        1. **Extract the Atom Symbol**:
            - The atom symbol (possibly with an appended numeric value) is extracted 
              from the literal using the `self.get_atom()` method.

        2. **Remove Numeric Value (if applicable)**:
            - The `self.remove_domain_val()` method removes the numeric value (for atoms in 
              non-boolean domains) from the atom symbol, leaving the base atom name.
              If the atom is in the boolean domain, no numeric value is removed.

        3. **Determine the Atom's Type**:
            - The type of the atom is retrieved from `self.symbol_atom_map` using the 
              base atom symbol (`atomsymbol0`). The type can be either 'boolean' or a 
              non-boolean type (e.g., integer).

        4. **Determine the Atom's Value**:
            - If the atom is of type 'boolean', the function checks whether the 
              literal contains a negation symbol (`~`). If negated, the value is set to 0, 
              otherwise it remains 1.
            - If the atom is non-boolean (e.g., an integer domain atom), the numeric 
              value is extracted using `self.get_val()`.

        5. **Return the Atom Symbol, Value, and Type**:
            - The function returns a list containing:
                - The base atom symbol (with any numeric value removed for non-boolean atoms).
                - The value of the atom (1 or 0 for boolean atoms, or the extracted 
                  numeric value for non-boolean atoms).
                - The type of the atom ('boolean' or non-boolean).

        Example:
            Input: "~door_open"  (a negated boolean literal)
            Output: ["door_open", 0, "boolean"]  (the atom is boolean and negated)

            Input: "elevator_floor_3" (an integer literal where the atom takes the value 3)
            Output: ["elevator_floor", 3, "int"] (the atom is non-boolean and has a value of 3)

        Args:
            lit (str): The literal (boolean or non-boolean) in string format.

        Returns:
            list: A list containing the base atom symbol (str), the atom's value (int), 
                  and the atom's type (str, such as 'boolean' or 'int').
    '''

    def get_atom_val_type (self, lit):
        [atomsymbol, atomsymbol_no_domainval] = self.trim_proposition (lit)
        val = 1
        type = self.symbol_atom_map [atomsymbol_no_domainval].type
        if type == self.boolean_str:
            if self.negation_str in lit:
                val = 0
        else:
            val = self.get_domain_val (atomsymbol)  
        return [atomsymbol_no_domainval, val, type]
    
    def trim_proposition (self, proposition):
        atomsymbol = self.get_atom (proposition)
        atomsymbol_noval = self.remove_domain_val (atomsymbol)
        return [atomsymbol, atomsymbol_noval]

    '''
        This function takes a boolean formula in CNF (Conjunctive Normal Form), 
        parses it into individual clauses, and maps the literals to their corresponding 
        boolean variables or values using a provided mapping. It returns the parsed 
        formula as a list of CNF clauses, where each clause is represented as a list of integers.

        The function also has an option to normalize the formula before processing it.

        Steps involved:
        
        1. **Normalize the Formula (Optional)**:
            - If the `normalize` flag is set to `True`, the formula is first normalized 
              using the `self.normalize_formula()` function, which converts the formula 
              into a standard CNF format and removes spaces.

        2. **Split the Formula into Clauses**:
            - The formula is split into individual clauses using the `&` operator, 
              which separates each clause in a CNF expression.

        3. **Process Each Clause**:
            - For each clause, the literals are further split by the `|` operator, 
              which separates the literals (variables) in each clause.
              
            - For each literal, the following steps are performed:
                a. **Extract Atom Information**:
                    - The atom symbol, its value, and its type (boolean or non-boolean) 
                      are extracted using the `self.get_atom_val_type()` function.
                
                b. **Map to Boolean Variables**:
                    - If the atom is boolean, the corresponding boolean variable is 
                      retrieved from the provided `map` using the atom symbol as a key.
                      
                    - If the atom is non-boolean (e.g., integer domain), the value is also 
                      considered, and the correct boolean variable is retrieved from the 
                      `map` using both the atom symbol and its value.
                      
                c. **Negate Literal if Necessary**:
                    - If the literal is negated (i.e., prefixed with `~`), the value of 
                      the boolean variable is negated (multiplied by -1).
                
                d. **Append to Clause**:
                    - The boolean variable (with its correct sign) is appended to the current clause.

        4. **Store Clauses**:
            - Each processed clause (now a list of integers representing boolean variables) 
              is added to the final list of clauses (`formula_clauses`).

        5. **Return CNF Clauses**:
            - The function returns the final list of clauses, where each clause is a list of 
              boolean variables or their negations.

        Example:
            Input: "(door_open | ~elevator_moving) & elevator_floor_0"
            Output: [[1, -2], [3]]
            - The output represents the CNF clauses, where each literal has been replaced 
              with its corresponding boolean variable.

        Args:
            formula (str): The input boolean formula in CNF as a string.
            map (dict): A dictionary mapping atom symbols (and values for non-boolean atoms) 
                        to boolean variables.
            normalize (bool): A flag indicating whether the formula should be normalized before processing.

        Returns:
            list: A list of CNF clauses, where each clause is a list of integers representing 
                  boolean variables (with negative values indicating negation).
    '''

    def get_cnf_clause (self, formula, map, normalize):
        if normalize:
            formula = self.normalize_formula (formula)
        clauses = formula.split (self.logicalANDstr)
        formula_clauses = []
        for clause in clauses:
            formula_clause = []
            lits = clause.split (self.logicalORstr)
            for lit in lits:
                [atomsymbol, val, type] = self.get_atom_val_type (lit)
                # print (lit)
                # print ('------------------')
                # print (atomsymbol, val, lit, lit.rsplit('_', 1)[1])
                bool_var = 0 
                bool_val = 1
                if type == self.boolean_str:
                    bool_var = map [(atomsymbol, None)]  
                else:
                    bool_var = map [(self.remove_domain_val (atomsymbol), str(val))]   
                if self.negation_str in lit:
                    bool_val = -1  
                formula_clause.append (bool_var*bool_val)
            formula_clauses.append (formula_clause)
        
        return formula_clauses

       
    def extract_atom_info(self, atom):
        match = re.match(self.atom_finder_pattern2, atom)
        if match:
            negation = match.group(1)  # "~" if present, None if absent
            atomsymbol = match.group(2)
            val = match.group(4) if match.group(4) else None  # 'val' only if it exists, else None
            t = match.group(5)  # Always extract t from the last part
            return atomsymbol, val if val != None else None, t
        return None
                        


    '''
    The `Atom` class represents an atom (a propositional variable) in a logical system. 
    Each atom is defined by a symbol (its name), a type (either 'boolean' or another type, 
    such as an integer), and a domain (the range of values the atom can take).

    The class also includes a method to handle the domain based on the atom's type.

    Attributes:
        symbol (str): The name of the atom.
        type (str): The type of the atom, typically 'boolean' or another type (e.g., 'int').
        domain (list): The domain of the atom. For boolean atoms, the domain is [0, 1], 
                       representing False and True. For non-boolean atoms, the domain is 
                       passed as a list of possible values.
    
    Methods:
        __init__(self, symbol, type, domain):
            Initializes an atom with the given symbol, type, and domain. 
            The domain is determined by the atom's type (boolean or non-boolean).

        parse_domain(self, type, domain):
            Determines the domain of the atom based on its type:
            - If the atom is boolean, the domain is set to [0, 1] (representing False and True).
            - For other types, the provided domain is returned as is.
    
    Example:
        - For a boolean atom:
            Input: symbol="door_open", type="boolean", domain=None
            Result: Atom with domain [0, 1]
        
        - For an integer atom:
            Input: symbol="elevator_floor", type="int", domain=[0, 1, 2, 3]
            Result: Atom with domain [0, 1, 2, 3]

    Args:
        symbol (str): The name of the atom.
        type (str): The type of the atom, either 'boolean' or another type like 'int'.
        domain (list): The domain of possible values for the atom (ignored for boolean atoms).

    Returns:
        An instance of the Atom class with the specified attributes.
    '''

class Atom (Helper):
    def __init__ (self,symbol, type, domain):
        self.symbol = symbol
        self.type = type
        self.domain = self.parse_domain (type, domain) 
    
    def parse_domain (self, type, domain):
        if type == self.boolean_str:
            return [0, 1]
        else:
            return domain
            


    '''
    The `Specification` class is designed to represent the formal model of a system for verification purposes. 
    It processes data related to state variables, initial states, transition relations, and safety properties, 
    and constructs the relevant constraints for model checking.

    The class also inherits from a `Helper` class, likely providing additional utility functions such as formula normalization.

    Attributes:
        state_variables (dict): A dictionary of the state variables, categorized by type (e.g., 'boolean', 'int').
        initial_state (list): A list of formulas representing the initial state of the system.
        transition_relations (dict): A dictionary representing the transition relations of the system.
        safety_property (list): A list of formulas representing the safety properties of the system.
        steps (int): The number of time steps to consider for model checking.
        state_atoms (list): A list of `Atom` objects representing the atomic state variables of the system.
        initial_state_constraints (list): A list of CNF formulas representing constraints on the initial state.
        transition_constraints (dict): A dictionary of transition constraints, where keys are transition rule names 
                                       and values are the CNF formulas representing the transitions.
        safety_violation_constraints (list): A list of CNF formulas representing safety violations (negation of safety properties).
        symbol_atom_map (dict): A mapping of state variable symbols to their corresponding `Atom` objects.
    
    Methods:
        __init__(self, steps, data):
            Initializes the Specification object with the provided data, including the state variables, initial states, 
            transition relations, and safety properties. It also builds the necessary constraints for verification.

        create_state_atoms(self):
            Creates `Atom` objects for each state variable in the system. These atoms are stored in the `state_atoms` list 
            and mapped in the `symbol_atom_map` for easy access.

        build_initial_state_constraints(self):
            Processes the initial state formulas, normalizes them, and appends the resulting CNF constraints to 
            `initial_state_constraints`.

        build_transition_constraints(self):
            Converts the preconditions and effects of each transition rule into a logical implication and normalizes it 
            into CNF form. These are stored in `transition_constraints`.

        build_safety_constraints(self):
            Processes the safety properties by negating them (as we check for violations) and converts them into CNF form, 
            storing them in `safety_violation_constraints`.

    Example:
        Input Data Format:
        - state_variables: {'boolean': {'door_open': ['true', 'false']}, 'int': {'elevator_floor': ['0', '1', '2', '3']}}
        - initial_state: "door_open=false,elevator_floor=0"
        - transition_relations: {'open_door': {'preconditions': ["~door_open", "~elevator_moving"], 'effects': ["door_open"]}}
        - safety_property: ["~door_open | ~elevator_moving"]
        
        Upon instantiation, the class will:
        1. Create `Atom` objects for state variables.
        2. Build constraints for the initial state.
        3. Build constraints for the transitions.
        4. Build constraints for the safety properties (in violation form).

        Args:
            steps (int): The number of steps (time frames) to consider in the model.
            data (list): A list containing the state variables, initial state, transition relations, and safety properties.

        Returns:
            An instance of the `Specification` class with fully constructed constraints.
    '''

class Specification (Helper):
    def __init__ (self, steps, data, incremental_encoding):
        self.state_variables = data [0]
        self.initial_state = data [1]
        self.initial_state = self.initial_state.split (self.comma_str)
        self.transition_relations = data [2]
        self.safety_property = data [3]
        self.steps = steps
        self.incremental_encoding = incremental_encoding
        self.temporal_atom = "TV"
        self.state_atoms = []
        self.initial_state_constraints = []
        self.transition_constraints = {}
        self.safety_violation_constraints = []
        self.symbol_atom_map = {}
        self.create_state_atoms ()
        self.build_initial_state_constraints ()
        self.build_transition_constraints ()
        self.build_safety_constraints ()

    def add_temporal_atom (self):
        atom = Atom (self.temporal_atom, self.boolean_str, None)
        self.state_atoms.append (atom)
        self.symbol_atom_map [atom.symbol] = atom

    def create_state_atoms (self):
        for type, states in self.state_variables.items():
            for symbol, val in states.items():
                atom = Atom (symbol, type, val)
                self.state_atoms.append (atom)
                self.symbol_atom_map [symbol] = atom 
        if self.incremental_encoding:
            self.add_temporal_atom ()

    def build_initial_state_constraints (self):
        for formula in self.initial_state:
            formula = self.normalize_formula (formula)
            self.initial_state_constraints.append (formula)

    def build_transition_constraints (self):
        for rule_name, rule in self.transition_relations.items():
            joining_str = self.space_str+self.logicalANDstr+self.space_str
            p =  joining_str.join(rule ["preconditions"])
            q =  joining_str.join(rule ["effects"])
            formula = self.implication_str+self.space_str+self.opening_square_brace+p+self.comma_str+self.space_str+q+self.closing_square_brace
            if self.incremental_encoding:
                formula = self.temporal_atom+self.space_str+self.logicalORstr+self.space_str+self.opening_square_brace+formula+self.closing_square_brace
            formula = self.normalize_formula (formula)
            self.transition_constraints [rule_name] = formula
    
    def build_safety_constraints (self):
        for formula in self.safety_property:
            prefix = ''
            # if self.incremental_encoding:
            #     prefix = self.temporal_atom+self.space_str+self.logicalORstr+self.space_str
            formula = self.normalize_formula (prefix+self.negation_str+self.opening_square_brace+formula+self.closing_square_brace)         
            formula = formula.split (self.logicalANDstr)
            formula = [f.replace(self.opening_square_brace,'').replace (self.closing_square_brace,'') for f in formula]
            for f in formula:
                self.safety_violation_constraints.append (f)

    '''
    The `CNFConverter` class is responsible for converting a system specification into 
    Conjunctive Normal Form (CNF) suitable for use with SAT solvers. It extends both the 
    `Specification` and `Helper` classes, inheriting methods for managing system data and 
    helper functions for formula manipulation.

    This class maps state variables to CNF variables, processes initial state constraints, 
    transition rules, and safety properties, and merges them into a single set of CNF clauses.

    Attributes:
        nvars (int): The total number of CNF variables.
        nclauses (int): The total number of CNF clauses.
        vars (list): A list of CNF variable indices from 1 to nvars.
        state_to_cnf_vars (dict): A mapping from state variables and time steps to CNF variables.
        initial_state_clauses (list): CNF clauses corresponding to the initial state constraints.
        transition_clauses (list): CNF clauses corresponding to the transition relations.
        safety_violation_clauses (list): CNF clauses corresponding to safety property violations.
        cnf_clauses (list): The final list of all CNF clauses (initial state, transition, safety).

    Methods:
        __init__(self, steps, data):
            Initializes the CNFConverter by setting up variables, mapping state variables 
            to CNF variables, and constructing CNF clauses for the initial state, transitions, 
            and safety properties. All CNF clauses are merged at the end.

        build_state_to_cnf_vars(self):
            Maps the state variables to CNF variables. For each time step (from 0 to `steps`), 
            boolean state variables are assigned one CNF variable, while non-boolean variables 
            are assigned multiple CNF variables, one for each value in their domain.
            The total number of CNF variables is stored in `nvars`.

        build_initial_state_cnf(self):
            Converts the initial state constraints into CNF clauses. The initial state is 
            represented by the state variables at time step 0. The resulting clauses are 
            added to `initial_state_clauses`, and the clause count (`nclauses`) is updated.

        build_transition_cnf(self):
            Converts the transition relations into CNF clauses. For each time step, the preconditions 
            and effects of each transition rule are converted into CNF and added to `transition_clauses`. 
            The clause count (`nclauses`) is updated accordingly.

        build_safety_violation_cnf(self):
            Converts the safety property violations into CNF clauses. At each time step, 
            the negated safety properties are transformed into CNF and added to `safety_violation_clauses`. 
            The clause count (`nclauses`) is updated.

        merge_all_cnf_clauses(self):
            Combines all CNF clauses (initial state, transition, and safety violation clauses) 
            into one final list, stored in `cnf_clauses`.

    Example:
        Input Data Format:
        - state_variables: {'boolean': {'door_open': ['true', 'false']}, 'int': {'elevator_floor': ['0', '1', '2', '3']}}
        - initial_state: "door_open=false,elevator_floor=0"
        - transition_relations: {'open_door': {'preconditions': ["~door_open", "~elevator_moving"], 'effects': ["door_open"]}}
        - safety_property: ["~door_open | ~elevator_moving"]
        
        After processing:
        - `state_to_cnf_vars` maps state variables at each time step to corresponding CNF variables.
        - CNF clauses are generated for initial states, transitions, and safety violations.
        - The clauses are merged into a single list in `cnf_clauses`.

    Args:
        steps (int): The number of time steps to consider.
        data (list): A list containing the state variables, initial state, transition relations, and safety properties.

    Returns:
        An instance of the `CNFConverter` class with all constraints represented as CNF clauses, 
        ready to be used with a SAT solver.
    '''

class CNFConverter (Specification, Helper):
    
    def get_timed_constraints (self,constraints):
        modified_constraints = []
        for t in range(0, self.steps + 1):
            for element in self.safety_violation_constraints:
                atoms = element.split(self.logicalORstr)
                updated_atoms = [atom + self.underscore_str + str(t) for atom in atoms]            
                modified_constraints.append(self.logicalORstr.join(updated_atoms))
        return modified_constraints

    def __init__ (self, incremental_encoding, steps, data):
        super ().__init__ (steps, data, incremental_encoding)
        self.nvars = 0
        self.nclauses = 0
        self.vars = []
        self.temporal_bool_vars = {}
        self.temporal_timed_atom = {}
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
            if self.incremental_encoding:
                idx += 1
                self.temporal_bool_vars [t] = idx
                self.temporal_timed_atom [t] = self.temporal_atom+self.underscore_str+str (t)
            self.state_to_cnf_vars[t] = {}  
            for atom in self.state_atoms:
                self.state_to_cnf_vars[t] [atom.symbol] = []
                if atom.type == self.boolean_str:
                    idx = idx + 1  
                    self.state_to_cnf_vars[t] [(atom.symbol, None)] = idx
                else:
                    for val in atom.domain:
                        idx = idx + 1
                        self.state_to_cnf_vars[t] [(atom.symbol, val)] = idx
        self.nvars = idx
        self.vars = list (range (1, self.nvars+1))

   
    def build_initial_state_cnf (self):
        init_state_bool_vars = self.state_to_cnf_vars[0]
        temporal_var = self.temporal_bool_vars [0]
        for formula in self.initial_state_constraints:
            clauses = self.get_cnf_clause (formula, init_state_bool_vars, True)
            for clause in clauses:
                clause.insert(0, -temporal_var)
                self.initial_state_clauses.append (clause)
                self.nclauses += 1

    def build_transition_cnf (self):
        for t in range (0, self.steps+1):
            bool_vars_t = self.state_to_cnf_vars[t]
            for rule_name, formula in self.transition_constraints.items():
                clauses = self.get_cnf_clause (formula, bool_vars_t, False)
                for clause in clauses:
                    if self.incremental_encoding:
                        temporal_var = self.temporal_bool_vars [t]
                        clause.insert(0, -temporal_var)
                    self.transition_clauses.append (clause)
                    self.nclauses += 1
    
    def build_safety_violation_cnf (self):
        # self.safety_violation_constraints is a list of conjuncts eg., ['door_open', 'elevator_moving', '~door_open|~elevator_floor_3']
     
        clause_list = self.get_timed_constraints (self.safety_violation_constraints)    
        results = []
        temporal_var = None
        for clause in clause_list:
            clause_cnf = []
            atoms = clause.split('|')
            for atom in atoms:
                atom = atom.strip('()')  # Strip any parentheses if present
                [atomsymbol, val, t] = self.extract_atom_info(atom)
                bool_var = self.state_to_cnf_vars [int(t)] [(atomsymbol, val)]
                bool_val = 1
                if self.negation_str in atom:
                    bool_val = -1
                lit = bool_var*bool_val
                clause_cnf.append (lit)
                if temporal_var is None:
                    temporal_var = self.temporal_bool_vars [int(t)]
            
            clause_cnf.insert (0,  -temporal_var)
            self.nclauses += 1
            self.safety_violation_clauses.append (clause_cnf)
            temporal_var = None 

    def merge_all_cnf_clauses (self):
        self.cnf_clauses = self.initial_state_clauses.copy()
        self.cnf_clauses.extend (self.transition_clauses)
        self.cnf_clauses.extend (self.safety_violation_clauses)
 

def spec2cnf (inputpath, ouputdir, steps, incremental):
    directory_path = os.path.dirname(inputpath)
    file_name = os.path.splitext(os.path.basename(inputpath))[0]
    
    if len(directory_path)>0:
        directory_path += "/"

    cnf_file_path = ouputdir+"/"+file_name+"_k"+str(steps)+".cnf"
    assumptions_file_path = ouputdir+"/"+file_name+"_assumptions_k"

    file = FileHandler (inputpath,cnf_file_path, assumptions_file_path)
    file.read_file ()

    cnfConverter = CNFConverter (incremental, steps, file.data)
    
    cnf_header = "p cnf "+str(cnfConverter.nvars)+" "+str(cnfConverter.nclauses)
    file.save_to_file (0, cnf_header,
                    cnfConverter.cnf_clauses)
    file.save_to_file (1, cnf_header,
                     list(cnfConverter.temporal_bool_vars.values()))

    return [cnf_file_path, assumptions_file_path]
    


