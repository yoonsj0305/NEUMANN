from neumann1.natural_reuse_v056 import numerically_valid


if __name__ == "__main__":
    assert numerically_valid(3.48e-16, 1.0526328239712942e-7)
    assert not numerically_valid(1e-16, 1.1e-6)
    print("corrective numerical tolerance contract smoke PASS")
