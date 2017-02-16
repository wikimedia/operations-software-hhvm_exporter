#!/usr/bin/python
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

import argparse
import datetime
import logging
import sys
import time

import requests

from prometheus_client import start_http_server, Summary
from prometheus_client.core import (CounterMetricFamily, GaugeMetricFamily,
                                    REGISTRY)

log = logging.getLogger(__name__)


class HHVMCollector(object):
    scrape_duration = Summary(
            'hhvm_scrape_duration_seconds', 'HHVM scrape duration')

    def __init__(self, admin_url):
        self.url = admin_url

    def _fetch_json(self, url):
        try:
            response = requests.get(url, timeout=2)
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError,
                ValueError):
            return None

    @scrape_duration.time()
    def collect(self):
        health_data = self._fetch_json(self.url + '/check-health')
        for metric in self._collect_health(health_data):
            yield metric

        memory_data = self._fetch_json(self.url + '/memory.json')
        for metric in self._collect_memory(memory_data):
            yield metric

        status_data = self._fetch_json(self.url + '/status.json')
        for metric in self._collect_status(status_data):
            yield metric

        up = GaugeMetricFamily('hhvm_up', 'HHVM admin interface is up')
        if not all([status_data, memory_data, health_data]):
            up.add_metric([], 0)
        else:
            up.add_metric([], 1)

        yield up

    def _collect_health(self, data):
        if data is None:
            raise StopIteration()

        metrics = {
           'load': GaugeMetricFamily(
                   'hhvm_load',
                   'Number of threads actively servicing requests'),
           'queued': GaugeMetricFamily(
                   'hhvm_queued', 'Number of queued jobs'),
           'hhbc-roarena-capac': GaugeMetricFamily(
                   'hhvm_hhbc_ro_arena_capacity_bytes',
                   'Read-only arena capacity, used only in RepoAuth mode'),
           'rds': GaugeMetricFamily(
                   'hhvm_rds_used_bytes', 'RDS total bytes usage'),
           'rds-local': GaugeMetricFamily(
                   'hhvm_rds_local_bytes', 'RDS local region bytes usage'),
           'rds-persistent': GaugeMetricFamily(
                   'hhvm_rds_persistent_bytes',
                   'RDS persistent region bytes usage'),
           'units': GaugeMetricFamily(
                   'hhvm_units_total', 'Number of loaded units'),
           'funcs': GaugeMetricFamily(
                   'hhvm_funcs_total', 'Number of functions created'),
        }

        for metric_name in metrics.keys():
            metrics[metric_name].add_metric(
                    [], data.get(metric_name, float('nan')))

        metrics['tc'] = GaugeMetricFamily(
                   'hhvm_tc_used_bytes', 'Translation cache usage',
                   labels=['block'])
        metrics['tc'].add_metric(
                ['main'], data.get('tc-size', float('nan')))
        for block in ('hot', 'prof', 'cold', 'frozen'):
            metrics['tc'].add_metric(
                [block], data.get('tc-{}size'.format(block), float('nan')))

        for metric in metrics.values():
            yield metric

    def _collect_memory(self, data):
        if data is None:
            raise StopIteration()

        metrics = {
           'success': GaugeMetricFamily(
                   'hhvm_memory_success',
                   'HHVM was able to fetch its memory statistics'),
           'vmsize': GaugeMetricFamily(
                   'hhvm_process_memory_size_bytes',
                   'Virtual memory size of HHVM process'),
           'vmdetail': GaugeMetricFamily(
                   'hhvm_process_memory_bytes', 'Virtual memory segment size',
                   labels=['segment']),
           'strings_count': GaugeMetricFamily(
                   'hhvm_memory_strings_count', 'Static strings allocated'),
           'strings_bytes': GaugeMetricFamily(
                   'hhvm_memory_strings_bytes',
                   'Static strings total bytes used'),
        }

        memorym = data.get('Memory', {})
        metrics['success'].add_metric([], data.get('Success', 0))

        statm = memorym.get('Process Stats (bytes)', {})
        metrics['vmsize'].add_metric([], statm.get('VmSize'))
        metrics['vmdetail'].add_metric(['rss'], statm.get('VmRss'))
        metrics['vmdetail'].add_metric(['shared'], statm.get('Shared'))
        metrics['vmdetail'].add_metric(['text'], statm.get('Text(Code)'))
        metrics['vmdetail'].add_metric(['data'], statm.get('Data'))

        stringsm = memorym.get('Breakdown', {}).get('Static Strings')
        if stringsm:
            metrics['strings_count'].add_metric(
                    [], stringsm.get('Details', {}).get('Count', float('nan')))
            metrics['strings_bytes'].add_metric(
                    [], stringsm.get('Bytes', float('nan')))

        for metric in metrics.values():
            yield metric

    def _collect_status(self, data):
        if data is None:
            raise StopIteration()

        metrics = {
           'compiler': GaugeMetricFamily(
                   'hhvm_build_info', 'HHVM build information',
                   labels=['compiler', 'build']),
           'start': CounterMetricFamily(
                   'hhvm_startup', 'HHVM process start time'),
        }

        processm = data.get('status', {}).get('process', {})
        if processm:
            metrics['compiler'].add_metric([
                processm.get('compiler'),
                processm.get('build')], 1)

            hhvm_start = processm.get('start', '')
            hhvm_start_date = datetime.datetime.strptime(
                    hhvm_start, '%a, %d-%b-%Y %H:%M:%S %Z')
            metrics['start'].add_metric(
                    [], float(hhvm_start_date.strftime('%s')))

        for metric in metrics.values():
            yield metric


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--admin-url', metavar='URL', help='HHVM admin url',
                        default='http://localhost:9002')
    parser.add_argument('-l', '--listen', metavar='ADDRESS',
                        help='Listen on this address', default=':9192')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    address, port = args.listen.split(':', 1)

    log.info('Starting hhvm_exporter on %s:%s', address, port)

    REGISTRY.register(HHVMCollector(args.admin_url))
    start_http_server(int(port), addr=address)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())
