# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

import importlib
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, TypedDict, cast

import pytest

from juju.client import connection, _definitions


class Versions(TypedDict, total=True):
    versions: List[int]


ClientFacades = Dict[str, Versions]


@pytest.fixture
def project_root(pytestconfig: pytest.Config) -> Path:
    return pytestconfig.rootpath


def test_client_facades(project_root: Path) -> None:
    client_facades = cast(ClientFacades, connection.client_facades)
    good_facades = make_client_facades_from_generated_code(project_root)
    assert {
        k: v['versions'] for k, v in client_facades.items()
    } == {
        k: v['versions'] for k, v in good_facades.items()
    }


def make_client_facades_from_generated_code(project_root: Path) -> ClientFacades:
    """Return a client_facades dictionary from generated code under project_root.
    """
    files_by_version: List[Tuple[int, Path]] = []
    # [(facade_version, Path), ...]
    for file in (project_root / 'juju' / 'client').glob('_client[0-9]*.py'):
        files_by_version.append((_version_from_filename(file), file))
    files_by_version.sort()

    # _clientN.py files import * from _definitions
    # so we will ignore any names from there
    ignore = dir(_definitions)

    facades_by_version: Dict[int, Set[str]] = {}
    # {facade_version: {facade_name, ...}, ...}
    for version, file in files_by_version:
        module = importlib.import_module(f'juju.client.{file.stem}')
        facades = {
            name.removesuffix("Facade")
            for name in dir(module)
            if not (name.startswith('_') or name in ignore)
        }
        facades_by_version[version] = facades

    # client_facades in connection.py is sorted
    # so we sort facade names before constructing it
    first, *rest = facades_by_version.values()
    sorted_facade_names: list[str] = sorted(first.union(*rest))

    client_facades: ClientFacades = {}
    # {facade_name: {'versions': [1, 2, 3, ...]}, ...}
    for name in sorted_facade_names:
        versions: List[int] = []
        for version, facades in facades_by_version.items():
            if name in facades:
                versions.append(version)
        client_facades[name] = {'versions': versions}
    return client_facades


def _version_from_filename(path: Path) -> int:
    match = re.search('_client([0-9]+).py', path.name)
    assert match
    return int(match.group(1))
