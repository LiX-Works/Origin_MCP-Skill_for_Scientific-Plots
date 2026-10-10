"""S3 offline guard/fixture tests; no Origin, process launch, or networking."""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import run_family_smoke as runner


def graph_info(graph):
    category = graph == 'CategoryDemo'
    return {'layers_count': 1,
            'page_geometry': {'physical_size_mm': {'width': 90, 'height': 65},
                              'resolution_dpi': {'x': 600, 'y': 600}},
            'layers': [{'plots_count': 1, 'plots': [{}],
                        'typography': {name: {'size': size, 'font_id': 2} for name, size in (
                            ('x_axis_title', 10), ('y_axis_title', 10), ('x_tick_label', 8), ('y_tick_label', 8))},
                        'axes': {'x': {'scale_name': 'linear', 'limits': [.5, 4.5, 1] if category else [0, 5, 1]},
                                 'y': {'scale_name': 'linear', 'limits': [0, 2.2, .5] if category else [0, 9, 1]}}}]}


def execution():
    return {'executed': True, 'figures': {graph: {'executed': True, 'graph': {'graph_name': graph},
            'worksheet': {'book_name': graph + '_Data', 'sheet_name': 'Sheet1'}} for graph in runner.FIXTURES}}


def bin_table():
    labels = ['箱中心', '计数', '累计计数', '累计百分比']
    values = [(0.5, 3, 3, 15), (1.5, 4, 7, 35), (2.5, 7, 14, 70),
              (3.5, 4, 18, 90), (4.5, 2, 20, 100)]
    return {'worksheet': {'book_name': 'HistogramDemo_Data', 'sheet_name': 'NativeBin'},
            'columns': labels, 'start_row': 0, 'total_rows': 5, 'returned_rows': 5,
            'rows': [dict(zip(labels, row)) for row in values]}


def adjustment():
    return {'executed': True, 'bin_worksheet': {'book_name': 'HistogramDemo_Data', 'sheet_name': 'NativeBin'}}


def complete_graph_info(graph):
    info = graph_info(graph)
    ref = execution()['figures'][graph]['worksheet']
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    category = graph == 'CategoryDemo'
    info['layers'][0]['plots'][0].update(
        native_type_id=203 if category else 219,
        data_binding={'status': 'available', 'kind': 'xy' if category else 'observations',
                      'worksheet': worksheet, 'row_range': [1, 4 if category else 20],
                      'x': {'column': 'A'}, 'y': {'column': 'B'}, 'observations': {'column': 'A'}},
        histogram={'bin_width': 1, 'begin': 0, 'end': 5, 'normalization': None,
                   'normalization_status': 'unavailable'})
    info['layers'][0]['axes']['x']['tick_label'] = {
        'status': 'available', 'type_code': 2, 'dataset': worksheet + '!A"Category"'}
    return info


class FakeClient:
    def __init__(self, fail_second=False, full_readback=False):
        self.calls = []
        self.fail_second = fail_second
        self.unknown_outcome = False
        self.full_readback = full_readback
        self.bin_created = False

    async def call(self, tool, args=None):
        args = args or {}
        self.calls.append((tool, args))
        if tool == 'origin_plan_figure_spec':
            return {'executor_executable': True}
        if tool == 'origin_execute_figure_spec':
            graph = args['spec']['figure']['id']
            if self.fail_second and graph == 'HistogramDemo':
                self.unknown_outcome = True
                raise TimeoutError('unknown result')
            return execution()['figures'][graph]
        if tool == 'origin_get_worksheet_info':
            graph = args['book_name'].removesuffix('_Data')
            return {'columns': ['A', 'B'] if graph == 'CategoryDemo' else ['A']}
        if tool == 'origin_get_graph_info':
            return deepcopy((complete_graph_info if self.full_readback else graph_info)(args['graph_name']))
        if tool == 'origin_read_worksheet':
            assert args['columns'] == [0, 1, 2, 3]
            return bin_table()
        if tool == 'origin_run_labtalk':
            if 'OpenBinWks' in args['script']:
                self.bin_created = True
            return {'result': True}
        if tool == 'origin_list_project':
            return {'workbooks': [{'name': 'CategoryDemo_Data', 'sheets': [{'name': 'Sheet1'}]},
                    {'name': 'HistogramDemo_Data', 'sheets': [{'name': 'Sheet1'}] +
                    ([{'name': 'NativeBin'}] if self.bin_created else [])}],
                    'graphs': [{'name': graph} for graph in runner.FIXTURES]}
        if tool == 'origin_export_graph':
            Path(args['path']).write_bytes(b'fixture-export')
            return {'path': args['path']}
        if tool == 'origin_open_project':
            return {'opened': True}
        if tool == 'origin_bridge_status':
            return {'origin_pid': 7, 'generation': 'fixture'}
        raise AssertionError(tool)

    async def wait_and_verify(self, expected, **options):
        self.calls.append(('wait_and_verify', options))
        assert len(expected) == 2
        assert expected[0].rows == runner.FIXTURES['CategoryDemo']['rows']
        assert expected[1].rows == runner.FIXTURES['HistogramDemo']['rows']
        return {'full_data_verified': True}

    async def save_new(self, path):
        self.calls.append(('save_new', str(path)))
        path.write_bytes(b'fixture-project')
        return {'saved': True, 'path': str(path), 'bytes': path.stat().st_size}

    def metrics(self):
        return {'unknown_outcome': self.unknown_outcome}


def args(tmp_path, phase='build'):
    return SimpleNamespace(run_dir=tmp_path, phase=phase, attempt=1, visual_reviewed=phase == 'finalize')


def test_specs_keep_input_semantics_and_one_project(tmp_path):
    specs = runner.fixture_specs(tmp_path)
    category, histogram = specs.values()
    assert [s['runtime']['new_project'] for s in specs.values()] == [True, False]
    assert category['plots'][0]['type'] == 'column'
    assert category['layers'][0]['y']['limits'][0] == 0
    assert runner.FIXTURES['CategoryDemo']['rows'] == tuple(zip(('Control', 'Method A', 'Method B', 'Method C'), (1.2, 1.6, 1.4, 1.9)))
    assert histogram['data'][0]['roles'] == {'y': 'obs'}
    assert histogram['plots'][0]['style']['histogram_bin_width'] == 1
    assert histogram['layers'][0]['y']['title'] == 'Count'
    assert len(runner.OBSERVATIONS) == 20
    assert all(0 < v < 5 and v != int(v) for v in runner.OBSERVATIONS)
    assert all('uncertainty' not in s['plots'][0] for s in specs.values())


def test_fixture_specs_are_executable_by_candidate_static_planner(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mcp' / 'src'))
    from origin_mcp.models import FigureSpec
    from origin_mcp.tools.figurespec import _plan_figure
    import csv

    for graph, spec in runner.fixture_specs(tmp_path).items():
        fixture = runner.FIXTURES[graph]
        with Path(spec['data'][0]['source']).open('x', newline='', encoding='utf8') as stream:
            writer = csv.writer(stream)
            writer.writerow(fixture['columns'])
            writer.writerows(fixture['rows'])
        plan = _plan_figure(FigureSpec.model_validate(spec))
        assert plan['executor_executable'] is True
        assert plan['warnings'] == []


@pytest.mark.parametrize('graph', runner.FIXTURES)
def test_shared_readback_does_not_claim_family_completion(graph):
    verified = runner.verify_graph(graph, graph_info(graph), execution()['figures'][graph]['worksheet'])
    assert verified['page_size_verified'] and verified['typography_verified']
    assert verified['family']['verified'] is False
    assert verified['family']['pending']


@pytest.mark.parametrize('graph', runner.FIXTURES)
def test_family_source_readback_rejects_truncated_or_wrong_column(graph):
    info = graph_info(graph)
    ref = execution()['figures'][graph]['worksheet']
    worksheet = '[' + ref['book_name'] + ']' + ref['sheet_name']
    category = graph == 'CategoryDemo'
    binding = {'status': 'available', 'worksheet': worksheet,
               'kind': 'xy' if category else 'observations',
               'row_range': [1, 4 if category else 20],
               'x': {'column': 'A'}, 'y': {'column': 'B'}, 'observations': {'column': 'A'}}
    plot = info['layers'][0]['plots'][0]
    plot.update(data_binding=binding, native_type_id=203 if category else 219)
    plot['histogram'] = {'bin_width': 1, 'begin': 0, 'end': 5}
    result = runner.verify_graph(graph, info, ref)['family']
    assert result['binding_verified'] is True
    assert result['verified'] is False  # Missing category order or actual count table.
    binding['row_range'][1] -= 1
    with pytest.raises(RuntimeError, match='source A/B rows|raw observations'):
        runner.verify_graph(graph, info, ref)


def test_histogram_binwidth_mismatch_is_rejected():
    info = graph_info('HistogramDemo')
    info['layers'][0]['plots'][0].update(native_type_id=219, histogram={'bin_width': .5})
    with pytest.raises(RuntimeError, match='bin_width differs'):
        runner.verify_graph('HistogramDemo', info, execution()['figures']['HistogramDemo']['worksheet'])


@pytest.mark.parametrize('bad', ['page', 'title', 'font', 'axis'])
def test_actual_graph_mismatch_is_rejected(bad):
    info = graph_info('CategoryDemo')
    if bad == 'page':
        info['page_geometry']['physical_size_mm']['width'] = 99
    elif bad == 'title':
        info['layers'][0]['typography']['x_axis_title']['size'] = 8
    elif bad == 'font':
        info['layers'][0]['typography']['x_axis_title']['font_id'] = None
    else:
        info['layers'][0]['axes']['y']['limits'][0] = 1
    with pytest.raises(RuntimeError):
        runner.verify_graph('CategoryDemo', info, execution()['figures']['CategoryDemo']['worksheet'])


def test_second_execution_unknown_preserves_first_success(tmp_path):
    client = FakeClient(fail_second=True)
    with pytest.raises(TimeoutError):
        asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    first = json.loads((tmp_path / 'execution-CategoryDemo.json').read_text())
    assert first['executed'] is True
    assert not (tmp_path / 'execution.json').exists()
    assert len([call for call in client.calls if call[0] == 'origin_execute_figure_spec']) == 2


def test_resume_reads_and_completes_outputs_without_reexecuting(tmp_path):
    runner.write_new(tmp_path / 'execution.json', execution())
    runner.write_new(tmp_path / 'presentation-adjustment.json', adjustment())
    client = FakeClient()
    asyncio.run(runner.run_phase(client, args(tmp_path, 'resume'), tmp_path, {}))
    assert 'origin_execute_figure_spec' not in [call[0] for call in client.calls]
    assert 'origin_plan_figure_spec' not in [call[0] for call in client.calls]
    assert 'origin_run_labtalk' not in [call[0] for call in client.calls]
    assert (tmp_path / 'checkpoint.opju').stat().st_size > 0
    assert len(list(tmp_path.glob('*-review.*'))) == 4
    report = json.loads((tmp_path / 'build.json').read_text(encoding='utf8'))
    assert report['source_to_origin_columns']['HistogramDemo'] == [['obs', 'A']]


def test_existing_inputs_reject_build_before_origin_mutation(tmp_path):
    (tmp_path / 'category-data.csv').write_text('protected')
    client = FakeClient()
    with pytest.raises(FileExistsError):
        asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    assert client.calls == []
    assert (tmp_path / 'category-data.csv').read_text() == 'protected'


def test_finalize_pending_contract_refuses_before_save(tmp_path):
    runner.write_new(tmp_path / 'execution.json', execution())
    runner.write_new(tmp_path / 'presentation-adjustment.json', adjustment())
    client = FakeClient()
    with pytest.raises(RuntimeError, match='Family readback remains unverified'):
        asyncio.run(runner.run_phase(client, args(tmp_path, 'finalize'), tmp_path, {}))
    assert 'save_new' not in [call[0] for call in client.calls]
    assert 'origin_open_project' not in [call[0] for call in client.calls]


def test_complete_histogram_verifies_actual_table_without_inventing_normalization_mode():
    graph = 'HistogramDemo'
    result = runner.verify_graph(graph, complete_graph_info(graph), execution()['figures'][graph]['worksheet'], bin_table())['family']
    assert result['verified'] is True
    assert result['counts']['counts'] == [3, 4, 7, 4, 2]
    assert result['counts']['sum'] == 20
    assert result['mode_metadata_verified'] is False
    assert result['mode_metadata_status'] == 'unavailable'


@pytest.mark.parametrize('corruption', ['count', 'center', 'cumulative', 'percentage', 'bounds'])
def test_native_bin_table_corruption_or_truncated_bounds_is_rejected(corruption):
    histogram = {'bin_width': 1, 'begin': 0, 'end': 5}
    bins = bin_table()
    if corruption == 'bounds':
        histogram['end'] = 2
    else:
        position = {'center': 0, 'count': 1, 'cumulative': 2, 'percentage': 3}[corruption]
        bins['rows'][2][bins['columns'][position]] += 1
    with pytest.raises((ValueError, RuntimeError)):
        runner.verify_bins(histogram, bins)


def test_category_tick_source_checks_quoted_actual_dataset():
    graph = 'CategoryDemo'
    ref = execution()['figures'][graph]['worksheet']
    info = complete_graph_info(graph)
    assert runner.verify_graph(graph, info, ref)['family']['verified'] is True
    info['layers'][0]['axes']['x']['tick_label']['dataset'] = '[wrong]Sheet1!A"Category"'
    with pytest.raises(RuntimeError, match='Category tick text'):
        runner.verify_graph(graph, info, ref)


def test_build_records_native_bin_action_once_and_finalize_reopens(tmp_path):
    client = FakeClient(full_readback=True)
    asyncio.run(runner.run_phase(client, args(tmp_path), tmp_path, {}))
    action = json.loads((tmp_path / 'presentation-adjustment.json').read_text(encoding='utf8'))
    assert action['bin_worksheet'] == adjustment()['bin_worksheet']
    assert len([call for call in client.calls if call[0] == 'origin_run_labtalk']) == 2
    assert 'layer.fixed=1' in action['scripts']['CategoryDemo']
    assert 'OpenBinWks nRecalculate:=1' in action['scripts']['HistogramDemo']
    build = json.loads((tmp_path / 'build.json').read_text(encoding='utf8'))
    assert all(family['family']['verified'] for family in build['graphics_verified'].values())
    prior = len(client.calls)
    asyncio.run(runner.run_phase(client, args(tmp_path, 'finalize'), tmp_path, {}))
    assert 'origin_execute_figure_spec' not in [call[0] for call in client.calls[prior:]]
    assert 'origin_run_labtalk' not in [call[0] for call in client.calls[prior:]]
    assert (tmp_path / 'families-final.opju').exists()
    assert len(list(tmp_path.glob('*-reopened.png'))) == 2
    assert json.loads((tmp_path / 'finalize.json').read_text(encoding='utf8'))['visual_review']['reviewed'] is True


def test_unknown_outcome_persists_across_attempts(tmp_path, monkeypatch):
    client = FakeClient(fail_second=True)

    @asynccontextmanager
    async def fake_connect(*unused, **kwargs):
        yield client

    monkeypatch.setattr(runner, 'connect', fake_connect)
    monkeypatch.setattr(runner, 'owned_environment', lambda run: ({'origin_pid': 7, 'generation': 'fixture'}, {}))
    with pytest.raises(TimeoutError):
        asyncio.run(runner.main(args(tmp_path)))
    marker = json.loads((tmp_path / 'unknown-outcome.json').read_text())
    assert marker['retry'] is False
    calls_before = len(client.calls)
    continuation = args(tmp_path, 'resume')
    continuation.attempt = 2
    with pytest.raises(RuntimeError, match='Previous RPC outcome unknown'):
        asyncio.run(runner.main(continuation))
    assert len(client.calls) == calls_before
