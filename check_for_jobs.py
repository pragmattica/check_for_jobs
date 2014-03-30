#!/usr/bin/python
import mechanize

USERNAME = ""
PASSWORD = ""
SITE_URL = ""


def main():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)

    response = br.open(SITE_URL)

    # To iterate through the available forms:
    # for form in br.forms():
    #     print "Form name:", form.name
    #     print form

    br.select_form("WCHtmlForm1")

    # To iterate through the controls in the selected form
    # for control in br.form.controls:
    #     print control
    #     print "type=%s, name=%s value=%s" % (control.type, control.name, br[control.name])

    ucontrol = br.form.find_control("UserName")
    ucontrol.value = USERNAME

    pcontrol = br.form.find_control("Password")
    pcontrol.value = PASSWORD

    login_response = br.submit()
    print login_response.read()


if __name__ == "__main__":
    main()