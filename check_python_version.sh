# accept version number as a parameter
ver=$1
# install specified Python version with pyenv
pyenv install $ver
pyenv local $ver
# run tests on the specified Python version
python production/tests/unit/run_tests.py > result
pyenv local system