# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

import importlib
import re
from pathlib import Path
from typing import Dict, List, TypedDict, cast

import pytest

from juju.client import connection, _definitions


class Versions(TypedDict, total=True):
    versions: List[int]


ClientFacades = Dict[str, Versions]


@pytest.fixture
def project_root(pytestconfig: pytest.Config) -> Path:
    return pytestconfig.rootpath


def test_facade_version_matches_filename(project_root: Path) -> None:
    ignore_names = dir(_definitions)
    for file in (project_root / 'juju' / 'client').glob('_client[0-9]*.py'):
        match = re.search('_client([0-9]+).py', file.name)
        assert match
        version = int(match.group(1))
        module = importlib.import_module(f'juju.client.{file.stem}')
        for cls_name in dir(module):
            if cls_name.startswith('_') or cls_name in ignore_names:
                continue
            assert getattr(module, cls_name).version == version


def test_class_name_matches_facade_name(project_root: Path) -> None:
    ignore_names = dir(_definitions)
    for file in (project_root / 'juju' / 'client').glob('_client[0-9]*.py'):
        module = importlib.import_module(f'juju.client.{file.stem}')
        for cls_name in dir(module):
            if cls_name.startswith('_') or cls_name in ignore_names:
                continue
            assert getattr(module, cls_name).name == cls_name.removesuffix('Facade')


def test_client_facades_matches_generated_code(project_root: Path) -> None:
    client_facades = cast(ClientFacades, connection.client_facades)
    expected_facades = make_client_facades_from_generated_code(project_root)
    assert {
        k: v['versions'] for k, v in client_facades.items()
    } == {
        k: v['versions'] for k, v in expected_facades.items()
    }


def make_client_facades_from_generated_code(project_root: Path) -> ClientFacades:
    """Return a client_facades dictionary from generated code under project_root.
    """
    ignore_names = dir(_definitions)
    excluded_facades = connection.excluded_facades
    facades: Dict[str, List[int]] = {}
    for file in (project_root / 'juju' / 'client').glob('_client[0-9]*.py'):
        module = importlib.import_module(f'juju.client.{file.stem}')
        for cls_name in dir(module):
            if cls_name.startswith('_') or cls_name in ignore_names:
                continue
            cls = getattr(module, cls_name)
            if cls.version in excluded_facades.get(cls.name, []):
                continue
            facades.setdefault(cls.name, []).append(cls.version)
    return {name: {'versions': sorted(facades[name])} for name in sorted(facades)}
