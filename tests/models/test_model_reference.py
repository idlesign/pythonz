from pythonz.apps.models import Reference


def create_reference(title, type_=None, robot=None, **kwargs):
    return Reference.objects.create(
        title=title, type=type_, submitter=robot,
        status=Reference.Status.PUBLISHED, **kwargs)


def test_reference_types(robot):

    ref = Reference.objects.create(
        title='func', type=Reference.Type.FUNCTION, submitter=robot)

    assert ref.is_type_callable  # Enum
    ref.refresh_from_db()
    assert ref.is_type_callable  # Int

    ref = Reference.objects.create(
        title='chap', type=Reference.Type.CHAPTER, submitter=robot)

    assert ref.is_type_bundle
    ref.refresh_from_db()
    assert ref.is_type_bundle


def test_reference_group_by_type(robot):

    chapter = create_reference('chap', Reference.Type.CHAPTER, robot)
    function = create_reference('func', Reference.Type.FUNCTION, robot)
    method = create_reference('meth', Reference.Type.METHOD, robot)
    module = create_reference('mod', Reference.Type.MODULE, robot)

    grouped = Reference.group_by_type([method, function, chapter, module])

    types_plural = Reference.TYPES_PLURAL

    assert grouped == [
        (types_plural[Reference.Type.CHAPTER], [chapter]),
        (types_plural[Reference.Type.MODULE], [module]),
        (types_plural[Reference.Type.FUNCTION], [function]),
        (types_plural[Reference.Type.METHOD], [method]),
    ]

    assert Reference.group_by_type([]) == []
    assert Reference.group_by_type([function]) == [(types_plural[Reference.Type.FUNCTION], [function])]
