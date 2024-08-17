# python run.py frumblesnatch-v1 python-algo snorkeldink-v3-3

import subprocess
import os
import sys

def run_match(algo1, algo2):
    """Run a match between two algorithms and return the result."""
    cmd = ['./scripts/run_match.sh', algo1, algo2]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error running match between {algo1} and {algo2}: {stderr.decode('utf-8')}", file=sys.stderr)
        return None

    damage_received_1 = 0
    damage_received_2 = 0
    # Find the line with "Winner"
    for line in stdout.decode('utf-8').splitlines():
        if "Got scored on at" in line:
            if algo1 in line:
                damage_received_1 += 1
            else:
                damage_received_2 += 1
        if "Winner" in line:
            winner = algo1 if line.strip()[-1]=='1' else algo2
            return "{} vs {}: damage_received_1: {}, damage_received_2: {}, winner: {}".format(
                algo1, algo2, damage_received_1, damage_received_2, winner)

    return "No winner found"

def main(algorithms):
    results = []
    n = len(algorithms)

    for i in range(n):
        for j in range(i + 1, n):
            algo1 = algorithms[i]
            algo2 = algorithms[j]
            print(f"Comparing {algo1} with {algo2}...")
            result = run_match(algo1, algo2)
            print(result)
            if result:
                results.append(result)
    
    # Concatenate all results
    with open('match_results.txt', 'w') as f:
        f.write("\n".join(results))
    
    print("All matches completed. Results written to match_results.txt.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <algo1> <algo2> ... <algoN>")
        sys.exit(1)
    
    main(sys.argv[1:])
