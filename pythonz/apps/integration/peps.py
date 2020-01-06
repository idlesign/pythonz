import re
from functools import partial
from collections import namedtuple
from os.path import splitext
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

from ..utils import sync_many_to_many, get_logger, PersonName
from ..signals import sig_send_generic_telegram


LOG = get_logger(__name__)

KEYS_REQUIRED = ['pep', 'title', 'status', 'type', 'author', 'created']
KEYS_OPTIONAL = ['python-version', 'superseded-by', 'replaces', 'requires']
KEYS_ALL = KEYS_REQUIRED + KEYS_OPTIONAL

RE_VERSION = re.compile('(\d{1,2}.\d{1,2}(.\d{1,2})?)')
RE_MAIL_TYPE1 = re.compile('([^<]+)<[^>]+>')
RE_MAIL_TYPE2 = re.compile('[^(]+\(([^)]+)\)')


PepInfo = namedtuple('PEPInfo', (
    'num', 'title', 'status', 'type',
    'created', 'authors', 'versions', 'superseded', 'replaces', 'requires'
))


def strip_mail(value):
    """Удаляет адреса эл. почты из строки author."""
    names = []

    for name in value.split(','):
        name = name.strip()

        matches = RE_MAIL_TYPE1.match(name)

        if not matches:
            matches = RE_MAIL_TYPE2.match(name)

        if matches:
            name = matches.group(1).strip()

        name = PersonName(name)
        name = name.full
        name and names.append(name)

    return names


def normalize_date(value):
    """Нормализует дату (в форматах, используемых в PEP), приводя к datetime."""
    created = value.strip()

    if created:
        if '(' in created:
            created = created[:created.index('(')].strip()

        strptime = partial(datetime.strptime, created)

        # 29-May-2011 / 18-June-2001 / 2011-03-16 / 30 Aug 2012 / 30 March 2013
        for fmt in ['%d-%b-%Y', '%d-%B-%Y', '%Y-%m-%d', '%d %b %Y', '%d %B %Y']:
            try:
                created = timezone.make_aware(strptime(fmt), timezone.get_current_timezone())
                break
            except ValueError:
                continue
        else:
            raise Exception('Unknown date format `%s` in `%s`' % (created, value))

    return created


def get_peps(exclude_peps=None, limit=None):
    """Проходит по репозиторию PEPов и возвращает данные о них в виде
    списка PEPInfo.

    :param list exclude_peps: Номера PEP (с ведущиеми нулями), которые можно пропустить.
    :param int limit: Максимальное количесто PEP, которые следует обработать.
    :rtype: listPepInfo]
    """
    LOG.debug('Getting PEPs ...')

    def make_list(pep, key):
        pep[key] = [int(chunk.strip()) for chunk in pep.get(key, '').split(',') if chunk.strip()] or []

    def normalize_pep_info(pep):

        pep['pep'] = int(pep['pep'])
        pep['author'] = strip_mail(pep['author'])

        version = pep.get('python-version', [])

        if version:
            version_ = []
            for match in RE_VERSION.findall(version):
                version_.append(match[0].replace(',', '.').replace('3000', '3.0'))
            version = version_

        pep['python-version'] = version
        pep['created'] = normalize_date(pep['created'])

        make_list(pep, 'superseded-by')
        make_list(pep, 'replaces')
        make_list(pep, 'requires')

    def get_pep_info(download_url):
        LOG.debug('Getting PEP info from %s ...', download_url)

        response = requests.get(download_url).text

        info_dict = {}
        header = []

        for line in response.splitlines():

            if not line.strip():
                break

            if line[0].strip():
                if ':' not in line:
                    break

                key, value = line.split(':', 1)
                value = value.strip()
                header.append((key, value))
            else:
                # продолжение секции
                key, value = header[-1]
                value = value + line
                header[-1] = key, value

        for key, value in header:
            key = key.lower()
            if key in KEYS_ALL:
                info_dict[key] = value.strip()

        normalize_pep_info(info_dict)

        pep_info = PepInfo(
            num=info_dict['pep'],
            title=info_dict['title'],
            versions=info_dict['python-version'],
            status=info_dict['status'],
            type=info_dict['type'],
            created=info_dict['created'],
            authors=info_dict['author'],
            superseded=info_dict['superseded-by'],
            replaces=info_dict['replaces'],
            requires=info_dict['requires'],
        )

        return pep_info

    exclude_peps = exclude_peps or []
    peps = []
    url_base = 'https://api.github.com/repos/python/peps/contents/'

    pep_counter = 0
    limit = limit or float('inf')

    json = requests.get(url_base).json()
    for item in json:
        name = item['name']

        if not name.startswith('pep-'):
            continue

        name_split = splitext(name)

        ext = name_split[1]
        if item['type'] == 'file' and ext in ('.txt', '.rst'):

            pep_num = name_split[0].replace('pep-', '')
            if pep_num in exclude_peps:
                continue

            peps.append(get_pep_info(item['download_url']))

            pep_counter += 1
            if pep_counter == limit:
                break

    LOG.debug('Getting PEPs done')

    return peps


def sync(skip_deadend_peps=True, limit=None):
    """Синхронизирует данные БД сайта с данными PEP из репозитория.

    :param bool skip_deadend_peps: Следует ли пропустить ПУПы, состояние которых уже не измениться.
    :param int limit: Максимальное количесто PEP, которые следует обработать.
    """
    from ..models import Version, PEP, Person, PersonsLinked

    LOG.debug('Syncing PEPs ...')

    map_statuses = {
        'Draft': PEP.STATUS_DRAFT,
        'Active': PEP.STATUS_ACTIVE,
        'Withdrawn': PEP.STATUS_WITHDRAWN,
        'Deferred': PEP.STATUS_DEFERRED,
        'Rejected': PEP.STATUS_REJECTED,
        'Accepted': PEP.STATUS_ACCEPTED,
        'Final': PEP.STATUS_FINAL,
        'Superseded': PEP.STATUS_SUPERSEDED,
        'April Fool!': PEP.STATUS_FOOL,

    }
    map_types = {
        'Process': PEP.TYPE_PROCESS,
        'Standards Track': PEP.TYPE_STANDARD,
        'Informational': PEP.TYPE_INFO,
    }

    exclude_peps = None
    if skip_deadend_peps:
        exclude_peps = PEP.objects.filter(status__in=PEP.STATUSES_DEADEND).values_list('slug', flat=True)

    peps = get_peps(exclude_peps=exclude_peps, limit=limit)

    known_peps = {pep.num: pep for pep in PEP.objects.all()}
    known_versions = []

    submitter_id = settings.ROBOT_USER_ID

    for pep in peps:  # type: PepInfo

        num = pep.num
        status_id = int(map_statuses.get(pep.status, 0))

        if not status_id:
            # Неизвестный статус. Например, Provisional.
            LOG.warning('Unknown status %s ...', pep.status)
            continue

        type_id = int(map_types[pep.type])

        LOG.info('Working on PEP %s ...', num)

        if num in known_peps:
            pep_model = known_peps[num]  # type: PEP

            if pep_model.status != status_id:
                pep_model.status = status_id
                pep_model.save()

                msg = 'PEP {} сменил статус на «{}»\n{}'.format(
                    pep_model.num,
                    PEP.STATUSES.get(status_id, 'Неизвестный'),
                    pep_model.get_absolute_url(with_prefix=True)
                )
                sig_send_generic_telegram.send(None, text=msg)

        else:
            LOG.debug('PEP %s is new. Creating ...', num)

            pep_model = PEP(
                num=num,
                title=pep.title,
                description=pep.title,
                status=status_id,
                type=type_id,
                time_published=pep.created or '2000-01-01',
                submitter_id=submitter_id,
            )
            pep_model.save(notify_published=True)
            known_peps[num] = pep_model

        if pep.versions:
            known_versions = known_versions or {v.title: v for v in Version.objects.all()}

            # Регистрируем неизвестные сайту версии Питона, указанные в PEP.
            for version in set(pep.versions).difference(known_versions):
                known_versions[version] = Version.create_stub(version)

            sync_many_to_many(pep, pep_model, 'versions', 'title', known_versions)

    known_persons = Person.get_known_persons()

    create_person = PersonsLinked.create_person

    for pep in peps:  # type: PepInfo
        # Для правильного связывания необходимо, чтобы в БД уже были все известные PEP.
        # В этом повторном проходе мы производим связывание.
        pep_model = known_peps[pep.num]
        sync_many_to_many(pep, pep_model, 'superseded', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'replaces', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'requires', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'authors', 'name_en', known_persons, unknown_handler=create_person)

    LOG.debug('Syncing PEPs done')
