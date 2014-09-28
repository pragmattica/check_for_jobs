#!/usr/bin/python
import os, mechanize, datetime, time, subprocess, pytz
from pytz import timezone

from bs4 import BeautifulSoup

USERNAME = ""
PASSWORD = ""
SITE_URL = ""
TO_NOTIFY = [""]


class Job(object):
    def __init__(self, requested, job_id_str, desc_str):
        self.requested = requested
        self.job_id_str = job_id_str
        self.desc_str = desc_str
        self.start_datetime, self.end_datetime = self.parse_desc_str(self.desc_str)
        self.duration = self.end_datetime - self.start_datetime
        self.num_hours = self.duration.total_seconds() // 3600
        self.num_minutes = (self.duration.total_seconds() - (self.num_hours * 3600)) // 60
        self.duration_str = str(int(self.num_hours)).zfill(2) + ":" + str(int(self.num_minutes)).zfill(2)

    def parse_special_date_time(self, date_str, time_str):
        month_str, day_str, year_str = date_str.split('/')
        hour_str, minute_str = time_str.split(':')
        revised_datetime_str = month_str.zfill(2) + '/' + day_str.zfill(2) + '/' + year_str + ' ' + hour_str.zfill(2) + ":" + minute_str
        if revised_datetime_str.endswith('AM'): revised_datetime_str = revised_datetime_str[:-2] + 'am'
        if revised_datetime_str.endswith('PM'): revised_datetime_str = revised_datetime_str[:-2] + 'pm'
        naive_datetime_obj = datetime.datetime.strptime(revised_datetime_str, "%m/%d/%Y %I:%M%p")
        eastern = timezone('America/Toronto')
        datetime_obj = eastern.localize(naive_datetime_obj)
        return datetime_obj

    def parse_desc_str(self, desc_str):
        cut_str = desc_str.strip()
        if desc_str.endswith(" (A) ") or desc_str.endswith(" (S)"):
            cut_str = cut_str[:-4]
            cut_str = cut_str.strip()
        start_datetime_str, end_datetime_str = cut_str.split(" until ")
        start_date_str, start_time_str = start_datetime_str.split(" at ")
        end_date_str, end_time_str = end_datetime_str.split(" at ")
        start_date_obj = self.parse_special_date_time(start_date_str, start_time_str)
        end_date_obj = self.parse_special_date_time(end_date_str, end_time_str)
        return (start_date_obj, end_date_obj)

# Parses the jobs list and returns a tuple containing a list of requested jobs and a second list
# of available jobs.
def parse_jobs(avail_response_html):
    # Figure out if the table of jobs is split into two sections
    soup = BeautifulSoup(avail_response_html, "lxml")
    tables = soup.find_all('table')
    for t in tables:
        data = t.find_all('td')
        if data[0].text == u'Job ID' and data[1].text == u'Employee': # This is the table listing the jobs
            rows = [c for c in t.contents if str(c).isspace() == False]
            if rows[1].text == u'You have been requested for the following jobs': # Two sections
                in_request_section = True
                request_list, avail_list = [], []
                for r in rows[2:]:
                    if in_request_section == True and len(r.find_all('td')) == 5:
                        new_req_job = Job(True, 0, r.find_all('td')[4].text)
                        request_list.append(new_req_job)
                    elif in_request_section == True and len(r.find_all('td')) != 5:
                        in_request_section = False
                    elif in_request_section == False and len(r.find_all('td')) == 5:
                        new_avail_job = Job(False, 0, r.find_all('td')[4].text)
                        avail_list.append(new_avail_job)
                return (request_list, avail_list)

            else: # Single section
                avail_list = []
                for r in rows[1:]:
                    new_avail_job = Job(False, 0, r.find_all('td')[4].text)
                    avail_list.append(new_avail_job)
                return ([], avail_list)

def notify_all(msg, title):
    for n in TO_NOTIFY:
        params = ["ssh", n, "osascript -e 'display notification \"" + msg + "\" with title \"" + title + "\" sound name \"Submarine\"'"]
        subprocess.call(params)
    print str(datetime.datetime.now()) + " Sent notification '" + msg + "' with title '" + title + "'"

def main():
    if SITE_URL == "":
        print "Need to enter a SITE_URL to use this script"

    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)

    # Open the site and log in
    response = br.open(SITE_URL + "/wc2/default.aspx")

    br.select_form("WCHtmlForm1")

    ucontrol = br.form.find_control("UserName")
    ucontrol.value = USERNAME

    pcontrol = br.form.find_control("Password")
    pcontrol.value = PASSWORD

    login_response = br.submit()
    login_response_html = login_response.read()

    # Get the three frames that make up the page (two of these
    # frames won't be examined, but they are retrieved anyway just
    # to make this script look more like a web-browser and less like
    # a bot)
    title_response = br.open(SITE_URL + "/wc2/title.aspx")
    title_response_html = title_response.read()

    message_response = br.open(SITE_URL + "/wc2/common/Message.aspx")
    message_response_html = message_response.read()

    menu_response = br.open(SITE_URL + "/wc2/sub/SubOptions.aspx")
    menu_response_html = menu_response.read()

    avail_response = br.open(SITE_URL + "/wc2/sub/SubAvailableJobs.aspx")
    avail_response_html = avail_response.read()

    if os.path.isfile("/tmp/check_for_jobs_send_alive.tmp"):
        notify_all("The check_for_jobs script is active!", "check_for_jobs")
        os.remove("/tmp/check_for_jobs_send_alive.tmp")
        print str(datetime.datetime.now()) + " Sent notice that check_for_jobs is active"

    if "No jobs available at this time." in avail_response_html:
        print str(datetime.datetime.now()) + " No jobs found"
    else:
        print str(datetime.datetime.now()) + " JOBS AVAILABLE!!!!!!!!!!!!!!!!!!"
        t = str(time.time())
        with open(t + ".log", 'w') as fout:
            fout.write(avail_response_html)

        try:
            # Retrieve the listed jobs
            (request_jobs, avail_jobs) = parse_jobs(avail_response_html)
            num_jobs = len(request_jobs) + len(avail_jobs)

            # Send notifications to OS X computers via ssh
            plurality_str = "job is"
            if num_jobs > 1:
                plurality_str = "jobs are"
            msg = str(num_jobs) + " " + plurality_str + " listed (" + str(len(request_jobs)) + " requested; " + str(len(avail_jobs)) + " available)"
            title = "check_for_jobs"
            notify_all(msg, title)

        except Exception, e:
            print str(datetime.datetime.now()) + " Exception occurred: " + str(e)

    # Now that we've finished using the web application, it seems polite
    # to log out
    logout_response = br.open(SITE_URL + "/wc2/Login/LOGOUT.aspx")
    logout_response_html = logout_response.read()


if __name__ == "__main__":
    main()