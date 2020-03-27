import json
import os
import sys

import nose
from xml.dom import minidom


def parse_ut_metrics(report_path):
    unittest_metrics = dict()
    parsed_xml = minidom.parse(report_path)
    result = parsed_xml.getElementsByTagName('testsuite')[0]
    count_total = int(result.attributes['tests'].value)
    unittest_metrics['UNIT_TEST_TOTAL'] = count_total
    count_errors = int(result.attributes['errors'].value)
    count_failures = int(result.attributes['failures'].value)
    unittest_metrics['UNIT_TEST_FAILURES'] = count_failures
    count_skip = int(result.attributes['skip'].value)
    count_succeses = count_total - count_errors - count_failures - count_skip
    unittest_metrics['UNIT_TEST_SUCCESSES'] = count_succeses
    unittest_metrics['UNIT_TEST_DURATION'] = 0
    return unittest_metrics


def parse_coverage_metrics(report_path):
    def parse_recurrently(element, metrics, all_tags):
        if len(all_tags) > 0:
            tag = all_tags[0]
            remaining_tags = all_tags[1:]
            for inner_element in element.getElementsByTagName(tag):
                metrics['TOTAL_' + tag.upper()] = metrics.get('TOTAL_' + tag.upper(), 0) + 1
                if 'line-rate' in inner_element.attributes and float(inner_element.attributes['line-rate'].value) > 0:
                    metrics['TOTAL_' + tag.upper() + '_COVERED'] = metrics.get('TOTAL_' + tag.upper() + '_COVERED',
                                                                               0) + 1
                else:
                    metrics['TOTAL_' + tag.upper() + '_COVERED'] = 0
                metrics = parse_recurrently(inner_element, metrics, remaining_tags)
            if tag not in element.attributes:
                metrics['TOTAL_' + tag.upper()] = metrics.get('TOTAL_' + tag.upper(), 0)
                metrics['TOTAL_' + tag.upper() + '_COVERED'] = metrics.get('TOTAL_' + tag.upper() + '_COVERED', 0)
            return metrics
        else:
            return metrics

    parsed_xml = minidom.parse(report_path)
    coverage = parsed_xml.getElementsByTagName('coverage')[0]
    tags_hierarchy = ['package', 'class', 'method']

    metrics = parse_recurrently(coverage, {}, tags_hierarchy)
    metrics['TOTAL_LINE'] = coverage.attributes['lines-valid'].value
    metrics['TOTAL_LINE_COVERED'] = coverage.attributes['lines-covered'].value
    metrics['TOTAL_BRANCH'] = coverage.attributes['branches-valid'].value
    metrics['TOTAL_BRANCH_COVERED'] = coverage.attributes['branches-covered'].value
    return metrics


if __name__ == '__main__':
    ut_dir = 'production/tests'
    ut_results = 'results.xml'
    coverage_results = 'coverage.xml'
    ut_times = 'results.xml'

    cov_results_path = os.path.join(ut_dir, coverage_results)
    ut_results_path = os.path.join(ut_dir, ut_results)

    argv = ['nosetests',
            '--with-coverage',
            '--cover-package=mstrio',
            '--cover-xml',
            '--cover-xml-file=' + cov_results_path,
            '--with-xunit',
            '--xunit-file=' + ut_results_path,
            ut_dir]

    try:
        ut_passed = nose.run(argv=argv)
    except Exception as e:
        pass

    coverage_metrics = parse_coverage_metrics(cov_results_path)
    with open(os.path.join(ut_dir, 'coverage_units.json'), 'w+') as f:
        json.dump(coverage_metrics, f)

    ut_metrics = parse_ut_metrics(ut_results_path)

    with open(os.path.join(ut_dir, 'metrics_units.json'), 'w+') as f:
        json.dump(ut_metrics, f)
    if ut_metrics['UNIT_TEST_SUCCESSES'] != ut_metrics['UNIT_TEST_TOTAL']:
        sys.exit(1)
    else:
        sys.exit(0)
