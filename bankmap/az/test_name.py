from bankmap.az.name import fix_exp_name


def test_fix_exp_name():
    assert fix_exp_name('10') == '10'
    assert fix_exp_name("map for asdsad") == "map_for_asdsad"
    assert fix_exp_name("map for asdsad 12321") == "map_for_asdsad_12321"
    assert fix_exp_name("map for asdsad-12321.,;}[)(") == "map_for_asdsad-12321_______"
    assert fix_exp_name("map for asdsad-12321.,;}[)(", max_len=5) == "map_f"
    assert fix_exp_name("map for Čįėž a", max_len=15) == "map_for______a"
