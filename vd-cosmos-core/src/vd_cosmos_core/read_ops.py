"""Public read operations shared by skill APIs and their CLI adapters."""
from .backends import FixtureReportReader, SavedReportReader
from .http_reader import HTTPReportReader
from .errors import FlowError
from .groups import group_expansion


def make_reader(config, backend, *, build_id=None, manifest=None, expected_rows=None):
    if backend == 'real' and build_id is not None:
        return HTTPReportReader(config, build_id, expected_rows)
    if not manifest:
        raise FlowError(2, 'build_id_required' if backend == 'real' else 'manifest_required')
    return (FixtureReportReader if backend == 'fixture' else SavedReportReader)(config, manifest)


def observe(reader):
    return reader.observe(reader.build_ref)


def fetch_logs(reader, observed=None):
    observed = observed if observed is not None else observe(reader)
    if observed['observation_failed']:
        return observed
    reader.require('fetch_log')
    packages = [p for r in observed['reports'].values() for p in r.get('packages', [])
                if p['category'] in {'build_error', 'export_error'}]
    if hasattr(reader, 'fetch_logs'):
        logs = reader.fetch_logs(packages)
    else:
        logs = [{'key': p['key'], **reader.fetch_log(reader.build_ref, p['key']['arch'], p)} for p in packages]
    return {'logs': logs, 'todos': observed['todos'], 'observation': observed, 'exit_code': 0}


def read_action(skill, command, reader, arch=None):
    if skill == 'watch':
        return observe(reader)
    if command == 'inputs':
        return reader.read_inputs(reader.build_ref)
    if command == 'packages':
        if not arch:
            raise FlowError(2, 'architecture_required')
        observed = observe(reader)
        if observed['observation_failed']:
            return observed
        return {**reader.read_packages(reader.build_ref, arch), 'todos': observed['todos'], 'exit_code': 0}
    if command == 'logs':
        return fetch_logs(reader)
    observed = observe(reader)
    if observed['observation_failed']:
        return observed
    packages = [p for r in observed['reports'].values() for p in r.get('packages', [])]
    return {**group_expansion(packages, reader.provides()), 'todos': observed['todos']}
