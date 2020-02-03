from pythonz.apps.models import Reference


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
