import collections


class Org:
    file = None
    __is_src = False
    __line = ""
    items = collections.OrderedDict()

    def __init__(self, file):
        self.file = file
        self.__line = file.readline()
        self.items['items'] = []
        indent = len(self.__line) - len(self.__line.lstrip("*"))
        self.items = self.__to_structure(indent)


    def __to_structure(self, indent):

        item = collections.OrderedDict()
        cur_indent = len(self.__line) - len(self.__line.lstrip("*"))
        if cur_indent == 1:
            item["type"] = "column"
        item["title"] = self.__line.lstrip("*").strip()
        item["lines"] = ["{} {}".format("#" * (cur_indent - 1), self.__line.lstrip("*").strip())]
        item['items'] = []
        item['src_lines'] = []
        item['indent'] = cur_indent

        for self.__line in self.file:
            if not self.__is_src:
                while self.__line.startswith("*"):
                    if (len(self.__line) - len(self.__line.lstrip("*"))) > indent:
                        item['items'].append(self.__to_structure(len(self.__line) - len(self.__line.lstrip("*"))))
                    else:
                        return item

                if self.__line.startswith("#+"):
                    self.__line = self.__line.removeprefix("#+")
                    if self.__line.startswith("CARD:"):
                        item["id"] = self.__line.removeprefix("CARD:").strip()
                    elif self.__line.startswith("PULL:"):
                        item["pull"] = self.__line.removeprefix("PULL:").strip()
                        item["type"] = "pull"
                    elif self.__line.startswith("ISSUE:"):
                        item["issue"] = self.__line.removeprefix("ISSUE:").strip()
                        item["type"] = "issue"
                    elif self.__line.startswith("EPIC"):
                        item["type"] = "epic"
                    elif self.__line.startswith("BEGIN_SRC"):
                        self.__is_src = True
                else:
                    item["lines"].append(self.__line.strip())

            else:
                if self.__line.startswith("#+END_SRC"):
                    self.__is_src = False
                else:
                    item["src_lines"].append(self.__line.strip())

        return item
