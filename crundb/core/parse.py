from lark import Lark
from lark import Transformer
tag_parser = Lark(r"""
    ?expr: term (operator term)*
    ?term: tag | "(" expr ")"
    tag: CNAME
        | ESCAPED_STRING
    operator: AND
            | OR
            | ANDNOT

    AND : "&"
    OR  : "|"
    ANDNOT : "!"

    %import common.ESCAPED_STRING
    %import common.WS
    %import common.CNAME
    %ignore WS

    """,start='expr')


class MyTransformer(Transformer):
    def __init__(self,sets):
        self.sets = sets
    def expr(self,items):
        v1 = items[0]
        for i in range(1,len(items),2):
            v2 = items[i+1]
            op = items[i]
            if op == 'AND':
                v1 = v1.intersection(v2)
            elif op == 'OR':
                v1 = v1.union(v2)
            elif op == 'ANDNOT':
                v1 = v1.difference(v2.intersection(v1))

        return v1
    def tag(self,items):
        if '"' in items[0].value:
            items[0].value = items[0].value[1:-1]
        if items[0].value not in self.sets:
           raise SyntaxError("Variable `{}` is not defined as tag at col {}".format(items[0].value,items[0].column))
        return set(self.sets[items[0].value])

    def operator(self,items):
        return items[0].type

def eval_tag_expr(expr:str,retr_val:dict):
    """Summary

    Args:
        expr (str): Description
        retr_val (dict): Description

    Returns:
        TYPE: Description
    """
    # parsing the grammar

    tree = tag_parser.parse(expr)
    return MyTransformer(retr_val).transform(tree)



