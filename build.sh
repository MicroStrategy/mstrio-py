echo "start install pip libraries"
cd /mnt/production
pip install jupyter
pip install nose
pip install pandas
pip install coverage
python setup.py sdist