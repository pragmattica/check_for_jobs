#!/usr/bin/python
import mechanize

USERNAME = ""
PASSWORD = ""
SITE_URL = ""


def main():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)

    response = br.open(SITE_URL + "/wc2/default.aspx")

    br.select_form("WCHtmlForm1")

    ucontrol = br.form.find_control("UserName")
    ucontrol.value = USERNAME

    pcontrol = br.form.find_control("Password")
    pcontrol.value = PASSWORD

    login_response = br.submit()
    login_response_html = login_response.read()

    menu_response = br.open(SITE_URL + "/wc2/sub/SubOptions.aspx")
    menu_response_html = menu_response.read()

    avail_response = br.open(SITE_URL + "/wc2/sub/SubAvailableJobs.aspx")
    if "No jobs available at this time." in avail_response.read():
        print "No jobs found"
    else:
        print "JOBS AVAILABLE!!!!!!!!!!!!!!!!!!"


if __name__ == "__main__":
    main()