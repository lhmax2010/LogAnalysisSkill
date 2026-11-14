"""Local checks by default; optional anonymous management clock self-check."""
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess

from .errors import FlowError


def php_packages():
    try:
        result = subprocess.run(['dpkg-query', '-W', '-f=${Package} ${Status}\n'], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return {'verified': False, 'count': None}
    if result.returncode: return {'verified': False, 'count': None}
    installed = [line.split()[0] for line in result.stdout.splitlines() if line.endswith('install ok installed')]
    return {'verified': True, 'count': sum('php' in name.casefold() for name in installed)}


def doctor(config, *, reader=None, package_probe=php_packages):
    php = package_probe()
    try: playwright = importlib.metadata.version('playwright')
    except importlib.metadata.PackageNotFoundError: playwright = None
    browser = config.raw.get('browser', {}).get('executable')
    result = {'exit_code': 0, 'online': reader is not None, 'php_packages': php,
              'DISPLAY_present': bool(os.environ.get('DISPLAY')), 'playwright_package_version': playwright,
              'browser_available': bool(browser and (Path(browser).is_file() or shutil.which(browser))),
              'browser_version': config.raw.get('browser', {}).get('version_held'),
              'browser_version_basis': '配置登记值；B1 不启动浏览器核验',
              'installations_performed': False, 'timezone_check': '未执行（离线默认）'}
    if not php['verified'] or php['count']:
        result.update(exit_code=6, php_constraint='需要人工检查；本工具不安装或卸载')
    if reader is None: return result
    overview = reader.overview(); samples = overview['samples']
    if not samples:
        from .bm_pages import listing
        page = listing(reader.get('/history/' + config.raw['cosmos']['bm_config_id'], history=True), config, 'history')
        samples = page['samples']
    clock = reader.samples[-1] if reader.samples else {}
    result['clock'] = clock
    if not reader.clock_valid():
        result.update(exit_code=6, timezone_check='时钟样本未核验')
    elif not samples:
        result.update(timezone_check='页面时区未验证', exit_code=3)
    else:
        sample = min(samples, key=lambda x: x['duration_s'])
        error = sample['start_time'] + sample['duration_s'] - clock['server_time']
        result.update(timezone_error_s=error, timezone_check='通过' if abs(error) <= 120 else '时区或页面口径不对')
        if abs(error) > 120:
            result.update(exit_code=3, todo='页面时区或时间口径需要核对')
    return result
