# coding=utf-8
import json
import urllib2
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

import datetime
import schedule

from config import BASE_API_URL, ENDPOINTS, PARKS, EMAIL_FROM, SMTP_SERVER, SMTP_USER, SMTP_PASSWORD

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
parking_update_limit = 24

class TestResult:
    def __init__(self, testName, passed, message):
        self.name = testName
        self.ok = passed
        self.msg = message


class TestResultGroup:
    def __init__(self, groupName, tests):
        self.name = groupName
        self.tests = tests


# Utils

def getEndpoint(endpoint):
    url = BASE_API_URL + endpoint
    try:
        json_obj = urllib2.urlopen(url)
    except urllib2.URLError as e:
        print "Failed to load URL: " + BASE_API_URL + endpoint + " - " + str(e)
        return None
    return json.load(json_obj)


def email(emailObjs):
    for email in emailObjs:
        print "Emailing " + email["email"] + " with content: " + email["content"]
        sendEmail(email["email"], email["subject"], email["content"])


def sendEmail(to, subject, content):
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = to
    s = SMTP(SMTP_SERVER, 465)
    s.login(SMTP_USER, SMTP_PASSWORD)
    s.sendmail(EMAIL_FROM, to, msg.as_string())
    s.quit()


def emailResults(test_results):
    msg = "[ALERT]: Some tests have failed\n\n"
    for testGroup in test_results:
        msg += "\nTest Group: " + testGroup.name + ": \n"
        for test in testGroup.tests:
            msg += "\t\t " + test.name + " - " + test.msg + "\n"
    sendEmail(ENDPOINTS["alert_email"], "API Watchdog Test Failure", msg)


# Check if a given park has had its info updated in the last 24 hours
def testParkUpdatedRecently(parkData):
    updatedDate = datetime.datetime.strptime(parkData["updated"], DATE_FORMAT)
    now = datetime.datetime.now()
    deltaHours = (now - updatedDate).total_seconds() / 3600
    print "[Park Custom Check] Checked park " + parkData[
        "name"] + ": " + "%.0f" % deltaHours + " hours since the last update"
    result = deltaHours < parking_update_limit
    resultMsg = "OK" if result is True else "Updated " + "%.0f" % deltaHours + " hours ago"
    return TestResult("Custom Park Test - Update time for " + parkData["name"], result, resultMsg)


# Tests
def testParks():
    park_data = getEndpoint("parking")
    results = []
    if park_data is not None:
        for k, v in park_data.items():
            testResult = testParkUpdatedRecently(park_data[k])
            results.append(testResult)
            if testResult.ok is False:
                email(PARKS[park_data[k]["name"]])
    else:
        results.append(TestResult("Custom Park Test - Update time", False, "Failed - Invalid JSON"))
    return results


def testEndpoint(endpoint_name):
    result = getEndpoint(endpoint_name) is not None
    testResult = TestResult("Test /" + endpoint_name, result, "OK" if result is True else "Failed")
    print testResult.name + " - " + testResult.msg
    return testResult


def processResults(test_results):
    allTests = []
    for testResultGroup in test_results:
        allTests.extend(testResultGroup.tests)

    # If any test has failed, email the results
    for item in allTests:
        if item.ok is not True:
            print "Some tests failed. Emailing results..."
            emailResults(test_results)
            break


def watchdog():
    test_results = []

    # Simple HTTP tests
    print "----- Performing simple HTTP Tests...  -----"
    public_results = []
    for endpoint_name in ENDPOINTS["public"]:
        public_results.append(testEndpoint(endpoint_name))

    test_results.append(
        TestResultGroup("Public Endpoint HTTP Tests", public_results)
    )

    # Custom tests
    print "----- Performing custom endpoint tests... -----"
    test_results.append(
        TestResultGroup("Custom Park Tests: Updated < 24h ago", testParks())
    )

    # Process results
    processResults(test_results)


# Schedule & Run once
schedule.every().hour.do(watchdog)
watchdog()
