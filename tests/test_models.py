
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
