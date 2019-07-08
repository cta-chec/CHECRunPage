from parsimonious.grammar import Grammar

grammar = Grammar(
    """
     #res       = (multiexpr)  (multiexpr)*
     multiexpr = expr (expr)*
     expr      = (op_brac  / bracketed  /  operation ) ws?
     op_brac   = operator bracketed
     operation = (operator tag) / tag
     bracketed = "(" multiexpr ")"
     operator  = ws (and / or / andnot) ws
     and       = "&"
     or        = "|"
     andnot    = "!"
     tag       = ~"[A-Z_0-9]*"i
     ws        = ~"\s*"
     """
)
from parsimonious.nodes import NodeVisitor, rule
import parsimonious


class IniVisitor(NodeVisitor):
    def __init__(self):
        self.operations = []
        self.tags = []

    def visit_bad(self, node, visited_children):
        raise

    def visit_bracketed(self, node, visited):
        _, expr, _ = visited
        return expr

    def visit_operation(self, node, visited):
        n = visited[0][0]
        if n.expr_name == "tag":
            tag = n
            self.tags.append(tag.text)
        else:
            op, tag = visited[0][1]
            self.tags.append(tag[0].text)
            if len(self.tags) > 1:
                self.operations.append(
                    (op[0].expr_name, self.tags.pop(), self.tags.pop())
                )
            elif len(self.tags) == 1:
                self.operations.append((op[0].expr_name, self.tags.pop()))

    def visit_op_brac(self, node, visited):
        op = visited[0][0].expr_name
        if len(self.tags) == 1:
            self.operations.append((op, self.tags.pop()))
        elif len(self.tags) == 2:
            self.operations.append((op, self.tags.pop(), self.tags.pop()))
        else:
            self.operations.append((op,))

    def visit_operator(self, node, visited):
        _, op, _ = visited
        return op[0].children[0], visited

    def visit_tag(self, node, visited):
        #         print('TAG')
        """ Gets the section name. """
        return node, visited

    def generic_visit(self, node, children):
        return node, children


# tree = grammar.parse('(run ! f_k) & N ! (G & H)')
