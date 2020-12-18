import os
import re

from m2r import convert

def replace_recursively(s, olds, news):
    assert len(olds) == len(news)
    if olds:
        s = s.replace(olds[0], news[0])
        return replace_recursively(s, olds[1:], news[1:])
    else:
        return s

prod_dir = os.getcwd()
sections_dir = os.path.join(prod_dir, 'sphinx', 'sections')
with open(os.path.join(prod_dir, 'README.md')) as f:
    readme = f.read()
with open(os.path.join(prod_dir, 'USAGE.md')) as f:
    usage = f.read()

# sections = readme.replace('####', 'hashtag x4').replace('###', 'hashtag x3').replace('##', 'hashtag x2').split('# ')
# sections = [replace_recursively(section, ['hashtag x4', 'hashtag x3', 'hashtag x2'], ['####', '###', '##']) \
#             for section in sections]
sections = re.split('[^#]# ', readme)
links = sections[-1]
links = '\n[' + links.split('[', maxsplit=1)[1]
sections = ['# ' + '\n'.join([section, links]) for section in sections[:-1]]
sections = sections[:-1] + [usage, sections[-1]]
sections = [s for s in sections if not s.startswith('# Table')]
sections = [s for s in sections if not s.startswith('# Documentation')]

with open(os.path.join(sections_dir, 'intro_modified.rst'), 'w') as f:
    f.write(convert('\n'.join(sections[:2])))

for i, section in enumerate(sections[2:]):
    with open(os.path.join(sections_dir, 'toc'+str(i)+'.rst'), 'w') as f:
        f.write(convert(section))
