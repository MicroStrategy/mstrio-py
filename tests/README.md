# Preparing environment before tests
The recommended way to use the tests is by using Python virtual environments.

To install dependencies execute:
```sh
cd production
pip3 install .
```

that's it ...

# Run tests
To run a test suite execute:
```sh
cd production
python3 tests/integration/<test_suite>.py 
```

# Available suites
Currently available test suites are:
 - full_regression.py
 - full_performance.py
