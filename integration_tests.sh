echo "start install pip libraries"
cd /mnt/production
pip install nose
pip install pandas
pip install coverage
pip install requests
pip install .
cd ..
echo "start run test with:"
python --version

python -m unittest production/tests/integration/test_suites/narrow_integration_regression.py
[ $? -eq 1 ] && exit 1

python -m unittest production/tests/integration/test_suites/broad_integration_regression.py
[ $? -eq 1 ] && exit 1
