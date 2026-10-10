"""Bounded heatmap guard tests; no Origin/process launch or network."""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import run_heatmap_smoke as runner


def execution():
    return {'executed': True, 'graph': {'graph_name': runner.GRAPH},
            'worksheet': {'book_name': 'HeatmapDemo_Data', 'sheet_name': 'Sheet1'},
            'command': {'derived_matrix': {'book_name': 'HeatmapDemo_Grid', 'sheet_name': 'MSheet1'}}}


def matrix_data():
    return {'matrix': {'book_name': 'HeatmapDemo_Grid', 'sheet_name': 'MSheet1',
                'shape': [3, 4], 'depth': 1, 'xymap': [0, 3, 0, 2],
                'data_ranges': ['[HeatmapDemo_Grid]MSheet1!1']},
            'object_index': 0, 'start_row': 0, 'start_col': 0, 'returned_shape': [3, 4],
            'data': [[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23]]}


def graph_info(complete=True):
    plot = {}
    geometry = {}
    if complete:
        plot = {'native_type_id': 105,
                'data_binding': {'status': 'available', 'kind': 'matrix',
                    'matrix': {'matrix_book': 'HeatmapDemo_Grid',
                        'matrix_sheet': '[HeatmapDemo_Grid]MSheet1', 'sheet': 'MSheet1',
                        'object_index': 1, 'object_index_base': 1}},
                'zlevels': {'levels': [0, 5.75, 11.5, 17.25, 23], 'minors': 0},
                'colormap': 'VIRIDIS.PAL'}
        geometry = {**runner.FRAME, 'status': 'available', 'unit': 'percent_of_page'}
    return {'layers_count': 1,
            'page_geometry': {'physical_size_mm': {'width': 100, 'height': 80},
                              'resolution_dpi': {'x': 600, 'y': 600}},
            'layers': [{'plots_count': 1, 'plots': [plot], 'geometry': geometry,
                        'color_scale': {'present': True, 'title': 'Value (a.u.)',
                            'title_visible': False, 'reverse_order': True,
                            'labels': {'size': 8, 'font_id': 2}} if complete else {},
                        'typography': {name: {'size': size, 'font_id': 2} for name, size in (
                            ('x_axis_title', 10), ('y_axis_title', 10), ('x_tick_label', 8), ('y_tick_label', 8))},
                        'axes': {'x': {'scale_name': 'linear', 'limits': [-.5, 3.5, 1]},
                                 'y': {'scale_name': 'linear', 'limits': [-.5, 2.5, 1]}}}]}


class FakeClient:
    def __init__(self, complete=True, unknown=False, changed_pixels=False):
        self.calls = []
        self.unknown_outcome = False
        self.complete, self.unknown, self.changed_pixels = complete, unknown, changed_pixels

    async def call(self, tool, args=None):
        args = args or {}
        self.calls.append((tool, args))
        if tool == 'origin_bridge_status':
            return {'origin_pid': 7, 'generation': 'fixture'}
        if tool == 'origin_plan_figure_spec':
            return {'executor_executable': True}
        if tool == 'origin_execute_figure_spec':
            if self.unknown:
                self.unknown_outcome = True
                raise TimeoutError('unknown execution result')
            return execution()
        if tool == 'origin_run_labtalk':
            if args.get('script') == runner.UNITS_READ_SCRIPT:
                return {'result': True, 'message_log': {'lines': [
                    'SCALE_UNITS=Value (a.u.)', 'SCALE_SIZE=9 FONT=2 PAL_FLIP=1']}}
            return {'result': True}
        if tool == 'origin_add_graph_label':
            return {'label_name': 'ScaleUnits'}
        if tool == 'origin_get_worksheet_info':
            return {'columns': ['A', 'B', 'C']}
        if tool == 'origin_get_graph_info':
            return graph_info(self.complete)
        if tool == 'origin_read_matrix':
            assert args['max_rows'] == 3 and args['max_cols'] == 4
            return matrix_data()
        if tool == 'origin_export_graph':
            path = Path(args['path'])
            if path.suffix == '.png':
                color = (1, 2, 3) if not self.changed_pixels or 'reopened' not in path.stem else (1, 2, 4)
                Image.new('RGB', (8, 6), color).save(path)
            else:
                path.write_bytes(b'fixture-pdf')
            return {'path': str(path)}
        if tool == 'origin_open_project':
            return {'opened': True}
        raise AssertionError(tool)

    async def wait_and_verify(self, expected, **options):
        self.calls.append(('wait_and_verify', options))
        assert len(expected) == 1
        assert expected[0].rows == runner.ROWS
        assert expected[0].columns == ('A', 'B', 'C')
        return {'data_verified': {expected[0].key: {'all_expected_values_match': True,
                                                  'rows': 12, 'cols': 3}}}

    async def save_new(self, path):
        self.calls.append(('save_new', str(path)))
        path.write_bytes(b'fixture-opju')
        return {'saved': True, 'path': str(path), 'bytes': path.stat().st_size}

    def metrics(self):
        return {'unknown_outcome': self.unknown_outcome}


def args(tmp_path, phase='build', attempt=1):
    return SimpleNamespace(run_dir=tmp_path, phase=phase, attempt=attempt,
                           visual_reviewed=phase == 'finalize')


def test_grid_semantics_and_static_planner(tmp_path):
    assert runner.ROWS == tuple((x, y, 10 * y + x) for y in range(3) for x in range(4))
    assert len(runner.ROWS) == 12
    assert [runner.ROWS[i][2] for i in (0, 3, 8, 11)] == [0, 3, 20, 23]
    spec = runner.fixture_spec(tmp_path)
    assert spec['runtime']['new_project'] is True
    assert spec['data'][0]['object'] == 'worksheet'
    assert spec['data'][0]['roles'] == {'x': 'x', 'y': 'y', 'z': 'z'}
    assert spec['plots'][0]['type'] == 'heatmap'
    assert spec['plots'][0]['style'] == {'colormap': 'Viridis.PAL', 'color_scale_limits': [0, 23],
                                        'contour_levels': list(range(24))}
    assert spec['layers'][0]['position'] == runner.FRAME
    with Path(spec['data'][0]['source']).open('x', newline='', encoding='utf8') as stream:
        writer = csv.writer(stream)
        writer.writerow(runner.COLUMNS)
        writer.writerows(runner.ROWS)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mcp' / 'src'))
    from origin_mcp.models import FigureSpec
    from origin_mcp.tools.figurespec import _plan_figure
    plan = _plan_figure(FigureSpec.model_validate(spec))
    assert plan['executor_executable'] is True
    assert plan['warnings'] == []


def test_missing_native_metadata_stays_pending():
    result = runner.verify_graph(graph_info(False), execution()['worksheet'])
    assert result['family']['verified'] is False
    assert set(result['family']['pending']) == {'actual layer geometry', 'actual heatmap native type',
        'actual matrix binding', 'actual derived matrix full values and coordinate map',
        'actual color levels', 'actual colormap', 'actual color scale present',
        'actual color scale title_visible',
        'actual color scale reverse_order', 'actual color scale labels size',
        'actual color scale labels font_id'}


def test_native_printer_dot_quantization_keeps_physical_frame_in_bounds():
    info = graph_info()
    info['page_geometry']['physical_size_mm'] = {'width': 99.99133, 'height': 79.96767}
    info['layers'][0]['geometry'].update(left=16, top=10.01, width=59.99, height=56.27)
    result = runner.verify_graph(info, execution()['worksheet'],
                                 execution()['command']['derived_matrix'], matrix_data())
    assert result['family']['verified'] is True


def test_frame_percent_quantization_does_not_relax_physical_one_dot_bound():
    info = graph_info()
    # The 0.04/0.05 percent changes fit the respective one-dot-plus-rounding
    # percentage tolerances, but page rounding in the same direction pushes the
    # physical width or height past one printer dot.
    for dimension, axis, actual_page, actual_percent in (
            ('width', 'x', 100.04, 60.04), ('height', 'y', 80.04, 56.30)):
        changed = deepcopy(info)
        changed['page_geometry']['physical_size_mm'][dimension] = actual_page
        changed['layers'][0]['geometry'][dimension] = actual_percent
        with pytest.raises(RuntimeError, match='physical frame'):
            runner.verify_graph(changed, execution()['worksheet'],
                                execution()['command']['derived_matrix'], matrix_data())


@pytest.mark.parametrize('corruption', ['wrong_matrix', 'values', 'xymap', 'type', 'levels', 'colormap', 'color_scale', 'geometry', 'page', 'axis'])
def test_actual_readback_corruption_rejected(corruption):
    info = graph_info()
    layer = info['layers'][0]
    plot = layer['plots'][0]
    matrix = matrix_data()
    if corruption == 'wrong_matrix':
        plot['data_binding']['matrix']['matrix_sheet'] = '[wrong]MSheet1'
    elif corruption == 'values':
        matrix['data'][2][3] = 22
    elif corruption == 'xymap':
        matrix['matrix']['xymap'] = [0, 2, 0, 3]
    elif corruption == 'type':
        plot['native_type_id'] = 226
    elif corruption == 'levels':
        plot['zlevels']['levels'][-1] = 24
    elif corruption == 'colormap':
        plot['colormap'] = 'Rainbow.PAL'
    elif corruption == 'color_scale':
        layer['color_scale']['reverse_order'] = False
    elif corruption == 'geometry':
        layer['geometry']['height'] = 60
    elif corruption == 'page':
        info['page_geometry']['physical_size_mm']['height'] = 81
    else:
        layer['axes']['y']['limits'] = [2.5, -.5, 1]
    with pytest.raises(RuntimeError):
        runner.verify_graph(info, execution()['worksheet'], execution()['command']['derived_matrix'], matrix)


def test_existing_output_blocks_build_before_mutation(tmp_path):
    (tmp_path / 'checkpoint.opju').write_bytes(b'protected')
    client = FakeClient()
    with pytest.raises(FileExistsError):
        asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    assert client.calls == []
    assert (tmp_path / 'checkpoint.opju').read_bytes() == b'protected'


def test_build_finalize_preserve_full_xyz_and_compare_decoded_pixels(tmp_path):
    client = FakeClient()
    asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    build = json.loads((tmp_path / 'build.json').read_text())
    assert build['source_to_origin_columns'] == [['x', 'A'], ['y', 'B'], ['z', 'C']]
    assert build['graphics_verified']['family']['verified'] is True
    assert build['presentation_adjustment']['script'] == runner.PRESENTATION_SCRIPT
    before = len(client.calls)
    asyncio.run(runner.run_phase(client, args(tmp_path, 'finalize'), tmp_path, {}))
    assert not any(tool in ('origin_execute_figure_spec', 'origin_add_graph_label')
                   or (tool == 'origin_run_labtalk' and arguments['script'] != runner.UNITS_READ_SCRIPT)
                   for tool, arguments in client.calls[before:])
    final = json.loads((tmp_path / 'finalize.json').read_text())
    assert final['reopened_pixels']['identical'] is True
    assert final['visual_review']['reviewed'] is True


def test_resume_never_replays_execution_or_presentation(tmp_path):
    runner.write_new(tmp_path / 'execution.json', execution())
    runner.write_new(tmp_path / 'presentation-adjustment-started.json', {'script': runner.PRESENTATION_SCRIPT})
    client = FakeClient(complete=False)
    asyncio.run(runner.run_phase(client, args(tmp_path, 'resume', 2), tmp_path, {}))
    assert not any(tool in ('origin_plan_figure_spec', 'origin_execute_figure_spec', 'origin_run_labtalk')
                   for tool, _ in client.calls)
    report = json.loads((tmp_path / 'build.json').read_text())
    assert report['presentation_adjustment']['executed'] is False
    assert report['graphics_verified']['family']['verified'] is False


def test_finalize_pending_metadata_blocks_save(tmp_path):
    runner.write_new(tmp_path / 'execution.json', execution())
    client = FakeClient(complete=False)
    with pytest.raises(RuntimeError, match='readback remains unverified'):
        asyncio.run(runner.run_phase(client, args(tmp_path, 'finalize'), tmp_path, {}))
    assert not any(tool in ('save_new', 'origin_open_project') for tool, _ in client.calls)


def test_changed_reopened_pixels_do_not_record_success(tmp_path):
    client = FakeClient(changed_pixels=True)
    asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    with pytest.raises(RuntimeError, match='PNG pixels differ'):
        asyncio.run(runner.run_phase(client, args(tmp_path, 'finalize'), tmp_path, {}))
    assert not (tmp_path / 'finalize.json').exists()


def test_hidden_native_title_is_not_mistaken_for_visible_units_label():
    info = graph_info()
    info['layers'][0]['color_scale']['title'] = None
    assert runner.verify_graph(info, execution()['worksheet'],
                               execution()['command']['derived_matrix'], matrix_data())['family']['verified']
    actual = {'result': True, 'message_log': {'lines': [
        'SCALE_UNITS=Value (a.u.)', 'SCALE_SIZE=9 FONT=2 PAL_FLIP=1']}}
    assert runner.verify_units_annotation(actual, 2)['size_pt'] == 9
    with pytest.raises(RuntimeError):
        runner.verify_units_annotation({'result': True, 'message_log': {'lines': []}}, 2)


def test_unknown_execution_marker_blocks_new_attempt(tmp_path, monkeypatch):
    client = FakeClient(unknown=True)

    @asynccontextmanager
    async def fake_connect(*unused, **kwargs):
        yield client

    monkeypatch.setattr(runner, 'connect', fake_connect)
    monkeypatch.setattr(runner, 'owned_environment', lambda run: ({'origin_pid': 7, 'generation': 'fixture'}, {}))
    with pytest.raises(TimeoutError):
        asyncio.run(runner.main(args(tmp_path)))
    marker = json.loads((tmp_path / 'unknown-outcome.json').read_text())
    assert marker['retry'] is False
    assert (tmp_path / 'execution-started.json').is_file()
    assert not (tmp_path / 'execution.json').exists()
    calls = deepcopy(client.calls)
    with pytest.raises(RuntimeError, match='Previous RPC outcome unknown'):
        asyncio.run(runner.main(args(tmp_path, 'resume', 2)))
    assert client.calls == calls
