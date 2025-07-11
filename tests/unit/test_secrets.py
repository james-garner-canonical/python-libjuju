# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

import os
import tempfile
import unittest
from pathlib import Path

import pytest

from juju.secrets import create_secret_data, read_secret_data


class TestCreateSecretData:
    @pytest.mark.parametrize(
        "keyval", ["foo", "=bar", "baz=", "f=bar", "ff=bar", "foo_bar=baz"]
    )
    def test_bad_key(self, keyval: str):
        with pytest.raises(ValueError):
            create_secret_data([keyval])

    @pytest.mark.parametrize(
        "keyval,expected_key,expected_val",
        [
            ("foo=bar", "foo", "YmFy"),
            ("hello=world", "hello", "d29ybGQ="),
            ("goodbye#base64=world", "goodbye", "world"),
            ("equalsign==", "equalsign", "PQ=="),
            ("equalsign#base64=PQ==", "equalsign", "PQ=="),
            ("pq-identity-theorem=P===Q", "pq-identity-theorem", "UD09PVE="),
        ],
    )
    def test_goo_key_values(self, keyval: str, expected_key: str, expected_val: str):
        actual = create_secret_data([keyval])
        expected = {expected_key: expected_val}
        assert actual == expected

    def test_key_content_too_large(self):
        with pytest.raises(ValueError):
            create_secret_data(["foo=" + ("a" * 8 * 1024)])

    def test_total_content_too_large(self):
        content = "a" * 4 * 1024
        args = [f"key{i}={content}" for i in range(20)]
        with pytest.raises(ValueError):
            create_secret_data(args)

    def test_secret_key_from_file(self):
        content = """
          -----BEGIN CERTIFICATE-----
          MIIFYjCCA0qgAwIBAgIQKaPND9YggIG6+jOcgmpk3DANBgkqhkiG9w0BAQsFADAz
          MRwwGgYDVQQKExNsaW51eGNvbnRhaW5lcnMub3JnMRMwEQYDVQQDDAp0aW1AZWx3
          -----END CERTIFICATE-----"""[1:]

        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            file_path = dir_path / "secret-data.bin"

            with open(file_path, "w") as file:
                file.write(content)

            data = create_secret_data(["key1=value1", f"key2#file={file_path}"])

            assert data == {
                "key1": "dmFsdWUx",
                "key2": (
                    "ICAgICAgICAgIC0tLS0tQkVHSU4gQ0VSVElGSUNBVEUtLS0tLQogICAgICAgICAgTUlJRllqQ0NBMHFnQXdJQkFnSVFLYVBORDlZZ2dJRzYrak9jZ21wazNEQU5CZ2txaGtpRzl3MEJBUXNGQURBegogICAgICAgICAgTVJ3d0dnWURWUVFLRXhOc2FXNTFlR052Ym5SaGFXNWxjbk11YjNKbk1STXdFUVlEVlFRRERBcDBhVzFBWld4MwogICAgICAgICAgLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQ=="
                ),
            }


class TestReadSecretData(unittest.TestCase):
    def test_yaml_file(self):
        data = """
        hello: world
        goodbye#base64: world
        another-key: !!binary |
          R0lGODlhDAAMAIQAAP//9/X17unp5WZmZgAAAOfn515eXvPz7Y6OjuDg4J+fn5
          OTk6enp56enmlpaWNjY6Ojo4SEhP/++f/++f/++f/++f/++f/++f/++f/++f/+
          +f/++f/++f/++f/++f/++SH+Dk1hZGUgd2l0aCBHSU1QACwAAAAADAAMAAAFLC
          AgjoEwnuNAFOhpEMTRiggcz4BNJHrv/zCFcLiwMWYNG84BwwEeECcgggoBADs=
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "secret.yaml")

            with open(file_path, "w") as file:
                file.write(data)

            attrs = read_secret_data(file_path)
            self.assertDictEqual(
                attrs,
                {
                    "hello": "d29ybGQ=",
                    "goodbye": "world",
                    "another-key": "YiJHSUY4OWFceDBjXHgwMFx4MGNceDAwXHg4NFx4MDBceDAwXHhmZlx4ZmZceGY3XHhmNVx4ZjVceGVlXHhlOVx4ZTlceGU1ZmZmXHgwMFx4MDBceDAwXHhlN1x4ZTdceGU3Xl5eXHhmM1x4ZjNceGVkXHg4ZVx4OGVceDhlXHhlMFx4ZTBceGUwXHg5Zlx4OWZceDlmXHg5M1x4OTNceDkzXHhhN1x4YTdceGE3XHg5ZVx4OWVceDllaWlpY2NjXHhhM1x4YTNceGEzXHg4NFx4ODRceDg0XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5XHhmZlx4ZmVceGY5IVx4ZmVceDBlTWFkZSB3aXRoIEdJTVBceDAwLFx4MDBceDAwXHgwMFx4MDBceDBjXHgwMFx4MGNceDAwXHgwMFx4MDUsICBceDhlXHg4MTBceDllXHhlM0BceDE0XHhlOGlceDEwXHhjNFx4ZDFceDhhXHgwOFx4MWNceGNmXHg4ME0kelx4ZWZceGZmMFx4ODVwXHhiOFx4YjAxZlxyXHgxYlx4Y2VceDAxXHhjM1x4MDFceDFlXHgxMCcgXHg4MlxuXHgwMVx4MDA7Ig==",
                },
            )

    def test_json_file(self):
        data = """
        {
            "hello": "world",
            "goodbye#base64": "world"
        }
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "secret.json")

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(data)

            attrs = read_secret_data(file_path)

            self.assertDictEqual(attrs, {"hello": "d29ybGQ=", "goodbye": "world"})
