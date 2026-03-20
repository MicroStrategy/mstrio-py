"""
    This is a template for creation of Aggregation Python Function which can be
    called in a Metric expression.

    It will work out of the box as is, when all variables are filled in.

    Method `get_results` needs to exist and return the values served as the
    metric evaluation results.

    Metric expression example: ScriptFunctionAggregation<_InputNames="lst, n",
                               _ScriptName=”nth_minimal_value”>( Cost, 2){~+}
"""

"""
    `lst` is a vector input
    `n` is a vector input
"""

def nth_minimal_value(lst, n):
    # Sort the list in ascending order
    sorted_lst = sorted(lst)

    # Check if n is within the range of the list length
    if n <= 0 or n > len(sorted_lst):
        raise ValueError("n is out of the valid range")

    # Return the nth minimal value (1-based index)
    return sorted_lst[n-1]

# must-have method which returns the values served as the metric evaluation results.
def get_results():
    return nth_minimal_value($lst, $n)

print(get_results())
