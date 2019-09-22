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
     """)
from parsimonious.nodes import NodeVisitor,rule
import parsimonious

class IniVisitor(NodeVisitor):
    def __init__(self):
        self.operations=[]
        self.tags = []

    def visit_bad(self,node,visited_children):
        raise
    def visit_bracketed(self, node, visited):
        _,expr,_ = visited
        return expr

    def visit_operation(self, node, visited):
        n = visited[0][0]
        if n.expr_name == "tag":
            tag  = n
            self.tags.append(tag.text)
        else:
            op ,tag = visited[0][1]
            self.tags.append(tag[0].text)
            if len(self.tags)>1:
                self.operations.append((op[0].expr_name,self.tags.pop(),self.tags.pop()))
            elif len(self.tags)==1:
                self.operations.append((op[0].expr_name,self.tags.pop()))
    def visit_op_brac(self, node,visited):
        op = visited[0][0].expr_name
        if len(self.tags)==1:
            self.operations.append((op,self.tags.pop()))
        elif len(self.tags)==2:
            self.operations.append((op,self.tags.pop(),self.tags.pop()))
        else:
            self.operations.append((op,))
    def visit_operator(self, node, visited):
        _,op,_ = visited
        return op[0].children[0],visited
    def visit_tag(self, node, visited):
#         print('TAG')
        """ Gets the section name. """
        return node,visited

    def generic_visit(self, node, children):
        return node,children


def parse(expr:str,retr_val:dict):
    """Summary

    Args:
        expr (str): Description
        retr_val (dict): Description

    Returns:
        TYPE: Description
    """
    # parsing the grammar
    tree = grammar.parse(expr)
    cv = IniVisitor()
    cv.visit(tree)
    ops = []
    for op in cv.operations:
        if len(op)>1:
            ops.append(list(op[1:])[::-1])
        ops.append(op[0])

    if len(ops)==0:
        ops.append([cv.tags[0]])
    # Executing operations
    stack = []
    for op in ops:
        if isinstance(op,list):
            for tag in op:
                stack.append(set(retr_val[tag]))
        else:
            v1 =  stack.pop()
            v2 = stack.pop()
            if op == 'and':
                stack.append(v1.intersection(v2))
            elif op == 'or':
                stack.append(v1.union(v2))
            elif op == 'andnot':
                stack.append(v2.difference(v1.intersection(v2)))
    return stack
# tree = grammar.parse('(run ! f_k) & N ! (G & H)')
