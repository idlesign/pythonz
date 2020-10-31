import re
from functools import partial
from collections import namedtuple
from os.path import splitext
from datetime import datetime
from typing import List, Dict

import requests
from django.conf import settings
from django.utils import timezone

from ..utils import sync_many_to_many, get_logger, PersonName
from ..signals import sig_send_generic_telegram

if False:  # pragma: nocover
    from ..models import PEP


LOG = get_logger(__name__)

KEYS_REQUIRED: List[str] = ['pep', 'title', 'status', 'type', 'author', 'created']
KEYS_OPTIONAL: List[str] = ['python-version', 'superseded-by', 'replaces', 'requires']
KEYS_ALL: List[str] = KEYS_REQUIRED + KEYS_OPTIONAL

RE_VERSION = re.compile(r'(\d{1,2}.\d{1,2}(.\d{1,2})?)')
RE_MAIL_TYPE1 = re.compile(r'([^<]+)<[^>]+>')
RE_MAIL_TYPE2 = re.compile(r'[^(]+\(([^)]+)\)')


PepInfo = namedtuple('PEPInfo', (
    'num', 'title', 'status', 'type',
    'created', 'authors', 'versions', 'superseded', 'replaces', 'requires'
))


def strip_mail(value: str) -> List[str]:
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


def normalize_date(value: str) -> datetime:
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
            raise Exception(f'Unknown date format `{created}` in `{value}`')

    return created


def get_peps(exclude_peps: List[str] = None, limit: int = None) -> List[PepInfo]:
    """Проходит по репозиторию PEPов и возвращает данные о них в виде
    списка PEPInfo.

    :param exclude_peps: Номера PEP (с ведущиеми нулями), которые можно пропустить.
    :param limit: Максимальное количесто PEP, которые следует обработать.

    """
    LOG.debug('Getting PEPs ...')

    def make_list(pep: dict, key: str):
        pep[key] = [int(chunk.strip()) for chunk in pep.get(key, '').split(',') if chunk.strip()] or []

    def normalize_pep_info(pep: dict):

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

    def get_pep_info(download_url: str) -> PepInfo:
        LOG.debug(f'Getting PEP info from {download_url} ...')

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


def sync(*, skip_deadend_peps: bool = True, limit: int = None) -> Dict[int, 'PEP']:
    """Синхронизирует данные БД сайта с данными PEP из репозитория.

    :param skip_deadend_peps: Следует ли пропустить ПУПы, состояние которых уже не измениться.
    :param limit: Максимальное количесто PEP, которые следует обработать.

    """
    from ..models import Version, PEP, Person, PersonsLinked

    LOG.debug('Syncing PEPs ...')

    map_statuses = {
        'Draft': PEP.Status.DRAFT,
        'Active': PEP.Status.ACTIVE,
        'Withdrawn': PEP.Status.WITHDRAWN,
        'Deferred': PEP.Status.DEFERRED,
        'Rejected': PEP.Status.REJECTED,
        'Accepted': PEP.Status.ACCEPTED,
        'Final': PEP.Status.FINAL,
        'Superseded': PEP.Status.SUPERSEDED,
        'April Fool!': PEP.Status.FOOL,

    }
    map_types = {
        'Process': PEP.Type.PROCESS,
        'Standards Track': PEP.Type.STANDARD,
        'Informational': PEP.Type.INFO,
    }

    exclude_peps = None

    if skip_deadend_peps:
        exclude_peps = PEP.objects.filter(status__in=PEP.STATUSES_DEADEND).values_list('slug', flat=True)

    peps = get_peps(exclude_peps=exclude_peps, limit=limit)

    known_peps = {pep.num: pep for pep in PEP.objects.all()}
    known_versions = []

    submitter_id = settings.ROBOT_USER_ID

    for pep in peps:

        pep: PepInfo

        num = pep.num
        status_id = int(map_statuses.get(pep.status, 0))

        if not status_id:
            # Неизвестный статус. Например, Provisional.
            LOG.warning(f'Unknown status {pep.status} ...')
            continue

        type_id = int(map_types[pep.type])

        LOG.info(f'Working on PEP {num} ...')

        if num in known_peps:

            pep_model: PEP = known_peps[num]

            if pep_model.status != status_id:
                pep_model.status = status_id
                pep_model.save(notify_published=False)

                status_title = PEP.Status(status_id).label

                msg = (
                    f'PEP {pep_model.num} сменил статус на «{status_title}»\n'
                    f'{pep_model.get_absolute_url(with_prefix=True)}'
                )
                sig_send_generic_telegram.send(None, text=msg)

        else:
            LOG.debug(f'PEP {num} is new. Creating ...')

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

    for pep in peps:
        # Для правильного связывания необходимо, чтобы в БД уже были все известные PEP.
        # В этом повторном проходе мы производим связывание.
        pep_model = known_peps[pep.num]
        sync_many_to_many(pep, pep_model, 'superseded', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'replaces', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'requires', 'num', known_peps)
        sync_many_to_many(pep, pep_model, 'authors', 'name_en', known_persons, unknown_handler=create_person)

    LOG.debug('Syncing PEPs done')

    return known_peps
