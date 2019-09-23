from crundb.core.parse import eval_tag_expr
import pytest
import copy
@pytest.fixture
def test_sets():
    whole = list(range(10))
    even = whole[::2]
    odd = whole[1::2]
    fivesix = [5,6]
    sets = dict(whole=whole, even=even, odd=odd, fivesix=fivesix, )
    return sets

def test_eval_tag_exprs_and(test_sets):
    sets = test_sets
    res = eval_tag_expr('whole & even',sets)
    assert list(res) == sets['even'], "Picking out even numbers from the whole set"

def test_eval_tag_exprs_or(test_sets):
    sets = test_sets
    res = eval_tag_expr('odd | even',sets)
    assert list(res) == sets['whole'], "odd `or` even makes whole"


def test_eval_tag_exprs_andnot(test_sets):
    sets = test_sets
    res = eval_tag_expr('fivesix ! even',sets)
    assert list(res) == [5], "Picking out 5 using andnot"
    res = eval_tag_expr('even ! fivesix',sets)
    assert sorted(list(res)) == [0,2,4,8], "Picking out all even except 6 using andnot (andnot is not unitary)"



def test_eval_tag_exprs_parentheses(test_sets):
    sets = test_sets
    res1 = eval_tag_expr('(whole ! even) | fivesix',copy.copy(sets))
    res2 = eval_tag_expr('whole ! (even | fivesix)',copy.copy(sets))
    assert res1 != res2, "`(whole ! even) | fivesix` is not equal to `whole ! (even | fivesix)`"
    assert sorted(list(res1)) == [1,3,5,6,7,9], "Correct result for: `(whole ! even) | fivesix`"
    assert sorted(list(res2)) == [1,3,7,9], "Correct result for: `whole ! (even | fivesix)`"

def test_eval_tag_exprs_nested_parentheses(test_sets):
    sets = test_sets
    res = eval_tag_expr('fivesix | (whole & (even & fivesix))',copy.copy(sets))
    assert sorted(list(res)) == [5,6],"Correct result for: `fivesix | (whole & (even & fivesix))`"
    res = eval_tag_expr('(fivesix | whole) & (even & fivesix)',copy.copy(sets))
    assert sorted(list(res)) == [6], "Correct result for: `(fivesix | whole) & (even & fivesix)`"