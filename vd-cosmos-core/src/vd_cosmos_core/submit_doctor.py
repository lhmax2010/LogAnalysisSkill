"""Local checks by default; optional anonymous management clock self-check."""
import importlib
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .analysis_tools import ANALYZER_DEPENDENCIES, check_analysis_dependencies
from .errors import FlowError
from .p4 import validate_config


def php_packages():
    try:
        result = subprocess.run(['dpkg-query', '-W', '-f=${Package} ${Status}\n'], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return {'verified': False, 'count': None}
    if result.returncode: return {'verified': False, 'count': None}
    installed = [line.split()[0] for line in result.stdout.splitlines() if line.endswith('install ok installed')]
    return {'verified': True, 'count': sum('php' in name.casefold() for name in installed)}


def optional_stdlib():
    facts = {}
    for name in ('lzma', 'bz2', 'sqlite3', 'ssl'):
        try:
            importlib.import_module(name)
        except ImportError:
            facts[name] = False
        else:
            facts[name] = True
    return facts


def analysis_dependencies(config):
    try:
        with tempfile.TemporaryDirectory(prefix='analysis-doctor-') as work:
            check_analysis_dependencies(config, work)
    except FlowError as error:
        return {'available': False, **error.as_dict()}
    except OSError:
        return {'available': False, 'error': 'analysis_doctor_workspace_unavailable'}
    return {'available': True, 'modules': list(ANALYZER_DEPENDENCIES)}


def doctor(config, *, reader=None, package_probe=php_packages):
    php = package_probe()
    try: playwright = importlib.metadata.version('playwright')
    except importlib.metadata.PackageNotFoundError: playwright = None
    browser = config.raw.get('browser', {}).get('executable')
    result = {'exit_code': 0, 'online': reader is not None, 'php_packages': php,
              'optional_stdlib': optional_stdlib(),
              'root_list_max_files': config.raw['analyzer']['root_list_max_files'],
              'analysis_dependencies': analysis_dependencies(config),
              'DISPLAY_present': bool(os.environ.get('DISPLAY')), 'playwright_package_version': playwright,
              'browser_available': bool(browser and (Path(browser).is_file() or shutil.which(browser))),
              'browser_version': config.raw.get('browser', {}).get('version_held'),
              'browser_version_basis': '配置登记值；B1 不启动浏览器核验',
              'installations_performed': False, 'timezone_check': '未执行（离线默认）'}
    if not php['verified'] or php['count']:
        result.update(exit_code=6, php_constraint='需要人工检查；本工具不安装或卸载')
    try:
        validate_config(config)
        result['p4_config'] = {'valid': True}
    except FlowError as error:
        result.update(error.as_dict(), p4_config={'valid': False, **error.as_dict()})
        return result
    if reader is None: return result
    def duration_samples(page):
        return [sample for sample in page['samples'] if sample['duration_s'] is not None]

    pages = [reader.overview()]
    samples = duration_samples(pages[0])
    if not samples:
        from .bm_pages import listing
        pages.append(listing(reader.get('/history/' + config.raw['cosmos']['bm_config_id'], history=True), config, 'history'))
        samples = duration_samples(pages[1])
    result['samples_skipped'] = sum(page['samples_skipped'] for page in pages)
    result['samples_skipped_shapes'] = [shape for page in pages for shape in page['samples_skipped_shapes']]
    result['duration_unrecognized'] = [row for page in pages for row in page['duration_unrecognized']]
    clock = reader.samples[-1] if reader.samples else {}
    result['clock'] = clock
    if not samples:
        result.update(timezone_check='页面时区未验证', exit_code=3)
    elif not reader.clock_valid():
        result.update(exit_code=6, timezone_check='时钟样本未核验')
    else:
        sample = min(samples, key=lambda x: x['duration_s'])
        error = sample['start_time'] + sample['duration_s'] - clock['server_time']
        result.update(timezone_error_s=error, timezone_check='通过' if abs(error) <= 120 else '时区或页面口径不对')
        if abs(error) > 120:
            result.update(exit_code=3, todo='页面时区或时间口径需要核对')
    return result
