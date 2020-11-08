from github import Github, Issue, PullRequest
import textwrap
import re

gh = Github(open(".toorg.token").readline().strip())

def find_column():
    for project in gh.get_organization("kyma-project").get_projects():
        # for project in gh.get_user("k15r").get_projects():
        if project.name == "Tunas":
            for column in project.get_columns():
                for name in ["Backlog", "To do", "In Progress"]:
                    if column.name == name:
                        print("* {}".format(name))
                        to_org(column)


def to_org(column):
    indent = 2
    for card in column.get_cards():
        if card.note is not None:
            if card.note.startswith("# "):
                indent = 2
                to_note(card, indent)
                indent = 3
            else:
                to_note(card, indent)
        else:
            content = card.get_content()
            if type(content) is Issue.Issue:
                to_issue(card, content, indent, "ISSUE")
            if type(content) is PullRequest.PullRequest:
                to_issue(card, content, indent, "PULL")


def to_issue(card, content, indent, issue):
    print("{} {}".format('*' * indent, content.title))
    print("#+CARD: {}".format(card.id))
    print("#+{}: {}".format(issue, content.number))
    print("#+URL: {}".format(content.html_url))
    print("#+BEGIN_SRC gfm")
    print(re.sub('^(,?[\*#])',r',\1',content.body, 0, re.MULTILINE))
    print("#+END_SRC")


def to_note(card, indent):
    heading = card.note.split('\n')[0]
    print("{} {}".format('*' * indent, heading.lstrip("# ")))
    print("#+BEGIN_SRC gfm")
    print("{}".format(card.note))
    print("#+END_SRC")
    print("#+CARD: {}".format(card.id))


find_column()
