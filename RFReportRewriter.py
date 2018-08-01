#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# Author: JiaSongsong
# Date: 2016-04-29

import sys
from pyh import *
import time


CHARSET = 'GB2312'
META = '''<meta http-equiv="Content-Type" content="text/html; charset=%s" /> ''' % CHARSET
CSS = '''<style type="text/css">
body {font-family: Helvetica, sans-serif; font-size: 0.8em; color: black; padding: 6px; background: white;}
.bg_pass {background-color: #00F000;} .bg_fail {background-color: #FF3333;}
table { table-layout: fixed;word-wrap: break-word;empty-cells: show;font-size: 1em;margin: 0 1px;background: white;}
th, td {vertical-align: top;} tr {background: white;} th {background: #DCDCF0;color: black;}
br {mso-data-placement: same-cell;} .parent-name {font-size: 0.7em;letter-spacing: -0.07em;}
h1 {float: left;margin: 0 0 0.5em 0;width: 75%;} h2 {clear: left;}
.details {border: 1px solid black;border-collapse: collapse;clear: both;width: 65em;margin-bottom: 1em;}
.details th {background: white;width: 10em;white-space: nowrap;text-align: left;vertical-align: top;padding: 0.2em 0.4em;}
.details td {vertical-align: top;padding: 0.2em 0.4em;} .error, .fail {color: red !important;font-weight: bold;}
.pass {color: #009900 !important;} .statistics {width: 65em;border-collapse: collapse;empty-cells: show;margin-bottom: 1em;}
.statistics tr:hover {background: #ECECF7;cursor: pointer;} .statistics th, .statistics td {border: 1px solid black;padding: 0.1em 0.3em;}
.statistics th {background-color: #DCDCF0;padding: 0.2em 0.3em;} .statistics td {vertical-align: middle;}
.stats-col-stat {width: 4.5em;text-align: center;} .stats-col-elapsed {width: 5.5em;text-align: center;}
.stats-col-name {color: blue;font-weight: bold;} .stats-col-graph {width: 9em;}
.graph, .empty-graph {border: 1px solid black;width: auto;height: 7px;padding: 0;background: red;}
.pass-bar, .fail-bar {float: left;height: 100%;} .pass-bar {background: #00F000;}
#errors {width: 100%;border-spacing: 0;border: 1px solid gray;padding: 0.3em 0.2em;margin: 0.2em 0;}
.error-time {width: 11em; white-space: nowrap; color: blue;}
.level {width: 4.5em;text-align: center;color: #FFCC00;font-weight: bold;} .message {white-space: pre-wrap;}
</style>'''


def time2str(millisec):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(millisec/1000))


def generate_bar(passed, failed):
    total = passed + failed
    pass_perent = 100.0 * passed / total
    fail_perent = 100.0 * failed / total
    mydiv = div(cl='graph')
    mydiv << div(cl='pass-bar', style='width: %d%%' % pass_perent, title='%.1f%%' % pass_perent)
    mydiv << div(cl='fail-bar', style='width: %d%%' % fail_perent, title='%.1f%%' % fail_perent)
    return mydiv.render()


def generate_stat_table_header(table_name):
    table_header = tr()
    table_header << th(table_name)
    table_header << th('Total', cl='stats-col-stat')
    table_header << th('Pass', cl='stats-col-stat')
    table_header << th('Fail', cl='stats-col-stat')
    table_header << th('Elapsed', cl='stats-col-elapsed')
    table_header << th('Pass/Fail', cl='stats-col-graph')
    return table_header.render()


def generate_stat_table_line(stat_suite):
    # {"elapsed":"02:26:23","fail":17,"label":"Critical Tests","pass":149}
    failed, passed = stat_suite['fail'], stat_suite['pass']
    table_line = tr()
    table_line << td(stat_suite['label'].decode('utf8').encode(CHARSET), cl='stats-col-name')
    table_line << td(passed+failed, cl='stats-col-stat')
    table_line << td(passed, cl='stats-col-stat')
    cls = ' bg_fail' if failed > 0 else ''
    table_line << td(failed, cl='stats-col-stat' + cls)
    table_line << td(stat_suite['elapsed'], cl='stats-col-elapsed')
    table_line << td(generate_bar(passed, failed), cl='stats-col-graph')
    return table_line.render()


def get_result_stats(orig_report):
    starttime, elapsed, stats = 0, 0, []
    starttime_keyword = 'window.output["baseMillis"] = '
    elapsed_keyword = 'window.output["generatedMillis"] = '
    stats_keyword = 'window.output["stats"] = '
    with open(orig_report, 'r') as f:
        for line in f:
            if line.startswith(starttime_keyword):
                starttime = int(line[len(starttime_keyword):-2].strip('"'))
            elif line.startswith(elapsed_keyword):
                elapsed = int(line[len(elapsed_keyword):-2].strip('"'))
            elif line.startswith(stats_keyword):
                stats_str = line[len(stats_keyword):-2]
                stats = eval(stats_str)
            if starttime and elapsed and stats:
                break
    return starttime, starttime+elapsed, stats


def get_all_stats(totoal_stats):
    elapsed, fail_num, pass_num = '', 0, 0
    for item in totoal_stats:
        if item.get('label', '') == 'All Tests':
            elapsed, fail_num, pass_num = item.get('elapsed', 0), item.get('fail', 0), item.get('pass', 0)
            break
    return elapsed, fail_num, pass_num


def convert(orig_report, new_report):
    starttime, endtime, result_stats = get_result_stats(orig_report)
    if not result_stats or len(result_stats) < 3:
        print '###### Get result stats from report file<%s> failed!' % (orig_report)
        return

    totoal_stats = result_stats[0]
    tag_stats = result_stats[1]
    suite_stats = result_stats[2]

    elapsed, fail_num, pass_num = get_all_stats(totoal_stats)

    page = PyH('SystemTest Test Report')
    page.head.append(META)
    page.head.append(CSS)

    if fail_num > 0:
        status = '%d critical tests failed' % fail_num
        cls = 'fail'
    else:
        status = 'All tests passed'
        cls = 'pass'

    html_body = page << body(cl='bg_' + cls)

    # Summary Information
    html_body << h2('Summary Information')
    details_table = html_body << table(cl='details')
    details_table << tr() << th('Status:') + td(status, cl=cls)
    details_table << tr() << th('Start Time:') + td(time2str(starttime))
    details_table << tr() << th('End Time:') + td(time2str(endtime))
    details_table << tr() << th('Elapsed Time:') + td(elapsed)

    stats_div = html_body << div(id="statistics-container")

    # Test Statistics
    stats_div << h2('Test Statistics')
    total_stat_table = stats_div << table(cl='statistics', id="total-stats")
    total_stat_table << generate_stat_table_header('Total Statistics')
    for item in totoal_stats:
        total_stat_table << generate_stat_table_line(item)

    # Statistics by Tag
    stat_by_tag_table = stats_div << table(cl='statistics', id="tag-stats")
    stat_by_tag_table << generate_stat_table_header('Statistics by Tag')
    for item in tag_stats:
        stat_by_tag_table << generate_stat_table_line(item)

    # Statistics by Suite
    stat_by_suite_table = stats_div << table(cl='statistics', id="suite-stats")
    stat_by_suite_table << generate_stat_table_header('Statistics by Suite')
    for item in suite_stats:
        stat_by_suite_table << generate_stat_table_line(item)

    page.printOut(new_report)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s orig_report_path new_report_path' % sys.argv[0]
        print 'Demo : %s orig/report.html new/report.html' % sys.argv[0]
    else:
        orig_report_path = sys.argv[1]
        new_report_path = sys.argv[2]

        convert(orig_report_path, new_report_path)
        print "Convert report file <%s> to new report file <%s> success!" % (orig_report_path, new_report_path)
