"""Bounded S3 developer fixtures in one explicitly owned candidate Origin.

Use launch_isolated.py first, then build -> review both PNGs ->
finalize --visual-reviewed -> close. Resume never executes a FigureSpec again.
Fixture dimensions and typography are examples, not public defaults.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import re
import sys
from pathlib import Path

from launch_isolated import processes
from origin_client import ExpectedSheet, connect
from run_xy_smoke import owned_environment, write_new

CATEGORIES = ('Control', 'Method A', 'Method B', 'Method C')
CATEGORY_VALUES = (1.2, 1.6, 1.4, 1.9)
OBSERVATIONS = (.2, .35, .7, 1.1, 1.25, 1.6, 1.85, 2.1, 2.2, 2.35,
                2.45, 2.6, 2.75, 2.9, 3.1, 3.35, 3.6, 3.85, 4.2, 4.65)
FIXTURES = {
    'CategoryDemo': {'columns': ('category', 'value'), 'rows': tuple(zip(CATEGORIES, CATEGORY_VALUES)),
                     'stem': 'category', 'type': 'column'},
    'HistogramDemo': {'columns': ('obs',), 'rows': tuple((v,) for v in OBSERVATIONS),
                      'stem': 'histogram', 'type': 'histogram'},
}
CATEGORY_ADJUSTMENT = (
    'win -a CategoryDemo; layer -s 1; {range rr=[CategoryDemo]1!1; set rr -q 0;} '
    'label -r Legend; layer.x2.ticks=0; layer.y2.ticks=0; '
    'layer.unit=1; layer.fixed=1; layer.left=18; layer.top=8; layer.width=76; layer.height=70;')
HISTOGRAM_ADJUSTMENT = (
    'win -a HistogramDemo; layer -s 1; set %C -hbb 0; set %C -hbe 5; set %C -hbs 1; '
    'set %C -q 0; label -r Legend; layer.x.label.decPlaces=0; layer.y.label.decPlaces=0; '
    'layer.x2.ticks=0; layer.y2.ticks=0; '
    'layer.unit=1; layer.fixed=1; layer.left=18; layer.top=8; layer.width=76; layer.height=70; '
    'OpenBinWks nRecalculate:=1;')


def fixture_specs(run):
    specs = {}
    for index, (graph, fixture) in enumerate(FIXTURES.items()):
        category = graph == 'CategoryDemo'
        specs[graph] = {
            'figure': {'id': graph},
            'runtime': {'new_project': index == 0, 'show_origin': False},
            'data': [{'id': 'synthetic', 'source': str(run / (fixture['stem'] + '-data.csv')),
                      'roles': {'x': 'category', 'y': 'value'} if category else {'y': 'obs'}}],
            'page': {'layout': 'single', 'size_mm': [90, 65]},
            'layers': [{'id': 'main', 'data_ref': 'synthetic',
                        'x': {'title': 'Method', 'limits': [.5, 4.5], 'step': 1} if category else
                             {'title': 'Observation (a.u.)', 'limits': [0, 5], 'step': 1},
                        'y': {'title': 'Summary value (a.u.)' if category else 'Count',
                              'limits': [0, 2.2] if category else [0, 9],
                              'step': .5 if category else 1}}],
            'plots': [{'id': fixture['stem'], 'layer': 'main', 'type': fixture['type'],
                       'style': {'color': '#2463A6', **({} if category else {'histogram_bin_width': 1})}}],
            'style': {'theme': 'nature', 'font_family': 'Arial', 'axis_title_size': 10,
                      'tick_label_size': 8, 'legend_font_size': 8, 'annotation_font_size': 8},
        }
    return specs


def verify_shared(info):
    """Read actual graph objects; never treat request parameters as readback."""
    if info['layers_count'] != 1 or len(info['layers']) != 1 or info['layers'][0]['plots_count'] != 1:
        raise RuntimeError('Expected exactly one layer and one plot')
    size = info['page_geometry']['physical_size_mm']
    dpi = info['page_geometry']['resolution_dpi']
    for dimension, resolution, wanted in (('width', 'x', 90), ('height', 'y', 65)):
        if dpi[resolution] <= 0 or not math.isclose(size[dimension], wanted, abs_tol=25.4 / dpi[resolution] + 1e-6):
            raise RuntimeError('Actual page dimensions differ from 90 x 65 mm')
    layer = info['layers'][0]
    sizes = {'x_axis_title': 10, 'y_axis_title': 10, 'x_tick_label': 8, 'y_tick_label': 8}
    for name, wanted in sizes.items():
        if layer['typography'][name]['size'] != wanted:
            raise RuntimeError('Actual typography differs: ' + name)
    fonts = {layer['typography'][name]['font_id'] for name in sizes}
    if None in fonts or len(fonts) != 1:
        raise RuntimeError('Title and tick fonts are inconsistent or unreadable')
    return {'page_size_verified': True, 'typography_verified': True,
            'font_id': next(iter(fonts)), 'font_family_name': 'not resolved by inspector'}


def verify_category(info, ref):
    """Require native XY binding, then the actual categorical tick source."""
    plot = info['layers'][0]['plots'][0]
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    binding = plot.get('data_binding', {})
    pending = []
    if plot.get('native_type_id') is None:
        pending.append('actual column native type')
    elif plot['native_type_id'] != 203:
        raise RuntimeError('Expected native column plot ID 203')
    if binding.get('status') != 'available':
        pending.append('actual category binding')
    elif (binding.get('kind') != 'xy' or binding.get('worksheet') != worksheet
          or (binding.get('x') or {}).get('column') != 'A'
          or (binding.get('y') or {}).get('column') != 'B'
          or binding.get('row_range') != [1, len(CATEGORIES)]):
        raise RuntimeError('Category plot does not bind all four source A/B rows')
    tick = info['layers'][0]['axes']['x'].get('tick_label', {})
    if tick.get('status') != 'available':
        pending.append('actual category tick source')
    elif tick.get('type_code') != 2:
        # A categorical type code alone does not reveal a custom category order.
        pending.append('actual displayed category order')
    else:
        parsed = re.fullmatch(r'(\[[^\]\r\n]+\][^!\r\n]+)!([A-Z]+)(?:"[^"\r\n]*")?', tick.get('dataset') or '')
        if not parsed or parsed.groups() != (worksheet, 'A'):
            raise RuntimeError('Category tick text does not read the original ordered A column')
    return {'verified': not pending, 'pending': pending, 'binding_verified': binding.get('status') == 'available',
            'tick_label_readback': tick, 'worksheet_expected': worksheet,
            'category_order_data_verified': not pending, 'rendered_label_order': 'requires visual review'}


def verify_histogram(info, ref, bins=None):
    """Bin anchors/counts must come from Origin, not the requested X limits."""
    plot = info['layers'][0]['plots'][0]
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    pending = []
    native_type = plot.get('native_type_id')
    if native_type is None:
        pending.append('actual histogram native type')
    elif native_type != 219:
        raise RuntimeError('Expected native histogram plot ID 219')
    binding = plot.get('data_binding', {})
    if binding.get('status') != 'available':
        pending.append('actual raw source binding')
    elif (binding.get('kind') != 'observations' or binding.get('worksheet') != worksheet
          or (binding.get('observations') or {}).get('column') != 'A'
          or binding.get('row_range') != [1, len(OBSERVATIONS)]):
        raise RuntimeError('Histogram does not bind all twenty raw observations')
    histogram = plot.get('histogram', {})
    for field, wanted in (('bin_width', 1), ('begin', 0), ('end', 5)):
        if histogram.get(field) is None:
            pending.append('actual histogram ' + field)
        elif not math.isclose(histogram[field], wanted, abs_tol=1e-9):
            raise RuntimeError('Actual histogram ' + field + ' differs from explicit fixture setting')
    counts_verified = None
    if bins is None:
        pending.append('actual native bin table')
    elif not any(name.startswith('actual histogram ') for name in pending):
        counts_verified = verify_bins(histogram, bins)
    return {'verified': not pending, 'pending': pending, 'binding_verified': binding.get('status') == 'available',
            'bin_settings_readback': histogram, 'worksheet_expected': worksheet,
            'counts': counts_verified, 'mode_metadata_verified': False,
            'mode_metadata_status': histogram.get('normalization_status', 'unavailable'),
            'scope': 'raw values and native bin count table verified; count bar heights require visual review'}


def verify_bins(histogram, bins):
    """Recompute counts using actual readback anchors, then check every native row."""
    begin, end, width = (histogram[name] for name in ('begin', 'end', 'bin_width'))
    number = (end - begin) / width
    if number <= 0 or not math.isclose(number, round(number), abs_tol=1e-9):
        raise RuntimeError('Actual histogram bounds do not define complete equal-width bins')
    count = int(round(number))
    anchors = [begin + width * i for i in range(count + 1)]
    counts = [sum(left <= value < right for value in OBSERVATIONS)
              for left, right in zip(anchors, anchors[1:])]
    if sum(counts) != len(OBSERVATIONS):
        raise RuntimeError('Actual histogram bins omit raw observations')
    cumulative, expected_rows = 0, []
    for index, frequency in enumerate(counts):
        cumulative += frequency
        expected_rows.append((anchors[index] + width / 2, frequency, cumulative,
                              cumulative * 100 / len(OBSERVATIONS)))
    ref = bins['worksheet']
    columns = tuple(bins['columns'])
    if len(columns) != 4:
        raise RuntimeError('Native bin table must expose exactly four positional columns')
    ExpectedSheet(ref['book_name'], ref['sheet_name'], columns, tuple(expected_rows),
                  abs_tol=1e-9).check_window(bins, 0, count)
    return {'verified': True, 'anchors': anchors, 'centers': [row[0] for row in expected_rows],
            'counts': counts, 'sum': sum(counts), 'boundary_convention': 'lower_inclusive_upper_exclusive',
            'source': 'actual bin parameters plus full native bin worksheet readback',
            'position_to_origin_columns': list(zip(('center', 'count', 'cumulative_count', 'cumulative_percent'), columns))}


def verify_graph(graph, info, ref, bins=None):
    result = verify_shared(info)
    layer = info['layers'][0]
    wanted_axes = {'x': [.5, 4.5, 1], 'y': [0, 2.2, .5]} if graph == 'CategoryDemo' else {
        'x': [0, 5, 1], 'y': [0, 9, 1]}
    for axis, wanted in wanted_axes.items():
        actual = layer['axes'][axis]
        if actual['scale_name'] != 'linear' or len(actual['limits']) != 3 or any(
                not math.isclose(a, b, abs_tol=1e-9) for a, b in zip(actual['limits'], wanted)):
            raise RuntimeError('Actual axis settings differ: ' + graph + '/' + axis)
    result['axis_settings_verified'] = True
    result['family'] = verify_category(info, ref) if graph == 'CategoryDemo' else verify_histogram(info, ref, bins)
    return result


def load_execution(run):
    execution = json.loads((run / 'execution.json').read_text(encoding='utf8'))
    if set(execution.get('figures', {})) != set(FIXTURES) or execution.get('executed') is not True:
        raise RuntimeError('No completed two-figure execution to inspect; plotting cannot be replayed')
    for graph, item in execution['figures'].items():
        if item.get('executed') is not True or item['graph']['graph_name'] != graph:
            raise RuntimeError('Unexpected recorded fixture identity')
    return execution


async def inspect(client, execution, adjustment=None):
    expected, mappings, worksheets = [], {}, {}
    for graph, fixture in FIXTURES.items():
        ref = execution['figures'][graph]['worksheet']
        metadata = await client.call('origin_get_worksheet_info', {'book_name': ref['book_name'],
                                                                  'sheet_name': ref['sheet_name']})
        columns = tuple(metadata['columns'])
        if len(columns) != len(fixture['columns']):
            raise RuntimeError('Imported worksheet column count changed: ' + graph)
        mappings[graph] = list(zip(fixture['columns'], columns))
        worksheets[graph] = metadata
        expected.append(ExpectedSheet(ref['book_name'], ref['sheet_name'], columns, fixture['rows']))
    data = await client.wait_and_verify(expected, graphs=list(FIXTURES), interval=.25)
    bins = None
    if adjustment is not None:
        ref = adjustment['bin_worksheet']
        bins = await client.call('origin_read_worksheet', {'book_name': ref['book_name'],
                                 'sheet_name': ref['sheet_name'], 'columns': [0, 1, 2, 3],
                                 'start_row': 0, 'max_rows': 1000})
        if any(bins.get('worksheet', {}).get(key) != ref[key] for key in ('book_name', 'sheet_name')):
            raise RuntimeError('Native bin worksheet identity differs from the recorded action')
    infos, verified = {}, {}
    for graph in FIXTURES:
        infos[graph] = await client.call('origin_get_graph_info', {'graph_name': graph})
        verified[graph] = verify_graph(graph, infos[graph], execution['figures'][graph]['worksheet'], bins)
    return {'verification': data, 'source_to_origin_columns': mappings,
            'worksheet_info': worksheets, 'graph_info': infos, 'graphics_verified': verified,
            'native_bin_table': bins}


async def adjust_once(client, run, execution):
    """One recorded fixture adjustment; never rerun this operation on resume."""
    before = await client.call('origin_list_project')
    write_new(run / 'presentation-adjustment-started.json', {'project_before': before,
              'scripts': {'CategoryDemo': CATEGORY_ADJUSTMENT, 'HistogramDemo': HISTOGRAM_ADJUSTMENT}})
    category = await client.call('origin_run_labtalk', {'script': CATEGORY_ADJUSTMENT, 'capture_log': True})
    write_new(run / 'presentation-category-result.json', category)
    if category.get('result') is not True:
        raise RuntimeError('Category presentation adjustment did not execute')
    histogram = await client.call('origin_run_labtalk', {'script': HISTOGRAM_ADJUSTMENT, 'capture_log': True})
    write_new(run / 'presentation-histogram-result.json', histogram)
    if histogram.get('result') is not True:
        raise RuntimeError('Histogram presentation adjustment did not execute')
    after = await client.call('origin_list_project')
    before_books = {book['name']: {sheet['name'] for sheet in book['sheets']} for book in before['workbooks']}
    after_books = {book['name']: {sheet['name'] for sheet in book['sheets']} for book in after['workbooks']}
    source_book = execution['figures']['HistogramDemo']['worksheet']['book_name']
    if (set(before_books) != set(after_books)
            or {g['name'] for g in before['graphs']} != {g['name'] for g in after['graphs']}):
        raise RuntimeError('Unexpected project objects created by native bin worksheet action')
    added = after_books[source_book] - before_books[source_book]
    if len(added) != 1 or any(before_books[book] - after_books[book] or
            (book != source_book and before_books[book] != after_books[book]) for book in before_books):
        raise RuntimeError('Expected exactly one native bin sheet added only inside histogram source book')
    result = {'executed': True, 'category': category, 'histogram': histogram,
              'scripts': {'CategoryDemo': CATEGORY_ADJUSTMENT, 'HistogramDemo': HISTOGRAM_ADJUSTMENT},
              'project_before': before, 'project_after': after,
              'bin_worksheet': {'book_name': source_book, 'sheet_name': next(iter(added))}}
    write_new(run / 'presentation-adjustment.json', result)
    return result


async def export_new(client, run, graph, name, suffix):
    path = run / (name + '.' + suffix)
    if path.exists():
        raise FileExistsError(path)
    result = await client.call('origin_export_graph', {'graph_name': graph, 'path': str(path),
                              'overwrite': False, 'width': 1400 if suffix == 'png' else 0})
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError('Export file was not created: ' + str(path))
    return {**result, 'bytes': path.stat().st_size}


async def run_phase(client, args, run, handshake):
    phase = args.phase
    if phase == 'build':
        specs = fixture_specs(run)
        # Reserve all input names before any Origin writes.
        for graph, fixture in FIXTURES.items():
            for name in (fixture['stem'] + '-data.csv', fixture['stem'] + '-spec.json',
                         'execution-' + graph + '.json'):
                if (run / name).exists():
                    raise FileExistsError('Build inputs already exist; use a fresh run or resume')
        if (run / 'execution.json').exists():
            raise FileExistsError('Completed execution exists; use resume')
        for graph, fixture in FIXTURES.items():
            with (run / (fixture['stem'] + '-data.csv')).open('x', newline='', encoding='utf8') as stream:
                writer = csv.writer(stream)
                writer.writerow(fixture['columns'])
                writer.writerows(fixture['rows'])
            write_new(run / (fixture['stem'] + '-spec.json'), specs[graph])
        figures = {}
        for graph, spec in specs.items():
            plan = await client.call('origin_plan_figure_spec', {'spec': spec})
            if plan.get('executor_executable') is not True:
                raise RuntimeError('Candidate executor cannot run ' + graph)
            result = await client.call('origin_execute_figure_spec', {'spec': spec})
            # Preserve each success even if the next request has an unknown outcome.
            write_new(run / ('execution-' + graph + '.json'), result)
            if result['graph']['graph_name'] != graph:
                raise RuntimeError('Unexpected graph identity')
            figures[graph] = result
        execution = {'executed': True, 'figures': figures}
        write_new(run / 'execution.json', execution)
        adjustment = await adjust_once(client, run, execution)
    elif phase in ('resume', 'finalize'):
        execution = load_execution(run)
        adjustment = json.loads((run / 'presentation-adjustment.json').read_text(encoding='utf8'))
        if adjustment.get('executed') is not True:
            raise RuntimeError('No completed presentation adjustment; resume cannot replay it')
    else:
        if not (run / 'finalize.json').is_file():
            raise RuntimeError('No finalized project; refusing automatic close')
        owned_environment(run)
        result = await client.call('origin_bridge_shutdown', {'release_origin': True, 'close_origin': True, 'timeout': 15})
        if result.get('origin_release_error') or not result.get('origin_release', {}).get('closed'):
            write_new(run / ('close-failed-' + str(args.attempt) + '.json'), result)
            raise RuntimeError('Bridge shutdown did not confirm Origin closure')
        for _ in range(30):
            if not any(p['ProcessId'] == handshake['origin_pid'] for p in processes()):
                break
            await asyncio.sleep(.2)
        else:
            raise RuntimeError('Owned Origin PID remains running after close')
        write_new(run / 'closed.json', {**result, 'owned_process_gone': True})
        print('OWNED_ORIGIN_CLOSED')
        return

    observation = await inspect(client, execution, adjustment)
    if phase == 'finalize':
        if not all(item['family']['verified'] for item in observation['graphics_verified'].values()):
            raise RuntimeError('Family readback remains unverified; cannot finalize')
        saved = await client.save_new(run / 'families-final.opju')
        opened = await client.call('origin_open_project', {'path': str(run / 'families-final.opju'),
                                                         'readonly': False, 'asksave': False})
        if opened.get('opened') is not True:
            raise RuntimeError('Origin did not confirm project reopen')
        observation = await inspect(client, execution, adjustment)
        if not all(item['family']['verified'] for item in observation['graphics_verified'].values()):
            raise RuntimeError('Reopened family readback remains unverified')
        exports = [await export_new(client, run, graph, fixture['stem'] + '-reopened', 'png')
                   for graph, fixture in FIXTURES.items()]
        write_new(run / 'finalize.json', {**observation, 'saved': saved, 'opened': opened,
                  'exports': exports, 'visual_review': {'reviewed': True,
                  'images': [f['stem'] + '-review.png' for f in FIXTURES.values()],
                  'checks': ['four category labels in input order', 'histogram bar heights 3,4,7,4,2',
                             'unclipped axis titles and readable fixture typography']},
                  'presentation_adjustment': adjustment, 'metrics': client.metrics()})
        print('FAMILIES_REOPENED: inspect reopened readback and PNGs before closing')
        return

    # Resume is read/continue validation only: no FigureSpec or presentation replay.
    checkpoint = run / 'checkpoint.opju'
    saved = {'existing': True, 'path': str(checkpoint), 'bytes': checkpoint.stat().st_size} if checkpoint.exists() else await client.save_new(checkpoint)
    if saved['bytes'] <= 0:
        raise RuntimeError('Empty checkpoint')
    exports = []
    for graph, fixture in FIXTURES.items():
        for suffix in ('png', 'pdf'):
            name = fixture['stem'] + '-review'
            path = run / (name + '.' + suffix)
            if path.exists():
                if path.stat().st_size <= 0:
                    raise RuntimeError('Empty existing export')
                exports.append({'existing': True, 'path': str(path), 'bytes': path.stat().st_size})
            else:
                exports.append(await export_new(client, run, graph, name, suffix))
    after = await inspect(client, execution, adjustment)
    report = {**observation, 'after_export': after, 'execution': execution,
              'saved': saved, 'exports': exports, 'presentation_adjustment': adjustment, 'metrics': client.metrics()}
    name = 'build.json' if phase == 'build' or not (run / 'build.json').exists() else 'resume-' + str(args.attempt) + '.json'
    write_new(run / name, report)
    pending = [graph for graph, item in after['graphics_verified'].items() if not item['family']['verified']]
    print('FAMILIES_BUILT: review both PNGs; family readback pending=' + ','.join(pending))


async def main(args):
    run = args.run_dir.resolve()
    if not args.run_dir.is_absolute() or not run.is_dir() or args.attempt < 1:
        raise ValueError('Existing absolute run directory and positive attempt required')
    if args.phase == 'finalize' and not args.visual_reviewed:
        raise ValueError('Review both fixture PNGs first; pass --visual-reviewed after actual inspection')
    if (run / 'unknown-outcome.json').exists():
        raise RuntimeError('Previous RPC outcome unknown; no automatic continuation or retry')
    handshake, env = owned_environment(run)
    log_dir = run / ('client-' + args.phase + '-' + str(args.attempt))
    # owned_environment supplies existing isolation; use this attempt's audit path.
    env['ORIGIN_MCP_LOG_FILE'] = str(run / ('mcp-' + args.phase + '-' + str(args.attempt) + '.jsonl'))
    async with connect(Path(sys.executable), log_dir, env=env) as client:
        try:
            status = await client.call('origin_bridge_status')
            if status.get('origin_pid') != handshake['origin_pid'] or status.get('generation') != handshake['generation']:
                raise RuntimeError('Bridge lifecycle differs from owned handshake')
            await run_phase(client, args, run, handshake)
        except BaseException:
            if client.unknown_outcome and not (run / 'unknown-outcome.json').exists():
                write_new(run / 'unknown-outcome.json', {'phase': args.phase, 'attempt': args.attempt,
                                                       'retry': False, 'metrics': client.metrics()})
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--phase', choices=('build', 'resume', 'finalize', 'close'), default='build')
    parser.add_argument('--visual-reviewed', action='store_true')
    parser.add_argument('--attempt', type=int, default=1, help='Fresh audit directory for an inspected continuation')
    asyncio.run(main(parser.parse_args()))
