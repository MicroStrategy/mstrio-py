"""
    This is a template for creation of Simple Python Function which can be
    called in a Metric expression.

    It will work out of the box as is, when all variables are filled in.

    Method `get_results` needs to exist and return the values served as the
    metric evaluation results.

    Metric expression example: ScriptFunctionSimple<_InputNames="x, y",
                               _ScriptName=”minus_two_numbers”>(Revenue, Cost)
"""

"""
    `x` is a scalar input
    `y` is a scalar input
"""

def minus_two_numbers(x, y):
    return x - y

# must-have method which returns the values served as the metric evaluation results. 
def get_results():
    return minus_two_numbers($x, $y)

print(get_results())
