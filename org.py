import collections
import copy
import random
import string

from github import Github, Issue, PullRequest
from itertools import chain
from re import sub


def escape(src_lines):
    lines = []
    if isinstance(src_lines, str):
        sublines = src_lines.splitlines()
    else:
        sublines = src_lines

    for subline in sublines:
        for ssline in subline.splitlines():
            lines.append(sub('^(,?[\*#])', r',\1', ssline))
    return "\n".join(lines)


class Item:
    def __init__(self):
        self.title = ""
        self.children = []
        self.parent = None
        self.type = ""
        self.id = 0
        self.url = ""
        self.gh_issue = ""
        self.lines = []
        self.src_lines = ""
        self.indent = -1
        self.gh_card = None

    def toOrg(self, indent):
        str = []
        if self.title:
            str = ['{} {}'.format(indent * "*", self.title)]
        elif self.src_lines:
            str = ['{} {}'.format(indent * "*", self.src_lines.strip().splitlines()[0].lstrip("*#"))]
        elif self.lines:
            str = ['{} {}'.format(indent * "*", self.lines[0].strip().lstrip("*#"))]
        if self.src_lines:
            str.append("\n".join(["#+BEGIN_SRC gfm", escape(self.src_lines), "#+END_SRC"]))
        if self.id != 0:
            str.append("#+CARD: {}".format(self.id))
        if self.url:
            str.append("#+URL: {}".format(self.url))
        if self.type == 'issue':
            str.append("#+ISSUE: {}".format(self.gh_issue))
        if self.type == 'pull':
            str.append("#+PULL: {}".format(self.gh_issue))
        if self.lines:
            str.append("\n".join(self.lines))
        if self.children:
            for child in self.children:
                str.append(child.toOrg(indent + 1))
        return "\n".join(str)

    def __str__(self):
        if self.title:
            return self.title
        lines = self.src_lines.splitlines()
        if lines:
            return lines[0].strip().lstrip("#*")
        return ""

    def __iter__(self):
        yield self
        for v in chain.from_iterable(self.children):
            yield v

    def update_from_gh_card(self, gh_card):
        if gh_card.note:
            self.src_lines = gh_card.note
        else:
            content = gh_card.get_content()
            self.src_lines = content.body
            self.title = content.title
            self.gh_issue = content.number
            if type(content) is Issue.Issue:
                self.type = 'issue'
                self.indent = -1
            if type(content) is PullRequest.PullRequest:
                self.type = 'pull'
                self.indent = -1


def move(item, last_found):
    if item.parent and item.parent.children:
        item.parent.children.remove(item)
        item.parent = None

    if item.indent == -1 or item.indent > last_found.indent:
        item.parent = last_found
        last_found.children.append(item)
        if item.indent != -1:
            return item
        return last_found
    else:
        cur_item = last_found
        while cur_item and cur_item.indent >= item.indent:
            cur_item = cur_item.parent
        if cur_item:
            cur_item.children.append(item)
            item.parent = cur_item
            if item.indent == -1:
                return item.parent
            else:
                return item
        else:
            print(item, item.indent)


def getTitle(gh_card, content):
    if content:
        return content.title
    else:
        return gh_card.note.splitlines()[0].lstrip('#*').strip()


class Org:
    def __init__(self, file, organisation="", project=""):
        self.__line = ""
        self.__file = file
        self.organisation = organisation
        self.project = project
        self.old = None
        self.item = self.__parse("{}-{}".format(organisation, project))

    def __str__(self):
        str = "#+TITLE: {}-{}\n".format(self.organisation, self.project)
        return str + self.item.toOrg(0)

    def Items(self):
        return self.__items

    def UpdateFromGH(self, columns=[], token=""):
        gh = Github(token)
        for gh_project in gh.get_organization(self.organisation).get_projects():
            if gh_project.name == self.project:
                self.__updateFromProject(gh_project, columns)

    def __updateFromProject(self, project, columns):
        for gh_column in project.get_columns():
            if not columns or gh_column.name in columns:
                for item in self.item:
                    if item.type == "column" and item.title == gh_column.name:
                        item.gh_card = gh_column
                        self.__updateFromColumn(gh_column, item)
                        break
                else:
                    item = Item()
                    item.type = "column"
                    item.title = gh_column.name
                    item.gh_card = gh_column
                    item.indent = 0
                    item.parent = self.item
                    self.item.children.append(item)
                    self.__updateFromColumn(gh_column, item)

    def __to_structure(self, indent):

        is_src = False
        item = Item()
        cur_indent = len(self.__line[0]) - len(self.__line[0].lstrip("*"))
        if cur_indent == 1:
            item.type = "column"
            cur_indent = 0
        item.title = self.__line[0].lstrip("*").strip()
        item.lines = []
        item.children = []
        item.src_lines = ""
        item.indent = cur_indent
        self.__line = (self.__line[0], True)

        for line in self.__file:
            self.__line = (line, False)
            line = self.__line[0]
            if not is_src:
                while self.__line[0].startswith("*") and not self.__line[1]:
                    new_indent = (len(self.__line[0]) - len(self.__line[0].lstrip("*")))
                    if new_indent > indent:
                        new_item = self.__to_structure(len(self.__line[0]) - len(self.__line[0].lstrip("*")))
                        new_item.parent = item
                        item.children.append(new_item)
                    else:
                        return item

                if line.startswith("#+"):
                    line = line.removeprefix("#+")
                    if line.startswith("CARD:"):
                        item.id = line.removeprefix("CARD:").strip()
                    elif line.startswith("PULL:"):
                        item.pull = line.removeprefix("PULL:").strip()
                        item.type = "pull"
                        item.indent = -1
                    elif line.startswith("ISSUE:"):
                        item.issue = line.removeprefix("ISSUE:").strip()
                        item.type = "issue"
                        item.indent = -1
                    elif line.startswith("EPIC"):
                        item.type = "epic"
                    elif line.startswith("BEGIN_SRC"):
                        is_src = True
                else:
                    item.lines.append(line.strip())

            else:
                if line.startswith("#+END_SRC"):
                    is_src = False
                else:
                    item.src_lines = "\n".join([item.src_lines, line.strip()])

        return item

    def __updateFromColumn(self, gh_column, last_column):
        for gh_card in gh_column.get_cards():
            content = None
            if not gh_card.note:
                content = gh_card.get_content()
            last_column = self.__updateFromCard(gh_card, content, last_column)

    def __updateFromCard(self, gh_card, content, last_found):
        gh_title = getTitle(gh_card, content)
        found = None
        prefix = ''.join(random.choices(string.ascii_uppercase, k=4))
        for item in self.item:
            if item.id == 0:
                continue
            if int(item.id) == gh_card.id:
                found = self.__updateItem(content, gh_card, item, last_found)
                return found


        for item in self.item:
            title = str(item)
            if title == gh_title:
                updated_item = self.__updateItem(content, gh_card, item, last_found)
                return updated_item

        # new item:
        item = Item()
        item.id = gh_card.id
        updated_item = self.__updateItem(content, gh_card, item, last_found)
        return updated_item

    def __updateItem(self, content, gh_card, item, last_found):
        item.gh_card = gh_card
        if not content:
            item.src_lines = gh_card.note
            if gh_card.note.startswith("#"):
                heading = gh_card.note.splitlines()[0]
                indent = len(heading) - len(heading.lstrip('#'))
                item.title = heading.lstrip("# ")
                item.indent = indent
        else:
            item.src_lines = content.body
            item.gh_issue = content.number
            item.title = content.title
            if type(content) is Issue.Issue:
                item.type = "issue"
            if type(content) is PullRequest.PullRequest:
                item.type = "pull"
            item.url = content.html_url
        new_last_found = move(item, last_found)
        return new_last_found

    def __parse(self, param):
        item = Item()
        for line in self.__file:
            self.__line = (line, False)
            while self.__line[0].startswith("*") and not self.__line[1]:
                new_indent = (len(self.__line[0]) - len(self.__line[0].lstrip("*")))
                if new_indent > 0:
                    new_item = self.__to_structure(len(self.__line[0]) - len(self.__line[0].lstrip("*")))
                    new_item.parent = item
                    item.children.append(new_item)
        return item
