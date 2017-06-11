import pytest


def test_person():

    from apps.models import Person

    known = {}
    person = Person(
        name='Натаниэль Смит',
        name_en='Nathaniel Smith',
        aka='Nathaniel J. Smith; N.J. Smith',
    )
    Person.contribute_to_known_persons(person, known)

    assert set(known.keys()) == {
        'Смит Натаниэль',
        'Smith N.J.',
        'N. Smith',
        'N.J. Smith',
        'Smith Nathaniel',
        'Натаниэль Смит',
        'Н. Смит',
        'Nathaniel Smith',
        'Nathaniel J. Smith',
        'N. J. Smith'
    }


@pytest.mark.django_db
def test_pep():

    from apps.models import PEP

    pep1 = PEP(num=1)
    pep1.save()

    pep9999 = PEP(num=9999)
    pep9999.save()

    assert pep1.get_link_to_pyorg() == 'https://www.python.org/dev/peps/pep-0001/'
    assert pep9999.get_link_to_pyorg() == 'https://www.python.org/dev/peps/pep-9999/'

    assert pep1.get_absolute_url(with_prefix=True) == 'http://pythonz.net/peps/named/0001/'
    assert pep9999.get_absolute_url(with_prefix=True) == 'http://pythonz.net/peps/named/9999/'


@pytest.mark.django_db
def test_summary():

    from apps.models import Summary

    Summary.create_article()
