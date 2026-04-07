import random

def get_cycle_plan(test_mapping, iteration):

    categories = {}

    for test, suite in test_mapping.items():
        categories.setdefault(suite, []).append(test)

    selected_tests = []

    for suite, tests in categories.items():

        # Rotate selection using iteration number
        idx = hash(iteration) % len(tests)
        selected_tests.append(tests[idx])

    return selected_tests