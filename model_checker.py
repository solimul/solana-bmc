import sys
from model_to_cnf import spec2cnf
from caller import solve

def main(inputpath, ouputdir, steps, incremental):
    formulapath, assumptionspath = spec2cnf(inputpath, ouputdir, steps, incremental)
    solve(formulapath, assumptionspath)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python model_checker.py <inputpath> <ouputdir> <steps> <incremental>")
        sys.exit(1)
    
    inputpath = sys.argv[1]
    outputdir = sys.argv [2]
    steps = int(sys.argv[3])
    incremental = int(sys.argv[4]) 
    main (inputpath, outputdir, steps, incremental)

