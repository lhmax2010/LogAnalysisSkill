#!/usr/bin/env python3
"""Install the approved property map or import local browser settings."""
import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vd_cosmos_core.config_update import update_submit
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import load_json
from vd_cosmos_core.submit_config import property_map_defaults


BROWSER_KEYS = {'auth_paths', 'static_paths', 'target_config', 'target_config_id', 'account'}


def browser_updates(path):
    data = load_json(path)
    if not isinstance(data, dict) or data.keys() - BROWSER_KEYS:
        raise FlowError(2, 'invalid_browser_input_keys')
    for key in data.keys() & {'target_config', 'target_config_id', 'account'}:
        value = data[key]
        if not isinstance(value, str) or not value or value != value.strip() or re.search(r'[\x00-\x1f\x7f]', value):
            raise FlowError(2, 'invalid_browser_input_value')
        if key == 'target_config_id' and not re.fullmatch(r'[0-9]+', value):
            raise FlowError(2, 'invalid_browser_input_value')
        if key == 'target_config' and any(not part.strip() or part != part.strip() or part in {'.','..'}
                                          for part in value.split('/')):
            raise FlowError(2, 'invalid_browser_input_value')
    return data


def apply(path, browser_input=None):
    def plan(config, submit):
        if config.raw['submit']['property_map_confirmed']:
            raise FlowError(4, 'property_map_already_confirmed')
        if config.raw['submit']['gate_patterns_confirmed']:
            raise FlowError(4, 'gate_patterns_already_confirmed')
        if browser_input is None:
            old = submit.get('property_map', {})
            new = property_map_defaults()
            updates = {'property_map': new}
        else:
            new = browser_updates(browser_input)
            old = submit
            updates = {key: value for key, value in new.items() if key not in old or old[key] != value}
        changes = {'added': sorted(new.keys() - old.keys()),
                   'changed': sorted(k for k in new.keys() & old.keys() if new[k] != old[k])}
        return (updates if any(changes.values()) else {}), changes

    return update_submit(path, plan)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise FlowError(2, 'config_path_required')


def main():
    parser = Parser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--browser-input', type=Path)
    try:
        args = parser.parse_args()
        section = 'submit' if args.browser_input is not None else 'submit.property_map'
        print(json.dumps({'ok': True, section: apply(args.config, args.browser_input)}))
        return 0
    except (OSError, ValueError):
        result = FlowError(6, 'config_update_failed')
    except FlowError as error:
        result = error
    print(json.dumps({'ok': False, 'error': result.reason, 'exit_code': result.code}))
    return result.code


if __name__ == '__main__':
    raise SystemExit(main())
