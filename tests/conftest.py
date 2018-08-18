import pytest

import pythotk


# https://docs.pytest.org/en/latest/doctest.html#the-doctest-namespace-fixture
@pytest.fixture(autouse=True)
def add_tk(doctest_namespace):
    doctest_namespace['tk'] = pythotk
