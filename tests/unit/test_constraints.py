# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

#
# Test our constraints parser
#
from __future__ import annotations

import unittest

from juju import constraints


class TestConstraints(unittest.TestCase):

    def test_mem_regex(self):
        m = constraints.MEM
        self.assertTrue(m.match("10G"))
        self.assertTrue(m.match("1G"))
        self.assertFalse(m.match("1Gb"))
        self.assertFalse(m.match("a1G"))
        self.assertFalse(m.match("1000"))

    def test_normalize_key(self):
        _ = constraints.normalize_key

        self.assertEqual(_("root-disk"), "root_disk")
        self.assertEqual(_("root-disk  "), "root_disk")
        self.assertEqual(_("  root-disk"), "root_disk")
        self.assertEqual(_("RootDisk"), "root_disk")
        self.assertEqual(_("rootDisk"), "root_disk")

        self.assertRaises(Exception, lambda: _("not-one-of-the-supported-keys"))

    def test_normalize_val(self):
        _ = constraints.normalize_value

        self.assertEqual(_("10G"), 10 * 1024)
        self.assertEqual(_("10M"), 10)
        self.assertEqual(_("10"), 10)
        self.assertEqual(_("foo,bar"), "foo,bar")
        self.assertEqual(_("false"), False)
        self.assertEqual(_("true"), True)
        self.assertEqual(_("FALSE"), False)
        self.assertEqual(_("TRUE"), True)

    def test_normalize_list_val(self):
        _ = constraints.normalize_list_value

        self.assertEqual(_("foo"), ["foo"])
        self.assertEqual(_("foo,bar"), ["foo", "bar"])

    def test_parse_constraints(self):
        _ = constraints.parse

        self.assertEqual(
            _("mem=10G"),
            {"mem": 10 * 1024}
        )

        self.assertEqual(
            _("mem=10G zones=bar,baz tags=tag1 spaces=space1,space2"),
            {"mem": 10 * 1024,
             "zones": ["bar", "baz"],
             "tags": ["tag1"],
             "spaces": ["space1", "space2"]}
        )

        self.assertRaises(Exception, lambda: _("root-disk>16G"))
        self.assertRaises(Exception, lambda: _("root-disk>=16G"))

    def test_parse_storage_constraint(self):
        _ = constraints.parse_storage_constraint

        self.assertEqual(
            _("pool,1M"),
            {"pool": "pool",
             "count": 1,
             "size": 1 * 1024 ** 0}
        )
        self.assertEqual(
            _("pool,"),
            {"pool": "pool",
             "count": 1}
        )
        self.assertEqual(
            _("1M"),
            {"size": 1 * 1024 ** 0,
             "count": 1}
        )
        self.assertEqual(
            _("p,1G"),
            {"pool": "p",
             "count": 1,
             "size": 1 * 1024 ** 1}
        )
        self.assertEqual(
            _("p,0.5T"),
            {"pool": "p",
             "count": 1,
             "size": 512 * 1024 ** 1}
        )
        self.assertEqual(
            _("3,0.5T"),
            {"count": 3,
             "size": 512 * 1024 ** 1}
        )
        self.assertEqual(
            _("0.5T,3"),
            {"count": 3,
             "size": 512 * 1024 ** 1}
        )

    def test_parse_storage_constraints(self):
        """Test that various valid storage constraints are parsed as expected."""
        storage_arg_pairs: list[
            tuple[dict[str, str], dict[str, constraints.StorageConstraintDict]]
        ] = [
            # (storage_arg, parsed_storage_arg)
            (
                {"some-label": "ebs,100G,1"},
                {"some-label": {"count": 1, "pool": "ebs", "size": 102400}},
            ),
            (
                {"some-label": "ebs,2.1G,3"},
                {"some-label": {"count": 3, "pool": "ebs", "size": 2150}},
            ),
            (
                {"some-label": "ebs,100G"},
                {"some-label": {"count": 1, "pool": "ebs", "size": 102400}},
            ),
            ({"some-label": "ebs,2"}, {"some-label": {"count": 2, "pool": "ebs"}}),
            ({"some-label": "200G,7"}, {"some-label": {"count": 7, "size": 204800}}),
            ({"some-label": "ebs"}, {"some-label": {"count": 1, "pool": "ebs"}}),
            (
                {"some-label": "10YB"},
                {"some-label": {"count": 1, "size": 11529215046068469760}},
            ),
            ({"some-label": "1"}, {"some-label": {"count": 1}}),
            ({"some-label": "-1"}, {"some-label": {"count": 1}}),
            ({"some-label": ""}, {"some-label": {"count": 1}}),
            (
                {
                    "some-label": "2.1G,3",
                    "data": "1MiB,70",
                    "logs": "ebs,-1",
                },
                {
                    "some-label": {"count": 3, "size": 2150},
                    "data": {"count": 70, "size": 1},
                    "logs": {"count": 1, "pool": "ebs"},
                },
            ),
        ]
        for storage_arg, parsed_storage_constraint in storage_arg_pairs:
            self.assertEqual(
                constraints.parse_storage_constraints(storage_arg),
                parsed_storage_constraint,
            )
            self.assertEqual(
                constraints.parse_storage_constraints(parsed_storage_constraint),
                parsed_storage_constraint,
            )

    def test_parse_device_constraint(self):
        _ = constraints.parse_device_constraint

        self.assertEqual(
            _("nvidia.com/gpu"),
            {"type": "nvidia.com/gpu",
             "count": 1}
        )
        self.assertEqual(
            _("2,nvidia.com/gpu"),
            {"type": "nvidia.com/gpu",
             "count": 2}
        )
        self.assertEqual(
            _("3,nvidia.com/gpu,gpu=nvidia-tesla-p100"),
            {"type": "nvidia.com/gpu",
             "count": 3,
             "attributes": {
                 "gpu": "nvidia-tesla-p100"
             }}
        )
        self.assertEqual(
            _("3,nvidia.com/gpu,gpu=nvidia-tesla-p100;2ndattr=another-attr"),
            {"type": "nvidia.com/gpu",
             "count": 3,
             "attributes": {
                 "gpu": "nvidia-tesla-p100",
                 "2ndattr": "another-attr"
             }}
        )
