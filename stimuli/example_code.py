import math

def load_data(path):
    data = []
    with open(path, "r") as f:
        for line in f:
            data.append(float(line.strip()))
    return data

def normalize(values):
    total = sum(values)
    return [v / total for v in values]

def compute_statistics(values):
    mean = sum(values) / len(values)
    variance = sum((v - mean)**2 for v in values) / len(values)
    return mean, math.sqrt(variance)

def main():
    values = load_data("numbers.txt")
    values = normalize(values)

    mean, std = compute_statistics(values)

    if std > 0.2:
        print("High variance detected")
    else:
        print("Variance is normal")

    for i, v in enumerate(values):
        if v > mean:
            print(f"Value {i} is above average")

if __name__ == "__main__":
    main()
