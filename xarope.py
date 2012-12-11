#!/usr/bin//env python
# coding: utf-8

# Author: João S. O. Bueno

"""
Simplified parser for Tubaina  (.afc) markup-code for books and e-books publishing
https://github.com/caelum/tubaina

This single script should provide  some quick and dirty output for 
authors which can thererfore preview their book output
without having to install or build the Java version of Tubaina themselves
"""
import sys

tubaina_style = """
<style>

.code {background: #a0a0c0;}

</style>
"""

# TAG PARAMETERS:
FREE = 0 # free text
SINGLE = 1 # Single, unseparated string
STR = 2  # double quote '"'enclosed arg 
#DASH = 3 # "--" prefixed  argv
PREFIX = 4 # Paramter prefixed by "xx="  (currently only used in the "w=" witdth parameter for img tags)

Tags = {
    "chapter": (FREE,),
    "code": (SINGLE,),
    "section": (FREE,),
    "box": (FREE, ),
    "title": (FREE,),
    "img": (SINGLE, PREFIX, STR),
    "list": (SINGLE,), 
    "quote": (STR, FREE)
    }

title_map = {
 "chapter": "h1",
 "section": "h2",
 "title": "h3"
}

Formatting_Symbols = ("%%", "**")

TEMPLATE = """
<html>
<head>
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 %(style)s
</head>
<body>
  %(body)s
</body>
</html>
"""

class Parser(object):
    def __init__(self, text):
        self.text = text
        
    def _iter_paragraphs(self, text):
        lines = iter(text.split("\n"))
        para = []
        while True:
            try:
                line = lines.next()
            except StopIteration:
                if para:
                    yield u"\n".join(para)
                raise
            _line = line.strip()
            para.append(line)
            if _line.endswith("]") or _line == u"":
                # paragraph contains a tubaina tag that ends here
                # FIXME: will fail for inline tubaina tags that close
                # inside a paragraph, but at the end of a line. 
                # You can win them all with simple code - 
                # The only fix would be to check here if
                # the tag being closed is an inline tag or not
                yield u"\n".join(para)
                para = []
            
    def _htmlize_paragraph(self, text):
        # TODO: look for "%%", "**" and inline "[...]" tags 
        return text
        
    def _htmlize(self, text):
        # Parse dierctly to HTML with hardcoded tags and classes
        # improve if the project ever grows
        inner_html = u""
        inside_list = False
        inside_code = 0
        prev = {"chapter": False, "section": False, "title": False}
        
        code_text = u""
        for para in self._iter_paragraphs(text):
            if inside_code:
                for line in para.split("\n"):
                    if line.strip().startswith(u"[/code"):
                        inside_code -= 1
                        if inside_code == 0:
                            inner_html += u"""<pre class="code"> %s </pre>\n""" % code_text
                            inside_code = 0
                            break
                    # Allows nested code tags:
                    if line.strip().startswith("[code"):
                        inside_code += 1
                    code_text += line + u"\n"
                # Possible unwatched corner case: inline text after a "[/code]" closetag
                continue
            if not para.strip().startswith(u"["): # Not a tubaina tag
                if not inside_list:
                    templ = u"<p>%s</p>\n"
                else:
                    templ = u"<ul>%s</ul>\n"
                #FIXME: add code for ordered lists
                para_html = self._htmlize_paragraph(para)
                inner_html += templ % para_html
            else:
                tag_name = para.split()[0][1:].strip("]")
                #sys.stderr.write(tag_name + "\n")
                try:
                    parameter_spec = Tags[tag_name.lower()]
                except KeyError:
                    sys.stderr.write("""Unknown tubaina tag "%s", ignoring!\n""" % tag_name)
                    continue
                parameters = self._parse_parameters(para, parameter_spec)
                if tag_name in ( "chapter", "section", "title"):
                    html = ""
                    if prev[tag_name]:
                        html += "</div>"
                    html += """<div class="%s" >\n """ % tag_name
                    html += """<%s>%s</%s>\n""" % (title_map[tag_name], parameters[0], title_map[tag_name])
                    prev[tag_name] = True
                    inner_html += html
                elif tag_name == "img":
                    html = """<img src="%s" %%s >  """ % parameters[0]
                    html %= (u"""width="%s" """ % parameters[1]) if len(parameters) >= 2 else u""
                    html += ("""<p class="caption">%s</p>""" % parameters[2]) if len(parameters) >= 3 else u""
                    inner_html += html
                elif tag_name == "code":
                    #TODO: ignoring language sprc parameter for now.
                    # in the future , make use of pygment, as used in the jva tubaina code.
                    inside_code += 1
                    
                    
        # Close open div tags from section, chapters and titles:
        for key, value in prev.items():
            if value:
                inner_html += "</div>"
        return inner_html
            
    def _parse_parameters(self, text, parameter_spec):
        index = text.find(" ")
        if index == -1:
            return []
        parameters = []
        for parameter_type in parameter_spec:
            if parameter_type == FREE:
                parameters.append(text[index: text.find(u"]")].strip())
                break
            leading_whitespace = (len(text[index:]) - len(text[index:].lstrip()) ) 
            if parameter_type in (SINGLE, PREFIX):
                par_text = text[index:].strip().split()[0].strip().strip("]")
                index += leading_whitespace + len(par_text)
                if parameter_type  == PREFIX:
                    par_text = par_text.split("=",1)[-1]
                parameters.append(par_text)
            elif parameter_type == STR:
                try:
                    par_text = text[index:].split('"')[1]
                except IndexError:
                    pass
                index += leading_whitespace + len(par_text) + 2
                parameters.append(par_text)
        return parameters        
                
    def render_html(self, style=""):
        self.inner_html = self._htmlize(self.text)
        self.html = TEMPLATE % {"body": self.inner_html, "style": style}
        return self.html

def main(filename):
    doc = Parser(open(filename).read().decode("utf-8"))
    html = doc.render_html(style=tubaina_style)
    sys.stdout.write(html.encode("utf-8"))

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main(sys.argv[1])
        sys.exit(0)
    sys.stderr.write("""Usage: xarope <filename> \n""")
 