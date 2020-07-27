# To parse the Test-*.xml surefire report
# count num of passed, failed and etc.,
# upload to ci server

import os
import sys
import json
import shutil
from xml.dom import minidom
from flowci import domain, client
from util import GetOutputDir

class Report:
    def __init__(self):
        self.tests = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0

    def add(self, report):
        self.tests += int(report.tests)
        self.failures += int(report.failures)
        self.errors += int(report.errors)
        self.skipped += int(report.skipped)

    def __str__(self):
        return "[REPORT] test: {}, failures: {}, errors: {}, skipped: {}".format(
            self.tests, self.failures, self.errors, self.skipped
        )

    def toStatsDict(self):
        total = self.tests
        success = total - self.failures - self.errors - self.skipped
        return {
            "success": success,
            "failures": self.failures,
            "errors": self.errors,
            "skipped": self.skipped
        }

class Surefire(Report):
    def __init__(self, xmlSuite):
        self.tests = xmlSuite.attributes['tests'].value
        self.failures = xmlSuite.attributes['failures'].value
        self.name = xmlSuite.attributes['name'].value
        self.time = xmlSuite.attributes['time'].value
        self.errors = xmlSuite.attributes['errors'].value
        self.skipped = xmlSuite.attributes['skipped'].value

    def __str__(self):
        return "[{}] test: {}, failures: {}, errors: {}, skipped: {}, time: {}".format(
            self.name, self.tests, self.failures, self.errors, self.skipped, self.time
        )


def findAllReportFiles(path):
    reports = []

    for i in os.listdir(path):
        fullPath = os.path.join(path, i)

        if os.path.isdir(fullPath) and not i.startswith("."):
            reports += findAllReportFiles(fullPath)

        if os.path.isfile(fullPath) and i.startswith("TEST-"):
            reports.append(fullPath)

    return reports


def toReportDictListAndStatistic(reportFiles):
    reports = []
    stats = Report()

    for xmlFile in reportFiles:
        reportDoc = minidom.parse(xmlFile)
        suites = reportDoc.getElementsByTagName('testsuite')
        report = Surefire(suites[0])

        reports.append(report.__dict__)
        stats.add(report)

    return reports, stats


def sendJobReport():
    reports = client.FindFiles("junit-report.html")

    if len(reports) == 0:
        print("[plugin-maven-test]: junit-report.html not found")
        return

    # copy resource to target
    outputDir = GetOutputDir()
    junitDir = os.path.join(outputDir, "junit")
    if os.path.exists(junitDir):
        shutil.rmtree(junitDir, True)
    os.mkdir(junitDir)

    junitResDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "junit")
    shutil.copy(reports[0], junitDir)
    shutil.copytree(os.path.join(junitResDir, "css"), os.path.join(junitDir, "css"))
    shutil.copytree(os.path.join(junitResDir, "images"), os.path.join(junitDir, "images"))

    zipFile = os.path.join(outputDir, "junit-report")
    zipFile = shutil.make_archive(zipFile, 'zip', junitDir)

    api = client.Client()
    status = api.sendJobReport(
        path=zipFile,
        name=domain.JobReportTests,
        zipped="true",
        contentType=domain.ContentTypeHtml,
        entryFile="junit-report.html"
    )
    print("[plugin-maven-test]: upload junit report with status {}".format(status))
    return


def sendFlowStatistic(stats):
    body = {
        "type": "junit",
        "data": stats
    }

    api = client.Client()
    status = api.sendStatistic(body)
    print("[plugin-maven-test]: upload junit statistic data with status {}".format(status))
    return

def start():
    # find all report files
    files = findAllReportFiles(domain.AgentJobDir)

    if len(files) == 0:
        print("[plugin-maven-test]: No junit report found")
        return

    # calculate
    reports, stats = toReportDictListAndStatistic(files)

    # send back to ci server
    sendJobReport()
    sendFlowStatistic(stats.toStatsDict())

    # check errors from unit test
    if stats.errors > 0 or stats.failures > 0:
        sys.exit('exit with unit test error or failure')

start()
