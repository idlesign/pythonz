from pythonz.apps.integration.base import RemoteSource


class SourceGroup1(RemoteSource):

    realm = 'group1'


class SourceGroup2(RemoteSource):

    realm = 'group2'


class Src1Grp1(SourceGroup1):

    alias = 'one'


class Src2Grp1(SourceGroup1):

    alias = 'two'


def test_sources():

    assert list(SourceGroup1.get_sources().keys()) == ['one', 'two']
    assert list(SourceGroup2.get_sources().keys()) == []

    assert SourceGroup1.get_source('one') is Src1Grp1

    enum = SourceGroup1.get_enum()
    assert enum.values == ['one', 'two']
