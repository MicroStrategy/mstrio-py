echo "start install pip libraries"
cd /mnt/production
pip install jupyter
pip install nose
pip install pandas
pip install coverage
pip install .
cd ..
echo "start run test with:"
python --version
python production/tests/unit/run_tests.py