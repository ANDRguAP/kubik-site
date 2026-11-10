"""Простая проверка HTML перед публикацией сайта (линтинг).
Ищет грубые ошибки: нет DOCTYPE, нет <title>, не закрыты основные теги,
повторяются id. При ошибках завершается с кодом 1 – тогда workflow
останавливается и сайт не публикуется."""
import glob
import sys
from html.parser import HTMLParser

PAIRED = {"html", "head", "body", "header", "nav", "main", "section", "footer",
          "div", "form", "ul", "ol", "table", "script", "style", "a", "button"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.errors, self.warnings = [], set(), [], []
        self.title, self.in_title = "", False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in PAIRED:
            self.stack.append((tag, self.getpos()[0]))
        if tag == "title":
            self.in_title = True
        if "id" in d:
            if d["id"] in self.ids:
                self.errors.append(f"строка {self.getpos()[0]}: повторяется id=\"{d['id']}\"")
            self.ids.add(d["id"])
        if tag == "img" and "alt" not in d:
            self.warnings.append(f"строка {self.getpos()[0]}: у <img> нет атрибута alt")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in PAIRED:
            if not self.stack or self.stack[-1][0] != tag:
                open_tag = self.stack[-1] if self.stack else None
                self.errors.append(f"строка {self.getpos()[0]}: лишний или неверно вложенный </{tag}>"
                                   + (f" (открыт <{open_tag[0]}> в строке {open_tag[1]})" if open_tag else ""))
            else:
                self.stack.pop()

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def check(path):
    text = open(path, encoding="utf-8").read()
    c = Checker()
    c.feed(text)
    if not text.lstrip().lower().startswith("<!doctype html"):
        c.errors.append("файл должен начинаться с <!DOCTYPE html>")
    if not c.title.strip():
        c.errors.append("нет непустого тега <title>")
    for tag, line in c.stack:
        c.errors.append(f"строка {line}: тег <{tag}> не закрыт")
    return c


files = [f for f in glob.glob("**/*.html", recursive=True) if not f.startswith(".github")]
if not files:
    print("HTML-файлы не найдены")
    sys.exit(1)
failed = False
for f in sorted(files):
    res = check(f)
    for w in res.warnings:
        print(f"[предупреждение] {f}, {w}")
    for e in res.errors:
        print(f"[ОШИБКА] {f}, {e}")
    if res.errors:
        failed = True
    else:
        print(f"[OK] {f}")
sys.exit(1 if failed else 0)
