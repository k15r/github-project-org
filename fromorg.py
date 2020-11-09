import collections
import pprint

from github import Github, ProjectCard, ProjectColumn, GithubObject, GithubException, Issue, PullRequest

gh = Github(open(".fromorg.token").readline().strip())
column: ProjectColumn = None
is_src = False
card = None
previous_card = None
project = None
max_indent = 2
file = None
line = ""

def find_project(project_name):
    global project
    for gh_project in gh.get_user("k15r").get_projects():
        if gh_project.name == project_name:
            project = gh_project

def find_column(column_name):
    # for project in gh.get_organization("k15r").get_projects():
    for gh_column in project.get_columns():
        if gh_column.name == column_name:
            return gh_column


def find_card():
    global card
    global project
    for gh_column in project.get_columns():
        for gh_card in gh_column.get_cards():
            if card["id"] != "" and gh_card.id == int(card['id']):
                return gh_card
            if gh_card.note == get_lines():
                return gh_card
            content = gh_card.get_content()
            if type(content) is Issue.Issue:
                if content.number == int(card['issue']):
                    return gh_card
            if type(content) is PullRequest.PullRequest:
                if content.number == int(card["pull"]):
                    return gh_card

    return None


def handle_line(line):
    pass

def get_lines():
    if card['src_lines'] != []:
        return "\n".join(card['src_lines'])
    return "\n".join(card['lines'])

def is_pr():
    return card["pull"] != ""
def is_issue():
    return card["issue"] != ""
def has_lines():
    return card["lines"] != [] or card["src_lines"] != []


def update_card():
    global previous_card
    if card is None:
        return
    elif not has_lines():
        return
    if card['id'] != "":
        gh_card = find_card()
    if gh_card is None and column is not None:
        try:
            if is_pr():
                gh_card = column.create_card(GithubObject.NotSet, int(card["pull"]), "PullRequest")
                if previous_card is not None:
                    gh_card.move("after:{}".format(previous_card), column)
                previous_card = gh_card.id
                return
            if is_issue():
                gh_card = column.create_card(GithubObject.NotSet, int(card["issue"]), "Issue")
                if previous_card is not None:
                    gh_card.move("after:{}".format(previous_card), column)
                previous_card = gh_card.id
                return
            if has_lines():
                lines = get_lines()
                gh_card = column.create_card(lines, GithubObject.NotSet, GithubObject.NotSet)
                if previous_card is not None:
                    gh_card.move("after:{}".format(previous_card), column)
                previous_card = gh_card.id
                return
        except GithubException as e:
            print(e)
            return
    if gh_card is not None:
        if has_lines() and not (is_pr() or is_issue()):
            gh_card.edit(get_lines())
            if previous_card is not None:
                gh_card.move("after:{}".format(previous_card), column)
            previous_card = gh_card.id
            return
        else:
            previous_card = gh_card.id



# find_project("test")
# to_cards()


def to_structure(indent):
    global file
    global is_src
    global line

    item = collections.OrderedDict()
    cur_indent = len(line) - len(line.lstrip("*"))
    if cur_indent == 1:
        item["type"] = "column"
    item["title"] = line.lstrip("*").strip()
    item["lines"] = ["{} {}".format("#" * (cur_indent - 1), line.lstrip("*").strip())]
    item['items'] = []
    item['src_lines'] = []
    item['indent'] = cur_indent

    for line in file:
        if not is_src:
            while line.startswith("*"):
                if (len(line) - len(line.lstrip("*"))) > indent:
                    item['items'].append(to_structure(len(line) - len(line.lstrip("*"))))
                else:
                    return item

            if line.startswith("#+"):
                line = line.removeprefix("#+")
                if line.startswith("CARD:"):
                    item["id"] = line.removeprefix("CARD:").strip()
                elif line.startswith("PULL:"):
                    item["pull"] = line.removeprefix("PULL:").strip()
                    item["type"] = "pull"
                elif line.startswith("ISSUE:"):
                    item["issue"] = line.removeprefix("ISSUE:").strip()
                    item["type"] = "issue"
                elif line.startswith("EPIC"):
                    item["type"] = "epic"
                elif line.startswith("BEGIN_SRC"):
                    is_src = True
            else:
                item["lines"].append(line.strip())

        else:
            if line.startswith("#+END_SRC"):
                is_src = False
            else:
                item["src_lines"].append(line.strip())

    return item

file = open('backlog.org')
line = file.readline()
items = collections.OrderedDict()
items['items'] = []
pp = pprint.PrettyPrinter(indent=2, width=200)
indent = len(line) - len(line.lstrip("*"))
pp.pprint (to_structure(indent))

