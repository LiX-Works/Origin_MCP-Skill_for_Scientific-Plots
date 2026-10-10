"""Development bridge: spawn one owned Origin, never attach to an existing one.

Uses the candidate MCP source and a run-specific authenticated localhost bridge.
No Origin add-on installation or user/global configuration changes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import time
from pathlib import Path


def processes():
    query = ('Get-CimInstance Win32_Process -Filter "Name LIKE \'Origin%\'" '
             '| Select-Object ProcessId,CreationDate,ExecutablePath | ConvertTo-Json -Compress')
    raw = subprocess.check_output(['powershell', '-NoProfile', '-Command', query], text=True).strip()
    data = json.loads(raw) if raw else []
    return data if isinstance(data, list) else [data]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')


def observe(op, graph_name):
    """Fixed read-only development probe; unavailable properties stay explicit."""
    def read(func):
        try:
            value = func()
            if isinstance(value, float) and not math.isfinite(value):
                return {'unavailable': 'nonfinite'}
            return value if isinstance(value, (str, int, float, bool, list, dict, type(None))) else str(value)
        except Exception as exc:
            return {'unavailable': type(exc).__name__ + ': ' + str(exc)}
    graph = op.find_graph(graph_name)
    result = {'graph': graph_name, 'page': {key: read(lambda key=key: graph.get_float(key))
                  for key in ('width', 'height', 'resx', 'resy')}}
    layers = []
    for layer in graph:
        plots = []
        for plot in layer.plot_list():
            plots.append({'lt_range': read(plot.lt_range), 'native_GetRange': read(plot.obj.GetRange),
                          'data_string': read(lambda: plot.get_str('data')),
                          'xdata_string': read(lambda: plot.get_str('xdata')),
                          'ydata_string': read(lambda: plot.get_str('ydata'))})
        layers.append({'properties': {key: read(lambda key=key: layer.get_float(key)) for key in
                       ('left', 'top', 'width', 'height', 'unit', 'x.label.pt', 'y.label.pt',
                        'x.label.font', 'y.label.font')},
                       'title_labels': {name: {key: read(lambda name=name, key=key:
                                            layer.label(name).get_float(key)) for key in ('fsize', 'font')}
                                        for name in ('xb', 'yl')},
                       'legend_size': read(lambda: layer.label('legend').get_float('fsize')),
                       'plots': plots})
    result['layers'] = layers
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    if not args.run_dir.is_absolute() or not run.is_dir() or any(run.iterdir()):
        raise ValueError('Use an existing empty absolute run directory')
    before = processes()
    if before:
        raise RuntimeError('Origin is already running; this developer launcher refuses an ambiguous session')
    source = Path(__file__).resolve().parents[1] / 'mcp' / 'src'
    private = run / 'private'
    private.mkdir()
    os.environ.update({'PYTHONPATH': str(source), 'ORIGIN_MCP_BRIDGE_HANDSHAKE': str(private / 'bridge.json'),
                       'ORIGIN_MCP_LOG_FILE': str(run / 'bridge.jsonl'),
                       'ORIGIN_MCP_ALLOWED_ROOTS': str(run), 'ORIGIN_MCP_KEEP_EXTERNAL': '1'})
    from origin_mcp.origin_client import OriginClient
    from origin_mcp.bridge import OriginEmbeddedBridgeServer
    from origin_mcp.bridge_handshake import generate_token, generate_generation, write_handshake, clear_handshake
    import origin_mcp
    if not Path(origin_mcp.__file__).resolve().is_relative_to(source.resolve()):
        raise RuntimeError('Launcher did not load the isolated candidate MCP source')
    client = OriginClient()
    connected = client.connect(show=False)  # external OriginExt.Application(), never ApplicationSI/attach
    import originpro.config as config
    if not config.oext:
        raise RuntimeError('Expected an external owned Origin runtime')
    new = processes()
    if len(new) != 1:
        raise RuntimeError('Cannot establish unique owned Origin PID; no project will be modified')
    owner = new[0]
    dump(run / 'ownership.json', {'before': before, 'target': owner, 'connection': connected,
                                 'backend': 'external Python / candidate MCP / serial bridge',
                                 'mcp_source': str(Path(origin_mcp.__file__).resolve())})
    generation = generate_generation()

    class SerialServer(OriginEmbeddedBridgeServer):
        def _pump_cooperative_tasks(self):
            super()._pump_cooperative_tasks()
            request = run / 'probe.request.json'
            if request.is_file():
                payload = json.loads(request.read_text(encoding='utf8'))
                output = run / payload['output']
                if output.parent != run or output.exists():
                    raise ValueError('Probe output must be a new file in this run')
                dump(output, observe(client.op, payload['graph']))
                request.unlink()

    with SerialServer(('127.0.0.1', 0), client=client, token=generate_token(), generation=generation,
                      lease_id=generation, origin_pid=owner['ProcessId']) as server:
        write_handshake('127.0.0.1', server.server_address[1], server.token, generation=generation,
                        lease_id=generation, origin_pid=owner['ProcessId'])
        print('OWNED_ORIGIN_READY pid=' + str(owner['ProcessId']), flush=True)
        try:
            server.serve_forever(poll_interval=.1)
        finally:
            clear_handshake()
            dump(run / 'launcher_stopped.json', {'at': time.time(), 'remaining_origin': processes()})
            print('OWNED_BRIDGE_STOPPED', flush=True)


if __name__ == '__main__':
    main()
