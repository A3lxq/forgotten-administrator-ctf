def test_genuine_flag_classified_correctly(app):
    result = app.flag_book.classify("SYN{test_one}")
    assert result == {"classification": "genuine", "id": "g1", "points": 100}


def test_decoy_flag_classified_correctly(app):
    result = app.flag_book.classify("FFLAG{test_decoy}")
    assert result == {"classification": "decoy", "id": "d1", "points": 0}


def test_unrecognized_string_is_invalid(app):
    result = app.flag_book.classify("not_a_real_flag")
    assert result["classification"] == "invalid"
    assert result["points"] == 0


def test_classify_strips_whitespace(app):
    result = app.flag_book.classify("  SYN{test_one}  \n")
    assert result["classification"] == "genuine"


def test_genuine_count(app):
    assert app.flag_book.genuine_count == 2
