import json
import os
import sys

import nose
from xml.dom import minidom

test_dir = 'production/tests'
test_results = 'results.xml'
test_times = 'results.xml'
test_argv = ['nosetests',
             '--with-xunit',
             '--xunit-file='+os.path.join(test_dir, test_results),
             test_dir]

if __name__ == '__main__':
    nose.run(argv=test_argv)
    metrics_build = dict()
    parsed_xml = minidom.parse(os.path.join(test_dir, test_results))
    result = parsed_xml.getElementsByTagName('testsuite')[0]
    count_total = int(result.attributes['tests'].value)
    metrics_build['UNIT_TEST_TOTAL'] = count_total
    count_errors = int(result.attributes['errors'].value)
    count_failures = int(result.attributes['failures'].value)
    metrics_build['UNIT_TEST_FAILURES'] = count_failures
    count_skip = int(result.attributes['skip'].value)
    count_succeses = count_total - count_errors - count_failures - count_skip
    metrics_build['UNIT_TEST_SUCCESSES'] = count_succeses
    metrics_build['UNIT_TEST_DURATION'] = 0
    with open(os.path.join(test_dir, 'metrics_units.json'), 'w+') as f:
        json.dump(metrics_build, f)
    if count_failures > 0:
        sys.exit(1)
