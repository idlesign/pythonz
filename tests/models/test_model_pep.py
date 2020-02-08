from pythonz.apps.models import PEP


def test_pep(robot):

    pep1 = PEP(num=1)
    pep1.save()

    pep9999 = PEP(num=9999)
    pep9999.save()

    assert pep1.get_link_to_pyorg() == 'https://www.python.org/dev/peps/pep-0001/'
    assert pep9999.get_link_to_pyorg() == 'https://www.python.org/dev/peps/pep-9999/'

    assert pep1.get_absolute_url(with_prefix=True) == 'https://pythonz.net/peps/named/0001/'
    assert pep9999.get_absolute_url(with_prefix=True) == 'https://pythonz.net/peps/named/9999/'
