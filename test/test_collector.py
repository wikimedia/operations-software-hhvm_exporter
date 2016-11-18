# Copyright 2016 Filippo Giunchedi
#                Wikimedia Foundation
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

from hhvm_exporter.exporter import HHVMCollector


class TestHHVMCollector(unittest.TestCase):
    def setUp(self):
        self.c = HHVMCollector('http://localhost:9090')

    def testCollectStatus(self):
        expected_names = ['hhvm_startup', 'hhvm_build_info']
        self.assertMetricEqual(
            [x.name for x in self.c._collect_status({})], expected_names)

    def testCollectMemory(self):
        expected_names = [
            'hhvm_memory_strings_count', 'hhvm_process_memory_bytes',
            'hhvm_memory_strings_bytes', 'hhvm_memory_success',
            'hhvm_tc_used_bytes', 'hhvm_process_memory_size_bytes']
        self.assertMetricEqual(
            [x.name for x in self.c._collect_memory({})], expected_names)

    def testCollectHealth(self):
        expected_names = [
            'hhvm_funcs_total', 'hhvm_hhbc_ro_arena_capacity_bytes',
            'hhvm_load', 'hhvm_queued', 'hhvm_rds_local_bytes',
            'hhvm_rds_persistent_bytes', 'hhvm_rds_used_bytes',
            'hhvm_tc_used_bytes', 'hhvm_units_total']
        self.assertMetricEqual(
            [x.name for x in self.c._collect_health({})], expected_names)

    def assertMetricEqual(self, actual, expected):
        return self.assertListEqual(sorted(actual), sorted(expected))
