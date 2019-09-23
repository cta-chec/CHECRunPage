from parsimonious.grammar import Grammar

__all__ =['eval_tag_expr']
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
from parsimonious.nodes import NodeVisitor

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
            v2 = self.tags.pop()
            v1 = self.tags.pop()
            self.operations.append((op, v1,v2 ))
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



def eval_tag_expr(expr:str,retr_val:dict):
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
            ops.append(list(op[1:]))
        ops.append(op[0])

    if len(ops)==0:
        ops.append([cv.tags[0]])
    stack = []
    for op in ops:
        if isinstance(op,list):
            for tag in op:
                stack.append(set(retr_val[tag]))
        else:
            stack.append(op)
    stack = list(reversed(stack))
    val_stack = []
    while len(stack)>0:
        op = stack.pop()
        if isinstance(op,str):
            v1 = val_stack.pop()
            v2 = val_stack.pop()
            if op == 'and':
                stack.append(v1.intersection(v2))
            elif op == 'or':
                stack.append(v1.union(v2))
            elif op == 'andnot':
                stack.append(v2.difference(v1.intersection(v2)))
        else:
            #This is non-trivial
            #The current value of the computation is put at
            #the last element of the list while subsequent values
            #(to be operated on) are
            #pushed behind that last value.
            val_stack.insert(-1,op)

    return val_stack.pop()
