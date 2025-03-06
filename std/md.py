import regex as re
from collections import defaultdict
# pip install markdown-it-py
from markdown_it import MarkdownIt

# Initialize the MarkdownIt parser with some plugins
md = MarkdownIt().enable('table')

from std import __set__
# pip install beautifulsoup4
from bs4 import BeautifulSoup, Tag, NavigableString

# https://markdown.liuchengtu.com/work/
# https://weareoutman.github.io/markdoc/
# https://markdownlivepreview.com/
# https://www.bejson.com/md/

@__set__(Tag)
@property
def has_heading_elements(self):
    return any(
        child.name and re.fullmatch('h\d', child.name)
        for child in self.children
    )


@__set__(NavigableString)
@property
def paragraph_depth(self):
    return self.depth


@__set__(Tag)
@property
def paragraph_depth(self):
    [*children] = self.children
    if not children:
        return self.depth
    return max(child.paragraph_depth for child in children)
    

@__set__(NavigableString)
def set_paragraph_depth(self, depth):
    self.depth = depth


@__set__(Tag)
def set_paragraph_depth(self, depth):
    self.depth = depth
    [*children] = self.children
    if self.has_heading_elements:
        level2children = defaultdict(list)
        for child in children:
            if child.name and (m := re.fullmatch('h(\d)', child.name)):
                level2children[int(m.group(1))].append(child)

        min_level = min(level2children.keys())
        depth_heading = depth
        if len(level2children[min_level]) > 1:
            depth_heading += 1

        current_level = 0
        for child in children:
            if child.name and (m := re.fullmatch('h(\d)', child.name)):
                current_level = int(m.group(1))
            depth_child = current_level - min_level
            depth_child += depth_heading if current_level else depth
            child.set_paragraph_depth(depth_child)
    else:
        depth_list = depth
        if self.name in ('ul', 'ol'):
            if sum(child.name == 'li' for child in children) > 1:
                depth_list += 1
            is_list = lambda child: child.name == 'li'
        elif self.name != 'li':
            if sum(child.name in ('ul', 'ol', 'table') for child in children) > 1:
                depth_list += 1
            is_list = lambda child: child.name in ('ul', 'ol')
        else:
            is_list = lambda _: False

        for child in children:
            child.set_paragraph_depth(depth_list if is_list(child) else depth)


def md2html(markdown, preprocess=True):
    if preprocess:
        markdown = markdown.replace('\n- ', '\n   - ')
        markdown = re.sub(r'(?<=[:：]|\*\*)\n+(?=[a-zA-Z\p{Han}])', ' ', markdown)
        markdown = re.sub(r'\*\*(\d+\. )([^*]+)\*\*', r'\1**\2**', markdown)
        markdown = re.sub(r'(?<=\n)\((\d+)\) ', r'   \1. ', markdown)
        markdown = re.sub(r'(?<=\n |\n  )(\d+)\. ', r'   \1. ', markdown)
    html = md.render(markdown)
    return BeautifulSoup(html, 'html.parser')
