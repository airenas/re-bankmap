from bankmap.az.name import fix_exp_name


def test_fix_exp_name():
    assert fix_exp_name('10') == '10'
    assert fix_exp_name("map for asdsad") == "map for asdsad"
    assert fix_exp_name("map for asdsad 12321") == "map for asdsad 12321"
    assert fix_exp_name("map for asdsad-12321.,;}[)(") == "map for asdsad-12321"
    assert fix_exp_name("map for asdsad-12321.,;}[)(", max_len=5) == "map f"
