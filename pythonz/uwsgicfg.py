from uwsgiconf.config import configure_uwsgi
from uwsgiconf.presets.nice import PythonSection


def get_configurations():

    from django.conf import settings

    in_production = settings.IN_PRODUCTION

    project = settings.PROJECT_NAME
    domain = settings.PROJECT_DOMAIN

    dir_state = settings.PROJECT_DIR_STATE

    section = PythonSection.bootstrap(
        f'http://:{80 if in_production else 8000}',
        allow_shared_sockets=in_production,

        wsgi_module=f'{project}.wsgi',
        process_prefix=f'[{project}] ',

        workers=2,
        threads=3,

        log_dedicated=True,
        ignore_write_errors=True,
        touch_reload=f"{dir_state / 'reloader'}",
        owner=project if in_production else None,
    )

    section.set_runtime_dir(f'{settings.PROJECT_DIR_RUN}')

    section.main_process.change_dir(f'{dir_state}')

    section.spooler.add(f"{dir_state / 'spool'}")

    if in_production and domain:
        section.configure_certbot_https(
            domain=domain,
            webroot=f"{dir_state / 'certbot'}",
            allow_shared_sockets=True)

    section.configure_maintenance_mode(
        f"{dir_state / 'maintenance'}", section.get_bundled_static_path('503.html'))

    return section


configure_uwsgi(get_configurations)
