from app.utils.code_generator import generate_short_code


def test_generate_short_code_length():
    code = generate_short_code()

    assert len(code) == 6


def test_generate_short_code_unique():
    codes = {generate_short_code() for _ in range(100)}

    assert len(codes) == 100
