# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

import importlib
import re
import warnings
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Set, Tuple, TypedDict, cast

import pytest

from juju.client import connection


class Versions(TypedDict, total=True):
    versions: List[int]


ClientFacades = Dict[str, Versions]


@pytest.fixture
def project_root(request: pytest.FixtureRequest):
    return request.config.rootpath


class TestFacades:
    def test_client_facades(self, project_root: Path) -> None:
        good_facades = self.generate_client_facades(project_root)
        client_facades = cast(ClientFacades, connection.client_facades)

        errors: List[Tuple[str, Optional[List[int]], Optional[List[int]]]] = []
        all_names = sorted(set(connection.client_facades).union(good_facades))
        for name in all_names:
            expected = self._versions_from_facades(good_facades, name)
            actual = self._versions_from_facades(client_facades, name)
            if expected != actual:
                errors.append((name, expected, actual))

        if errors:
            print('The following errors were found in connection.client_facades:')
        for name, expected, actual in errors:
            expected_msg = (
                f'should be {expected},'
                if expected is not None
                else 'should not be present,'
            )
            actual_msg = (
                f'not {actual}'
                if actual is not None
                else 'but is not present'
            )
            print(f'    {name!r} {expected_msg} {actual_msg}')

        assert not errors

    @classmethod
    def generate_client_facades(cls, project_root: Path) -> ClientFacades:
        """Return a client_facades dictionary from generated code under project_root.
        """
        files_by_version: List[Tuple[int, Path]] = []
        # [(facade_version, Path), ...]
        for file in (project_root / 'juju' / 'client').glob('_client[0-9]*.py'):
            files_by_version.append((cls._version_from_filename(file), file))
        files_by_version.sort()

        # _clientN.py files import * from _definitions
        # so we will ignore any names from there
        ignore = dir(importlib.import_module('juju.client._definitions'))

        facades_by_version: Dict[int, Set[str]] = {}
        # {facade_version: {facade_name, ...}, ...}
        for version, file in files_by_version:
            module = cls._try_import(f'juju.client.{file.stem}')
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

    @staticmethod
    def _try_import(module_name: str) -> ModuleType | None:
        try:
            return importlib.import_module(module_name)
        except NameError as e:
            warnings.warn(f'error on importing {module_name}:\n{type(e).__name__}: {e}')
            return None

    @staticmethod
    def _version_from_filename(path: Path) -> int:
        match = re.search('_client([0-9]+).py', path.name)
        assert match
        return int(match.group(1))

    @staticmethod
    def _versions_from_facades(facades: ClientFacades, name: str) -> Optional[List[int]]:
        if name not in facades:
            return None
        return facades[name]['versions']
