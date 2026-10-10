import csv
from types import SimpleNamespace

import pytest
from origin_mcp.models import FigureDataSpec, FigureSpec
from origin_mcp.refs import GraphRef, WorksheetRef
import origin_mcp.tools.figurespec as figurespec

ROWS = [(x, y, 10*y+x) for y in range(3) for x in range(4)]


def source(tmp_path, rows):
    path = tmp_path / 'grid.csv'
    with path.open('w', newline='', encoding='utf8') as stream:
        writer = csv.writer(stream)
        writer.writerow(('x', 'y', 'z'))
        writer.writerows(rows)
    return FigureDataSpec(id='grid', source=path, roles={'x':'x', 'y':'y', 'z':'z'})


def test_grid_preserves_values_and_coordinate_orientation_despite_shuffled_input(tmp_path):
    data = source(tmp_path, ROWS[::2] + ROWS[1::2])
    result = figurespec._regular_xyz_grid(data, data.roles)
    assert result['data'] == [[0,1,2,3], [10,11,12,13], [20,21,22,23]]
    assert result['xymap'] == [0,3,0,2]


@pytest.mark.parametrize('rows', [ROWS+[(0,0,99)], ROWS[:-1],
    [(x*x,y,z) for x,y,z in ROWS], [(x,y,float('nan') if x==0 else z) for x,y,z in ROWS],
    [(x,y,'invalid' if x==0 else z) for x,y,z in ROWS], [(x,0,x) for x in range(4)]])
def test_unsupported_or_ambiguous_grids_fail_before_origin_writes(tmp_path, monkeypatch, rows):
    data = source(tmp_path, rows)
    def forbidden(*args, **kwargs):
        pytest.fail('Invalid heatmap must be rejected before Origin mutation')
    monkeypatch.setattr(figurespec, 'client', SimpleNamespace(new_project=forbidden))
    spec = FigureSpec(figure={'id':'HeatTest'}, runtime={'new_project':True}, data=[data],
                      layers=[{'id':'main'}], plots=[{'id':'heat','layer':'main','type':'heatmap'}])
    with pytest.raises(ValueError):
        figurespec._plan_figure(spec)


def test_cell_heatmap_uses_native_matrix_and_105_not_xyz_contour_243(tmp_path, monkeypatch):
    data = source(tmp_path, ROWS)
    calls=[]
    def imported(**kwargs):
        calls.append(('import',kwargs))
        return WorksheetRef('Raw','Sheet1',['x','y','z'],12)
    def matrix(**kwargs):
        calls.append(('matrix',kwargs))
        return {'book_name':'Grid','sheet_name':'MSheet1','data_ranges':['[Grid]MSheet1!1']}
    def plotted(**kwargs):
        calls.append(('plot',kwargs))
        return GraphRef('HeatTest')
    fake=SimpleNamespace(import_table=imported,create_matrix=matrix,plot_matrix_by_id=plotted,
                         set_plot_style=lambda **kwargs: calls.append(('style',kwargs)))
    monkeypatch.setattr(figurespec,'client',fake)
    spec=FigureSpec(figure={'id':'HeatTest'},data=[data],layers=[{'id':'main'}],
                    plots=[{'id':'heat','layer':'main','type':'heatmap','style':{'colormap':'Viridis.PAL'}}])
    raw,graph,command=figurespec._create_base_graph(spec,data,spec.layers[0],spec.plots[0])
    assert raw.book_name=='Raw' and graph.graph_name=='HeatTest'
    plot_args=next(kwargs for operation,kwargs in calls if operation=='plot')
    assert plot_args['plot_type_id']==105 and plot_args['template']=='heatmap'
    matrix_args=next(kwargs for operation,kwargs in calls if operation=='matrix')
    assert matrix_args['data']==[[0,1,2,3],[10,11,12,13],[20,21,22,23]]
    assert command['representation']=='cell_heatmap'
    assert command['transformation']['interpolation']=='none'
    assert command['transformation']['refresh_link']=='explicit rebuild required'
