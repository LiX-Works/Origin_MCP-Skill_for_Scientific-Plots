"""One bounded, synthetic 4 x 3 XYZ heatmap in an explicitly owned Origin.

launch_isolated.py -> build -> inspect PNG/PDF -> finalize --visual-reviewed -> close.
Resume only reads/continues recorded execution; it never replays the plot or
presentation action. Fixture dimensions/fonts are deliberate test choices.
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
from run_xy_smoke import owned_environment, write_new

GRAPH = 'HeatmapDemo'
COLUMNS = ('x', 'y', 'z')
ROWS = tuple((x, y, 10 * y + x) for y in range(3) for x in range(4))
CORNERS = {'bottom_left': 0, 'bottom_right': 3, 'top_left': 20, 'top_right': 23}
FRAME = {'left': 16, 'top': 10, 'width': 60, 'height': 56.25}
# Recorded fixture action confirmed by the owned probe; no guessed colorbar fields.
PRESENTATION_SCRIPT = (
    'win -a HeatmapDemo; layer -s 1; layer.unit=1; layer.fixed=1; '
    'layer.left=16; layer.top=10; layer.width=60; layer.height=56.25; '
    'layer.x.label.decPlaces=0; layer.y.label.decPlaces=0; layer.x.label.rotate=0; '
    'layer.x2.ticks=0; layer.y2.ticks=0; '
    'layer.cmap.flippal=1; layer.cmap.updateScale(); '
    'Spectrum1.fsize=10; Spectrum1.font=font(Arial); '
    'Spectrum1.labels.fsize=8; Spectrum1.labels.font=font(Arial); '
    'Spectrum1.labels.autodisp=0; Spectrum1.labels.numdisp=1; Spectrum1.labels.decplaces=0; '
    'Spectrum1.levels.major=3; Spectrum1.levels.from=0; Spectrum1.levels.to=23; '
    'Spectrum1.levels.inc=1; Spectrum1.levels.inc$="5"; '
    'Spectrum1.title=0; Spectrum1.title$="Value (a.u.)"; Spectrum1.revorder=1;')

UNITS_READ_SCRIPT = (
    'win -a HeatmapDemo; layer -s 1; '
    'type -a "SCALE_UNITS=%(ScaleUnits.text$)"; '
    'type -a "SCALE_SIZE=$(ScaleUnits.fsize) FONT=$(ScaleUnits.font) PAL_FLIP=$(layer.cmap.flippal)";')


def verify_units_annotation(result, font_id):
    """Check captured actual annotation properties, not the label creation response."""
    lines = result.get('message_log', {}).get('lines', [])
    if result.get('result') is not True or 'SCALE_UNITS=Value (a.u.)' not in lines:
        raise RuntimeError('Actual units annotation is missing or has incorrect text')
    import re
    values = [re.fullmatch(r'SCALE_SIZE=([\d.]+) FONT=([\d.]+) PAL_FLIP=([\d.]+)', line) for line in lines]
    match = next((value for value in values if value is not None), None)
    if match is None or tuple(map(float, match.groups())) != (9.0, float(font_id), 1.0):
        raise RuntimeError('Actual units label font/size or palette direction differs from the inspected fixture')
    return {'actual_text': 'Value (a.u.)', 'size_pt': 9, 'font_id': font_id,
            'palette_flip': True, 'source': 'captured LabTalk object properties'}


def fixture_spec(run):
    return {
        'figure': {'id': GRAPH},
        'runtime': {'new_project': True, 'show_origin': False},
        'data': [{'id': 'synthetic', 'source': str(run / 'heatmap-data.csv'),
                  'object': 'worksheet', 'roles': dict(zip(COLUMNS, COLUMNS))}],
        'page': {'layout': 'single', 'size_mm': [100, 80]},
        'layers': [{'id': 'main', 'data_ref': 'synthetic',
                    'position_mode': 'absolute', 'position': dict(FRAME),
                    'x': {'title': 'X (a.u.)', 'limits': [-.5, 3.5], 'step': 1},
                    'y': {'title': 'Y (a.u.)', 'limits': [-.5, 2.5], 'step': 1}}],
        'plots': [{'id': 'field', 'layer': 'main', 'type': 'heatmap',
                   'style': {'colormap': 'Viridis.PAL', 'color_scale_limits': [0, 23],
                             'contour_levels': list(range(24))}}],
        'style': {'theme': 'nature', 'font_family': 'Arial', 'axis_title_size': 10,
                  'tick_label_size': 8, 'legend_font_size': 8, 'annotation_font_size': 8},
    }


def verify_matrix(actual, ref):
    """Inspect every native matrix value and XY map, never the conversion request."""
    metadata = actual['matrix']
    if any(metadata.get(key) != ref[key] for key in ('book_name', 'sheet_name')):
        raise RuntimeError('Actual derived matrix identity differs from recorded execution')
    if (metadata.get('shape') != [3, 4] or metadata.get('depth') != 1
            or actual.get('object_index') != 0 or actual.get('start_row') != 0
            or actual.get('start_col') != 0 or actual.get('returned_shape') != [3, 4]):
        raise RuntimeError('Actual derived matrix is not the complete single 3 x 4 object')
    if metadata.get('xymap') != [0, 3, 0, 2]:
        raise RuntimeError('Actual matrix XY mapping differs from the source grid')
    expected = [[10 * y + x for x in range(4)] for y in range(3)]
    values = actual.get('data', [])
    if (len(values) != 3 or any(len(row) != 4 for row in values)
            or any(isinstance(got, bool) or not isinstance(got, (int, float))
                   or not math.isclose(got, wanted, rel_tol=1e-12, abs_tol=0)
                   for row, wanted_row in zip(values, expected)
                   for got, wanted in zip(row, wanted_row))):
        raise RuntimeError('Actual matrix values differ from all twelve source XYZ values')
    return {'verified': True, 'shape': [3, 4], 'all_expected_values_match': True,
            'xymap': metadata['xymap'], 'corners': CORNERS,
            'source': 'origin_read_matrix full window and native matrix metadata'}


def verify_graph(info, ref, matrix_ref=None, matrix_data=None):
    """Fail on actual mismatches; expose unavailable heatmap metadata as pending."""
    if (info['layers_count'] != 1 or len(info['layers']) != 1
            or info['layers'][0]['plots_count'] != 1 or len(info['layers'][0]['plots']) != 1):
        raise RuntimeError('Expected exactly one layer and one heatmap')
    size = info['page_geometry']['physical_size_mm']
    dpi = info['page_geometry']['resolution_dpi']
    for dimension, axis, wanted in (('width', 'x', 100), ('height', 'y', 80)):
        if (dpi[axis] <= 0 or not math.isclose(size[dimension], wanted,
                abs_tol=25.4 / dpi[axis] + 1e-6)):
            raise RuntimeError('Actual page dimensions differ from 100 x 80 mm')
    layer = info['layers'][0]
    sizes = {'x_axis_title': 10, 'y_axis_title': 10, 'x_tick_label': 8, 'y_tick_label': 8}
    for name, wanted in sizes.items():
        if layer['typography'][name]['size'] != wanted:
            raise RuntimeError('Actual typography differs: ' + name)
    fonts = {layer['typography'][name]['font_id'] for name in sizes}
    if None in fonts or len(fonts) != 1:
        raise RuntimeError('Actual axis title and tick fonts are inconsistent or unreadable')
    for axis, wanted in (('x', [-.5, 3.5, 1]), ('y', [-.5, 2.5, 1])):
        actual = layer['axes'][axis]
        if (actual['scale_name'] != 'linear' or len(actual['limits']) != 3
                or any(not math.isclose(a, b, abs_tol=1e-9)
                       for a, b in zip(actual['limits'], wanted))):
            raise RuntimeError('Actual axis settings differ: ' + axis)
    pending = []
    geometry = layer.get('geometry', {})
    if geometry.get('status') != 'available' or geometry.get('unit') == 'unavailable':
        pending.append('actual layer geometry')
    else:
        # Native layer percentages are quantized to page printer dots, then
        # displayed at two decimals. Keep both the percent and physical bounds.
        native_dots = {dimension: (info['page_geometry'].get(dimension)
                                  or size[dimension] * dpi[axis] / 25.4)
                       for dimension, axis in (('width', 'x'), ('height', 'y'))}
        percent_tolerance = {key: 100 / native_dots[dimension] + .005 + 1e-6
                             for key, dimension in (('left', 'width'), ('width', 'width'),
                                                    ('top', 'height'), ('height', 'height'))}
        if geometry.get('unit') != 'percent_of_page' or any(
                geometry.get(key) is None or not math.isclose(geometry[key], value,
                    abs_tol=percent_tolerance[key]) for key, value in FRAME.items()):
            raise RuntimeError('Actual layer geometry differs from the explicit percent frame')
        for dimension, axis, wanted in (('width', 'x', 60), ('height', 'y', 45)):
            physical = geometry[dimension] * size[dimension] / 100
            if not math.isclose(physical, wanted, abs_tol=25.4 / dpi[axis] + 1e-6):
                raise RuntimeError('Actual physical frame differs from 60 x 45 mm')
    plot = layer['plots'][0]
    if plot.get('native_type_id') is None:
        pending.append('actual heatmap native type')
    elif plot['native_type_id'] != 105:
        raise RuntimeError('Expected native cell heatmap plot ID 105')
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    binding = plot.get('data_binding', {})
    if binding.get('status') != 'available':
        pending.append('actual matrix binding')
    elif binding.get('kind') != 'matrix':
        raise RuntimeError('Cell heatmap does not bind a native matrix')
    matrix_verified = None
    if matrix_ref is None or matrix_data is None:
        pending.append('actual derived matrix full values and coordinate map')
    else:
        matrix_verified = verify_matrix(matrix_data, matrix_ref)
        # Exact plot-to-matrix identity is independent of the matrix full read.
        if binding.get('status') == 'available':
            native = binding.get('matrix')
            data_ranges = matrix_data['matrix'].get('data_ranges', [])
            if native is None or len(data_ranges) != 1:
                pending.append('actual plotted matrix object identity')
            elif (native.get('matrix_book') != matrix_ref['book_name']
                  or native.get('sheet') != matrix_ref['sheet_name']
                  or native.get('matrix_sheet') != f"[{matrix_ref['book_name']}]{matrix_ref['sheet_name']}"
                  or native.get('object_index_base') != 1 or native.get('object_index') != 1):
                raise RuntimeError('Heatmap binds a different native matrix object')
    zlevels = plot.get('zlevels', {})
    levels = zlevels.get('levels')
    if levels is None:
        pending.append('actual color levels')
    elif (len(levels) < 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in levels)
          or any(a >= b for a, b in zip(levels, levels[1:]))
          or not math.isclose(levels[0], 0, abs_tol=1e-9)
          or not math.isclose(levels[-1], 23, abs_tol=1e-9)):
        raise RuntimeError('Actual heatmap color levels do not span [0,23] monotonically')
    colormap = plot.get('colormap')
    if colormap is None:
        pending.append('actual colormap')
    elif not isinstance(colormap, str) or colormap.replace('\\', '/').split('/')[-1].lower().removesuffix('.pal') != 'viridis':
        raise RuntimeError('Actual heatmap colormap differs from Viridis')
    color_scale = layer.get('color_scale', {})
    for key, wanted in (('present', True),
                        ('title_visible', False), ('reverse_order', True)):
        if color_scale.get(key) is None:
            pending.append('actual color scale ' + key)
        elif color_scale[key] != wanted:
            raise RuntimeError('Actual color scale differs: ' + key)
    labels = color_scale.get('labels', {})
    for key, wanted in (('size', 8), ('font_id', next(iter(fonts)))):
        if labels.get(key) is None:
            pending.append('actual color scale labels ' + key)
        elif labels[key] != wanted:
            raise RuntimeError('Actual color scale labels differ: ' + key)
    return {'page_size_verified': True, 'typography_verified': True,
            'axis_settings_verified': True, 'font_id': next(iter(fonts)),
            'font_family_name': 'not resolved by inspector',
            'family': {'verified': not pending, 'pending': pending,
                       'binding_verified': binding.get('status') == 'available',
                       'geometry_readback': geometry, 'zlevels_readback': zlevels,
                       'matrix_verified': matrix_verified,
                       'color_scale_limits_verified': levels is not None,
                       'colormap_readback': colormap,
                       'color_scale_readback': color_scale,
                       'worksheet_expected': worksheet,
                       'orientation': {'expected_corners': CORNERS,
                                       'rendered_orientation': 'requires actual visual review'},
                       'scope': 'one regular XYZ fixture reordered into cells without interpolation'}}


def load_execution(run):
    execution = json.loads((run / 'execution.json').read_text(encoding='utf8'))
    if execution.get('executed') is not True or execution['graph']['graph_name'] != GRAPH:
        raise RuntimeError('No completed bounded heatmap execution; plotting cannot be replayed')
    return execution


async def inspect(client, execution):
    ref = execution['worksheet']
    metadata = await client.call('origin_get_worksheet_info', {'book_name': ref['book_name'],
                                                              'sheet_name': ref['sheet_name']})
    columns = tuple(metadata['columns'])
    if len(columns) != len(COLUMNS):
        raise RuntimeError('Imported worksheet must expose exactly three XYZ columns')
    data = await client.wait_and_verify(
        [ExpectedSheet(ref['book_name'], ref['sheet_name'], columns, ROWS)],
        graphs=[GRAPH], interval=.25)
    matrix_ref = execution.get('command', {}).get('derived_matrix')
    matrix_data = None
    if matrix_ref is not None:
        matrix_data = await client.call('origin_read_matrix', {
            'book_name': matrix_ref['book_name'], 'sheet_name': matrix_ref['sheet_name'],
            'object_index': 0, 'start_row': 0, 'start_col': 0, 'max_rows': 3, 'max_cols': 4})
    info = await client.call('origin_get_graph_info', {'graph_name': GRAPH})
    verified = verify_graph(info, ref, matrix_ref, matrix_data)
    units = units_verified = None
    if verified['family']['verified']:
        units = await client.call('origin_run_labtalk', {'script': UNITS_READ_SCRIPT, 'capture_log': True})
        units_verified = verify_units_annotation(units, verified['font_id'])
    return {'verification': data, 'source_to_origin_columns': list(zip(COLUMNS, columns)),
            'worksheet_info': metadata, 'matrix_readback': matrix_data,
            'graph_info': info, 'graphics_verified': verified,
            'units_annotation_verified': units_verified, 'units_readback': units}


async def adjust_once(client, run):
    if PRESENTATION_SCRIPT is None:
        return {'executed': False, 'status': 'pending_live_probe',
                'reason': 'No confirmed native presentation script; no action dispatched'}
    write_new(run / 'presentation-adjustment-started.json', {'script': PRESENTATION_SCRIPT})
    result = await client.call('origin_run_labtalk', {'script': PRESENTATION_SCRIPT, 'capture_log': True})
    write_new(run / 'presentation-adjustment-result.json', result)
    if result.get('result') is not True:
        raise RuntimeError('Explicit heatmap presentation adjustment did not execute')
    units = await client.call('origin_add_graph_label', {'graph_name': GRAPH, 'name': 'ScaleUnits',
                              'text': 'Value (a.u.)', 'left': 1800, 'top': 75, 'font_size': 9})
    font = await client.call('origin_run_labtalk', {
        'script': 'win -a HeatmapDemo; layer -s 1; ScaleUnits.font=font(Arial);', 'capture_log': True})
    if font.get('result') is not True:
        raise RuntimeError('Units annotation font did not apply')
    record = {'executed': True, 'script': PRESENTATION_SCRIPT, 'result': result,
              'units_annotation': units, 'units_font': font}
    write_new(run / 'presentation-adjustment.json', record)
    return record


async def export_new(client, run, stem, suffix):
    path = run / (stem + '.' + suffix)
    if path.exists():
        raise FileExistsError(path)
    result = await client.call('origin_export_graph', {'graph_name': GRAPH, 'path': str(path),
                              'overwrite': False, 'width': 1400 if suffix == 'png' else 0})
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError('Export file was not created: ' + str(path))
    return {**result, 'bytes': path.stat().st_size}


def verify_reopened_pixels(run):
    # Pillow is already available in this project's independent development env.
    from PIL import Image
    with Image.open(run / 'heatmap-review.png') as before, Image.open(run / 'heatmap-reopened.png') as after:
        before.load()
        after.load()
        if before.size != after.size or before.mode != after.mode or before.tobytes() != after.tobytes():
            raise RuntimeError('Reopened heatmap PNG pixels differ from reviewed PNG')
        return {'identical': True, 'size': list(before.size), 'mode': before.mode,
                'source': 'decoded PNG pixel comparison'}


async def run_phase(client, args, run, handshake):
    phase = args.phase
    if phase == 'build':
        names = ('heatmap-data.csv', 'heatmap-spec.json', 'execution.json', 'execution-started.json',
                 'presentation-adjustment-started.json', 'presentation-adjustment.json',
                 'presentation-adjustment-result.json', 'checkpoint.opju',
                 'heatmap-review.png', 'heatmap-review.pdf', 'build.json')
        if any((run / name).exists() for name in names):
            raise FileExistsError('Build inputs or outputs already exist; use a fresh run or resume')
        with (run / 'heatmap-data.csv').open('x', newline='', encoding='utf8') as stream:
            writer = csv.writer(stream)
            writer.writerow(COLUMNS)
            writer.writerows(ROWS)
        spec = fixture_spec(run)
        write_new(run / 'heatmap-spec.json', spec)
        plan = await client.call('origin_plan_figure_spec', {'spec': spec})
        if plan.get('executor_executable') is not True:
            raise RuntimeError('Candidate executor cannot run this heatmap fixture')
        write_new(run / 'execution-started.json', {'graph': GRAPH, 'retry': False})
        execution = await client.call('origin_execute_figure_spec', {'spec': spec})
        write_new(run / 'execution.json', execution)
        execution = load_execution(run)
        adjustment = await adjust_once(client, run)
    elif phase in ('resume', 'finalize'):
        execution = load_execution(run)
        action = run / 'presentation-adjustment.json'
        adjustment = json.loads(action.read_text(encoding='utf8')) if action.exists() else {
            'executed': False, 'status': 'pending_live_probe', 'reason': 'No completed presentation action recorded'}
        # Even an interrupted action is not replayed by resume.
    else:
        if not (run / 'finalize.json').is_file():
            raise RuntimeError('No finalized heatmap project; refusing automatic close')
        owned_environment(run)
        result = await client.call('origin_bridge_shutdown', {'release_origin': True,
                                                             'close_origin': True, 'timeout': 15})
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

    observation = await inspect(client, execution)
    if phase == 'finalize':
        if not args.visual_reviewed:
            raise ValueError('Actual visual review is required before finalize')
        if not observation['graphics_verified']['family']['verified']:
            raise RuntimeError('Heatmap readback remains unverified; cannot finalize')
        for name in ('heatmap-final.opju', 'heatmap-reopened.png', 'finalize.json'):
            if (run / name).exists():
                raise FileExistsError('Finalize outputs already exist: ' + name)
        if not (run / 'build.json').is_file():
            raise RuntimeError('No recorded heatmap build to finalize')
        saved = await client.save_new(run / 'heatmap-final.opju')
        opened = await client.call('origin_open_project', {'path': str(run / 'heatmap-final.opju'),
                                                         'readonly': False, 'asksave': False})
        if opened.get('opened') is not True:
            raise RuntimeError('Origin did not confirm project reopen')
        observation = await inspect(client, execution)
        if not observation['graphics_verified']['family']['verified']:
            raise RuntimeError('Reopened heatmap readback remains unverified')
        export = await export_new(client, run, 'heatmap-reopened', 'png')
        pixels = verify_reopened_pixels(run)
        write_new(run / 'finalize.json', {**observation, 'execution': execution, 'saved': saved,
                  'opened': opened, 'export': export, 'reopened_pixels': pixels,
                  'presentation_adjustment': adjustment,
                  'visual_review': {'reviewed': True, 'images': ['heatmap-review.png', 'heatmap-review.pdf'],
                      'checks': ['4 x 3 cells; bottom corners 0/3 and top corners 20/23',
                                 'Viridis scale spans 0 to 23; readable colorbar',
                                 'equal physical coordinate scale; unclipped axes and labels']},
                  'metrics': client.metrics()})
        print('HEATMAP_REOPENED: readback and decoded PNG pixels verified before close')
        return

    checkpoint = run / 'checkpoint.opju'
    saved = {'existing': True, 'path': str(checkpoint), 'bytes': checkpoint.stat().st_size} if checkpoint.exists() else await client.save_new(checkpoint)
    if saved['bytes'] <= 0:
        raise RuntimeError('Empty checkpoint')
    exports = []
    for suffix in ('png', 'pdf'):
        path = run / ('heatmap-review.' + suffix)
        if path.exists():
            if path.stat().st_size <= 0:
                raise RuntimeError('Empty existing heatmap export')
            exports.append({'existing': True, 'path': str(path), 'bytes': path.stat().st_size})
        else:
            exports.append(await export_new(client, run, 'heatmap-review', suffix))
    after = await inspect(client, execution)
    report = {**observation, 'after_export': after, 'execution': execution, 'saved': saved,
              'exports': exports, 'presentation_adjustment': adjustment, 'metrics': client.metrics()}
    name = 'build.json' if not (run / 'build.json').exists() else 'resume-' + str(args.attempt) + '.json'
    write_new(run / name, report)
    print('HEATMAP_BUILT: inspect PNG/PDF; pending=' + ','.join(after['graphics_verified']['family']['pending']))


async def main(args):
    run = args.run_dir.resolve()
    if not args.run_dir.is_absolute() or not run.is_dir() or args.attempt < 1:
        raise ValueError('Existing absolute run directory and positive attempt required')
    if args.phase == 'finalize' and not args.visual_reviewed:
        raise ValueError('Review heatmap PNG/PDF first; pass --visual-reviewed after actual inspection')
    if (run / 'unknown-outcome.json').exists():
        raise RuntimeError('Previous RPC outcome unknown; no automatic continuation or retry')
    handshake, env = owned_environment(run)
    log_dir = run / ('client-' + args.phase + '-' + str(args.attempt))
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
    parser.add_argument('--attempt', type=int, default=1, help='Fresh audit logs for an inspected continuation')
    asyncio.run(main(parser.parse_args()))
