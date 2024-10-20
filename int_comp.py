import sympy as sp

def encode_a_greater_than_b_large_domain(n):
    """
    Encode a > b for all values of a and b within the range [0, n-1]
    and convert it to CNF.
    """
    # Calculate number of bits needed to represent values in range [0, n-1]
    bit_count = int(sp.ceiling(sp.log(n, 2)))
    
    # Generate bitwise variables for a and b
    a_bits = [sp.Symbol(f'a{i}') for i in reversed(range(bit_count))]
    b_bits = [sp.Symbol(f'b{i}') for i in reversed(range(bit_count))]
    
    # Initialize the formula as None to start building the boolean formula
    formula = None
    
    # For each possible value of a and b (from 0 to n-1)
    for a_val in range(n):
        for b_val in range(n):
            if a_val > b_val:
                # Convert a_val and b_val to binary
                a_bin = f'{a_val:0{bit_count}b}'
                b_bin = f'{b_val:0{bit_count}b}'
                
                # Create the conjunction of bit conditions
                clause = True
                for i in range(bit_count):
                    a_bit = a_bits[i] if a_bin[i] == '1' else ~a_bits[i]
                    b_bit = b_bits[i] if b_bin[i] == '1' else ~b_bits[i]
                    clause = clause & (a_bit & ~b_bit)
                
                # Add this clause to the overall formula
                if formula is None:
                    formula = clause
                else:
                    formula = formula | clause
    
    # Handle the case when formula remains None (no valid conditions)
    if formula is None:
        return False
    
    # Convert to CNF
    cnf_expr = sp.to_cnf(formula, simplify=True)
    return cnf_expr

# Example usage: Encode for a and b in the range [0, 7]
n = 10  # Range [0, 7]
cnf_expr = encode_a_greater_than_b_large_domain(n)
print("CNF for a > b in the range [0, 7]:")
print(cnf_expr)
