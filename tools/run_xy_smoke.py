"""Bounded developer XY example against an explicitly owned candidate bridge.

build -> inspect xy-review.png -> finalize --visual-reviewed -> close.
This is a synthetic development check, not general chart-family certification.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import sys
from pathlib import Path

from launch_isolated import processes
from origin_client import ExpectedSheet, connect

ROWS = tuple((x, round(.2 + .05 * x + .01 * x * x, 8)) for x in range(11))
COLUMNS = ('time_s', 'response')


def verify_graph(info, ref):
    """Check actual readback of this one fixture, not FigureSpec request echoes."""
    if info['layers_count'] != 1 or info['layers'][0]['plots_count'] != 1:
        raise RuntimeError('Expected exactly one layer and one curve')
    size = info['page_geometry']['physical_size_mm']
    dpi = info['page_geometry']['resolution_dpi']
    if not (math.isclose(size['width'], 90, abs_tol=25.4 / dpi['x'] + 1e-6)
            and math.isclose(size['height'], 65, abs_tol=25.4 / dpi['y'] + 1e-6)):
        raise RuntimeError('Actual page dimensions differ from 90 x 65 mm')
    layer = info['layers'][0]
    sizes = {'x_axis_title': 10, 'y_axis_title': 10, 'x_tick_label': 8, 'y_tick_label': 8}
    for name, wanted in sizes.items():
        if layer['typography'][name]['size'] != wanted:
            raise RuntimeError('Actual typography differs: ' + name)
    font_ids = {layer['typography'][name]['font_id'] for name in sizes}
    if None in font_ids or len(font_ids) != 1:
        raise RuntimeError('Actual title and tick fonts are inconsistent or unreadable')
    binding = layer['plots'][0]['data_binding']
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    if (binding['worksheet'] != worksheet or binding['x']['column'] != 'A'
            or binding['y']['column'] != 'B' or binding['row_range'] != [1, 11]):
        raise RuntimeError('Actual curve does not bind the expected worksheet, columns, and all 11 rows')
    for axis, wanted in (('x', [-.35, 10.35, 2]), ('y', [0, 1.8, .3])):
        actual = layer['axes'][axis]
        if actual['scale_name'] != 'linear' or any(not math.isclose(a, b, abs_tol=1e-9)
                                                   for a, b in zip(actual['limits'], wanted)):
            raise RuntimeError('Actual axis settings differ: ' + axis)
    return {'binding_verified': True, 'page_size_verified': True, 'typography_verified': True,
            'axis_settings_verified': True, 'font_id': next(iter(font_ids)),
            'font_family_name': 'not resolved by inspector'}


def write_new(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def owned_environment(run):
    ownership = json.loads((run / 'ownership.json').read_text(encoding='utf8'))
    target = ownership['target']
    matches = [p for p in processes() if p['ProcessId'] == target['ProcessId']
               and p['CreationDate'] == target['CreationDate']]
    if len(matches) != 1:
        raise RuntimeError('Owned Origin identity is no longer current; refusing operation')
    handshake = json.loads((run / 'private' / 'bridge.json').read_text(encoding='utf8'))
    if handshake.get('origin_pid') != target['ProcessId'] or handshake.get('host') != '127.0.0.1':
        raise RuntimeError('Bridge does not identify the owned local Origin')
    source = Path(__file__).resolve().parents[1] / 'mcp' / 'src'
    env = {'PYTHONPATH': str(source), 'ORIGIN_MCP_BRIDGE_HANDSHAKE': str(run / 'private' / 'bridge.json'),
           'ORIGIN_MCP_BRIDGE_HOST': handshake['host'], 'ORIGIN_MCP_BRIDGE_PORT': str(handshake['port']),
           'ORIGIN_MCP_BRIDGE_TOKEN': handshake['token'], 'ORIGIN_MCP_BRIDGE_TIMEOUT': '40',
           'ORIGIN_MCP_ALLOWED_ROOTS': str(run), 'ORIGIN_MCP_LOG_FILE': str(run / 'mcp-tools.jsonl')}
    return handshake, env


async def main(args):
    run = args.run_dir.resolve()
    if not args.run_dir.is_absolute() or not run.is_dir():
        raise ValueError('An existing absolute run directory is required')
    handshake, env = owned_environment(run)
    phase = args.phase
    if phase == 'finalize' and not args.visual_reviewed:
        raise ValueError('Review xy-review.png first; pass --visual-reviewed only after actual inspection')
    log_name = 'client-' + phase + (('-' + str(args.attempt)) if args.attempt > 1 else '')
    async with connect(Path(sys.executable), run / log_name, env=env) as client:
        status = await client.call('origin_bridge_status')
        if status.get('origin_pid') != handshake['origin_pid'] or status.get('generation') != handshake['generation']:
            raise RuntimeError('Bridge lifecycle differs from the owned handshake')
        if phase in ('build', 'resume'):
            # Resume reads an already recorded successful execution; it never replays plotting.
            if phase == 'resume':
                execution = json.loads((run / 'execution.json').read_text(encoding='utf8'))
                if execution.get('executed') is not True:
                    raise RuntimeError('No completed execution to inspect')
            else:
                execution = None
            outputs = [run / name for name in ('data.csv', 'spec.json', 'xy-review.png', 'xy-review.pdf',
                                                'checkpoint.opju', 'build.json', 'execution.json')]
            if phase == 'resume':
                outputs = [p for p in outputs if p.name not in ('data.csv', 'spec.json', 'execution.json')]
            if any(path.exists() for path in outputs):
                raise FileExistsError('Build outputs already exist; create a fresh run')
            if phase == 'build':
                with (run / 'data.csv').open('x', newline='', encoding='utf8') as stream:
                    writer = csv.writer(stream)
                    writer.writerow(COLUMNS)
                    writer.writerows(ROWS)
            spec = {
                'figure': {'id': 'XYDemo'},
                'runtime': {'new_project': True, 'show_origin': False},
                'data': [{'id': 'synthetic', 'source': str(run / 'data.csv'), 'roles': {'x': 'time_s', 'y': 'response'}}],
                'page': {'layout': 'single', 'size_mm': [90, 65]},
                'layers': [{'id': 'main', 'data_ref': 'synthetic',
                            'x': {'title': 'Time (s)', 'limits': [-.35, 10.35], 'step': 2},
                            'y': {'title': 'Response (a.u.)', 'limits': [0, 1.8], 'step': .3}}],
                'plots': [{'id': 'response', 'layer': 'main', 'type': 'line_symbol',
                           'style': {'color': '#2463A6', 'line_width': 1.2, 'symbol_size': 3}}],
                'style': {'theme': 'nature', 'font_family': 'Arial', 'axis_title_size': 10,
                          'tick_label_size': 8, 'legend_font_size': 8, 'annotation_font_size': 8},
            }
            if phase == 'build':
                write_new(run / 'spec.json', spec)
                plan = await client.call('origin_plan_figure_spec', {'spec': spec})
                if plan.get('executor_executable') is not True:
                    raise RuntimeError('Candidate executor cannot run this example')
                execution = await client.call('origin_execute_figure_spec', {'spec': spec})
                write_new(run / 'execution.json', execution)
            ref = execution['worksheet']
            graph = execution['graph']['graph_name']
            if graph != 'XYDemo':
                raise RuntimeError('Unexpected graph identity for this bounded fixture')
            # Existing low-level tool handles a deliberate, recorded presentation choice.
            # One series needs no legend or automatic numeric endpoint label.
            if (run / 'presentation-adjustment.json').exists():
                adjustment = json.loads((run / 'presentation-adjustment.json').read_text(encoding='utf8'))
            else:
                adjustment = await client.call('origin_run_labtalk', {'script':
                    'win -a XYDemo; layer -s 1; {range rr=[XYDemo]1!1; set rr -q 0;} label -r Legend; '
                    'layer.x.label.decPlaces=0; layer.y.label.decPlaces=1; '
                    'layer.x2.ticks=0; layer.y2.ticks=0;', 'capture_log': True})
                if adjustment.get('result') is True:
                    write_new(run / 'presentation-adjustment.json', adjustment)
            if adjustment.get('result') is not True:
                raise RuntimeError('Explicit presentation adjustment did not execute')
            metadata = await client.call('origin_get_worksheet_info', {'book_name': ref['book_name'],
                                                                      'sheet_name': ref['sheet_name']})
            actual_columns = tuple(metadata['columns'])
            if len(actual_columns) != len(COLUMNS):
                raise RuntimeError('Imported worksheet column count changed')
            expected = ExpectedSheet(ref['book_name'], ref['sheet_name'], actual_columns, ROWS)
            data = await client.wait_and_verify([expected], graphs=[graph], interval=.25)
            info = await client.call('origin_get_graph_info', {'graph_name': graph})
            graphics = verify_graph(info, ref)
            saved = await client.save_new(run / 'checkpoint.opju')
            exports = []
            for suffix in ('png', 'pdf'):
                exports.append(await client.call('origin_export_graph', {
                    'graph_name': graph, 'path': str(run / ('xy-review.' + suffix)),
                    'overwrite': False, 'width': 1400 if suffix == 'png' else 0}))
            write_new(run / 'probe.request.json', {'graph': graph, 'output': 'probe-built.json'})
            await client.call('origin_list_project')
            after_export = await client.call('origin_get_graph_info', {'graph_name': graph})
            verify_graph(after_export, ref)
            write_new(run / 'build.json', {'execution': execution, 'verification': data,
                                          'source_to_origin_columns': list(zip(COLUMNS, actual_columns)),
                                          'worksheet_info': metadata,
                                          'graph_info': info, 'graph_after_export': after_export,
                                          'graphics_verified': graphics, 'presentation_adjustment': adjustment,
                                          'saved': saved, 'exports': exports,
                                          'metrics': client.metrics()})
            print('XY_BUILT: review PNG and actual readback before finalize')
        elif phase == 'finalize':
            build = json.loads((run / 'build.json').read_text(encoding='utf8'))
            graph = build['execution']['graph']['graph_name']
            ref = build['execution']['worksheet']
            columns = tuple(item[1] for item in build['source_to_origin_columns'])
            expected = ExpectedSheet(ref['book_name'], ref['sheet_name'], columns, ROWS)
            saved = await client.save_new(run / 'xy-final.opju')
            opened = await client.call('origin_open_project', {'path': str(run / 'xy-final.opju'),
                                                               'readonly': False, 'asksave': False})
            if opened.get('opened') is not True:
                raise RuntimeError('Origin did not confirm project reopen')
            data = await client.wait_and_verify([expected], graphs=[graph], interval=.25)
            info = await client.call('origin_get_graph_info', {'graph_name': graph})
            graphics = verify_graph(info, ref)
            export = await client.call('origin_export_graph', {'graph_name': graph,
                                      'path': str(run / 'xy-reopened.png'), 'overwrite': False, 'width': 1400})
            write_new(run / 'probe.request.json', {'graph': graph, 'output': 'probe-reopened.json'})
            await client.call('origin_list_project')
            write_new(run / 'finalize.json', {'saved': saved, 'opened': opened, 'verification': data,
                                             'graph_info': info, 'graphics_verified': graphics, 'export': export,
                                             'visual_review': {'reviewed': True, 'image': 'xy-review.png'},
                                             'metrics': client.metrics()})
            print('XY_REOPENED: inspect reopened readback and PNG before closing')
        else:
            if not (run / 'finalize.json').is_file():
                raise RuntimeError('No finalized project; refusing automatic close')
            owned_environment(run)
            result = await client.call('origin_bridge_shutdown', {'release_origin': True, 'close_origin': True,
                                                                    'timeout': 15})
            if result.get('origin_release_error') or not result.get('origin_release', {}).get('closed'):
                write_new(run / 'close-failed.json', result)
                raise RuntimeError('Bridge shutdown did not confirm Origin closure')
            for _ in range(30):
                if not any(p['ProcessId'] == handshake['origin_pid'] for p in processes()):
                    break
                await asyncio.sleep(.2)
            else:
                raise RuntimeError('Owned Origin PID is still running after close request')
            write_new(run / 'closed.json', {**result, 'owned_process_gone': True})
            print('OWNED_ORIGIN_CLOSED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--phase', choices=('build', 'resume', 'finalize', 'close'), default='build')
    parser.add_argument('--visual-reviewed', action='store_true')
    parser.add_argument('--attempt', type=int, default=1, help='Use a fresh audit log after an inspected failure')
    asyncio.run(main(parser.parse_args()))
