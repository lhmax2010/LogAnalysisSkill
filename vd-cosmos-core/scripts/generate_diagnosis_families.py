#!/usr/bin/env python3
"""FatTank-only generator. Run from a controlling terminal on the build host."""
import argparse
from pathlib import Path
import os
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vd_cosmos_core.config import load_config
from vd_cosmos_core.diagnosis import MANDATORY_FAMILIES, PEEK_FAMILIES, PEEK_OVERRIDES, seed_tiers, validate_family
from vd_cosmos_core.errors import FlowError
from vd_cosmos_core.files import atomic_write, json_bytes
from vd_cosmos_core.submit_terminal import ancestors_allowed


def run(root, command):
    return subprocess.run(['sudo', 'chroot', str(root), *command], check=True,
                          text=True, stdout=subprocess.PIPE, timeout=90).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--gbs-root', required=True, type=Path)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        ancestors_allowed()
        if not os.isatty(sys.stdin.fileno()):
            raise FlowError(2, 'terminal_required')
        config = load_config(args.config)
        target = config.output(args.output)
        if target.exists():
            raise FlowError(4, 'diagnosis_family_output_exists')
        root = args.gbs_root.resolve(strict=True)
        if root == Path('/') or not root.is_dir():
            raise FlowError(2, 'invalid_gbs_root')
        release = run(root, ['/usr/bin/rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}\n', 'clang']).strip()
        tiers = seed_tiers()
        for tier, families in (('mandatory', MANDATORY_FAMILIES), ('peek', PEEK_FAMILIES)):
            for family in sorted(families):
                tree = run(root, ['/usr/bin/diagtool', 'tree', family])
                flags = set(re.findall(r'(?<![\w-])-W[A-Za-z0-9][A-Za-z0-9_-]*', tree))
                if family not in flags:
                    raise FlowError(5, 'diagtool_tree_unrecognized')
                tiers[tier].update(flags)
        tiers['mandatory'].difference_update(tiers['peek'] & PEEK_OVERRIDES)
        tiers['peek'].difference_update(tiers['mandatory'])
        result = validate_family({'schema_version': 1, 'clang_release': release,
                                  'tiers': {k: sorted(v) for k, v in tiers.items()}})
        atomic_write(config.data_root, target, json_bytes(result))
        print(target)
    except FlowError as error:
        print(error.reason, file=sys.stderr)
        return error.code
    except (OSError, subprocess.SubprocessError, UnicodeError):
        print('diagnosis_family_generation_failed', file=sys.stderr)
        return 5
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
