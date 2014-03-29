#!/usr/bin/python
from ghost import Ghost

USERNAME = ""
PASSWORD = ""
SITE_URL = ""


def main():
    ghost = Ghost()

    page, extra_resources = ghost.open(SITE_URL)
    assert page.http_status == 200

    result, resources = ghost.set_field_value("input[name=UserName]", USERNAME)
    result, resources = ghost.set_field_value("input[name=Password]", PASSWORD)

    ghost.click("input[name=Submit]")
    page, extra_resources = ghost.wait_for_page_loaded()
    #assert page.http_status == 200

    print page.content

if __name__ == "__main__":
    main()