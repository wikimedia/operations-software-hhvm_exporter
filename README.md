# Prometheus exporter for HHVM

Export health and runtime metrics from HHVM admin interface into
[Prometheus](https://prometheus.io) metrics.

## Running

The easiest way to run `hhvm_exporter` is via a virtualenv:

```
virtualenv .venv
.venv/bin/python setup.py develop
.venv/bin/hhvm_exporter
```

By default metrics are polled from `http://localhost:9002` and exposed on TCP port `9406`:

```
curl localhost:9406/metrics -s | grep -v '^#'
hhvm_load 0.0
hhvm_memory_strings_bytes 13641543.0
hhvm_process_memory_bytes{segment="rss"} 443691008.0
hhvm_process_memory_bytes{segment="shared"} 101527552.0
...
hhvm_startup 1477007598.0
hhvm_up 1.0
hhvm_scrape_duration_seconds_count 14.0
hhvm_scrape_duration_seconds_sum 0.0016635158681310713
```
