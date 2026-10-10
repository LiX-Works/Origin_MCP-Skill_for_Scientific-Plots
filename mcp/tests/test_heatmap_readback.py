"""Native heatmap/XYZ readback contracts; fakes do not prove live Origin behavior."""

from __future__ import annotations

import math
import re
from types import SimpleNamespace

import pytest


class SourceReadback:
    def __init__(self, *, matrix="[HeatGrid]MSheet1!1", columns=None, rows=(1, 12), fail=False):
        self.matrix = matrix
        self.columns = columns if columns is not None else {
            axis: f"[RawXYZ]Sheet1!{column}[1:12]"
            for axis, column in zip("xyz", "ABC")
        }
        self.rows = rows
        self.fail = fail
        self.vars = {}
        self.scripts = []

    def lt_exec(self, script):
        self.scripts.append(script)
        if self.fail:
            return False
        for name in re.findall(r"range -w (\w+) =", script):
            self.vars[name] = self.matrix
        for axis, name in re.findall(r"range -w([xyz]) (\w+) =", script):
            self.vars[name] = self.columns.get(axis)
        for name, source in re.findall(r"string (\w+)\$ = %\((\w+)\);", script):
            self.vars[name] = self.vars[source]
        for flag, name in re.findall(r"get [^;]+ -([be]) (\w+);", script):
            self.vars[name] = self.rows[0 if flag == "b" else 1]
        return True

    def get_lt_str(self, name):
        return self.vars[name]

    def lt_float(self, name):
        return self.vars[name]


def native_plot(pid, *, plot_range="[GraphHeat]1!1", **properties):
    def numeric(prop):
        assert prop == "plot1.pid"
        return pid

    return SimpleNamespace(
        layer=SimpleNamespace(GetNumProp=numeric),
        index=lambda: 0,
        lt_range=lambda: plot_range,
        **properties,
    )


def test_native_105_reads_actual_matrix_address(fake_client):
    op = SourceReadback(matrix="[ActualGrid]2!3")
    fake_client._op = op
    result = fake_client._plot_data_binding(native_plot(105))
    assert result["kind"] == "matrix"
    assert result["status"] == "available"
    assert result["source"] == "OriginLab.LabTalk.range-w"
    assert result["raw_data_ranges"] == {"matrix": "[ActualGrid]2!3"}
    assert result["matrix"] == {
        "matrix_sheet": "[ActualGrid]2", "matrix_book": "ActualGrid",
        "sheet": "2", "object_index": 3, "object_index_base": 1,
    }
    assert result["x"] is result["y"] is result["z"] is result["worksheet"] is None
    assert result["row_range"] is None
    assert "range -w " in op.scripts[0]
    assert not any(token in op.scripts[0] for token in ("range -wx", "range -wy", "range -wz", "get "))
    assert op.scripts[-1].startswith("del -ra owfm")


@pytest.mark.parametrize("source,long_name", [('[MBook1]MSheet1!1"Derived Z grid"', "Derived Z grid"), ('[MBook1]MSheet1!1"Derived ""quoted"" grid"', 'Derived "quoted" grid')])
def test_matrix_source_accepts_actual_quoted_long_name(fake_client, source, long_name):
    fake_client._op = SourceReadback(matrix=source)
    result = fake_client._plot_data_binding(native_plot(105))
    assert result["status"] == "available"
    assert result["raw_data_ranges"]["matrix"] == source
    assert result["matrix"]["matrix_sheet"] == "[MBook1]MSheet1"
    assert result["matrix"]["object_index"] == 1
    assert result["matrix"]["long_name"] == long_name


@pytest.mark.parametrize("source", ["[GraphHeat]1!1", "[GraphHeat]2!2", "[Grid]1!0", "[Grid]1!Mat(MyZ)", "[Grid]1!A", "", None])
def test_matrix_unknown_or_graph_source_stays_null(fake_client, source):
    fake_client._op = SourceReadback(matrix=source)
    result = fake_client._plot_data_binding(native_plot(105))
    assert result["status"] == "unavailable"
    assert result["matrix"] is None
    assert result["raw_data_ranges"]["matrix"] == source


def test_failed_matrix_readback_cleans_variables(fake_client):
    fake_client._op = SourceReadback(fail=True)
    result = fake_client._plot_data_binding(native_plot(105))
    assert result["matrix"] is None
    assert result["raw_data_ranges"]["matrix"] is None
    assert fake_client._op.scripts[-1].startswith("del -ra owfm")


@pytest.mark.parametrize("pid", [105, 243])
def test_unsafe_plot_address_does_not_execute(fake_client, pid):
    op = SourceReadback()
    fake_client._op = op
    result = fake_client._plot_data_binding(native_plot(pid, plot_range="[Graph]1!1; win -a Other"))
    assert result["status"] == "unavailable"
    assert op.scripts == []


def test_native_243_contours_read_all_three_actual_columns(fake_client):
    op = SourceReadback()
    fake_client._op = op
    result = fake_client._plot_data_binding(native_plot(243))
    assert result["kind"] == "xyz"
    assert result["status"] == "available"
    assert result["worksheet"] == "[RawXYZ]Sheet1"
    assert [result[axis]["column"] for axis in "xyz"] == ["A", "B", "C"]
    assert result["raw_data_ranges"] == op.columns
    assert result["row_range"] == [1, 12]
    assert result["row_range_source"] == "LabTalk.get-graph-range-b-e"
    assert "range -wz " in op.scripts[0]
    assert result["observations"] is None


def test_xyz_missing_z_is_partial_and_not_echoed(fake_client):
    fake_client._op = SourceReadback(columns={"x": "[Actual]1!D", "y": "[Actual]1!F"})
    result = fake_client._plot_data_binding(native_plot(243))
    assert result["status"] == "partial"
    assert result["x"]["column"] == "D"
    assert result["y"]["column"] == "F"
    assert result["z"] is None
    assert result["worksheet"] is None
    assert result["row_range"] is None


def test_xyz_source_rows_must_agree_for_fallback(fake_client):
    fake_client._op = SourceReadback(rows=(math.nan, math.nan))
    result = fake_client._plot_data_binding(native_plot(243))
    assert result["row_range"] == [1, 12]
    assert result["row_range_source"] == "source_range_string"
    fake_client._op = SourceReadback(columns={"x": "[Actual]1!A[1:12]", "y": "[Actual]1!B[1:12]", "z": "[Actual]1!C[2:12]"}, rows=(math.nan, math.nan))
    result = fake_client._plot_data_binding(native_plot(243))
    assert result["row_range"] is None
    assert result["status"] == "partial"


def test_colormap_and_levels_remain_actual_not_requested(fake_client):
    fake_client._op = SourceReadback()
    plot = native_plot(105, colormap="ActualPalette.pal", zlevels={"minors": 0, "levels": [2.0, 11.0, 20.0]})
    result = fake_client._plot_info(plot, 0)
    assert result["native_type_id"] == 105
    assert result["colormap"] == "ActualPalette.pal"
    assert result["zlevels"]["levels"] == [2.0, 11.0, 20.0]
    assert result["data_binding"]["kind"] == "matrix"


def spectrum_label(*, values=None, title="Measured Z"):
    actual = {"labels.font": 7, "labels.fsize": 8, "revorder": 0, "title": 1}
    if values is not None:
        actual = values
    return SimpleNamespace(get_float=lambda prop: actual.get(prop, math.nan), get_str=lambda prop: title if prop == "title" else "")


def test_spectrum_readback_reads_documented_title_and_label_properties(fake_client):
    label = spectrum_label()
    result = fake_client._color_scale_readback(SimpleNamespace(label=lambda name: label if name == "Spectrum1" else None))
    assert result["status"] == "available"
    assert result["present"] is True
    assert result["title"] == "Measured Z"
    assert result["title_visible"] is True
    assert result["reverse_order"] is False
    assert result["labels"]["font_id"] == 7
    assert result["labels"]["size"] == 8
    assert result["labels"]["size_unit"] == "pt"
    assert result["labels"]["font_family"] is None
    assert result["title_typography"] is None


def test_missing_spectrum_does_not_create_or_infer_color_scale(fake_client):
    calls = []
    layer = SimpleNamespace(label=lambda name: calls.append(name))
    result = fake_client._color_scale_readback(layer)
    assert calls == ["Spectrum1"]
    assert result["status"] == "unavailable"
    assert result["present"] is False
    assert result["title"] is result["title_visible"] is result["reverse_order"] is None
    assert result["labels"]["size"] is None


def test_spectrum_labels_fall_back_to_actual_layer_properties(fake_client):
    calls = []
    actual = {"Spectrum1.labels.font": 67, "Spectrum1.labels.fsize": 8}
    layer = SimpleNamespace(label=lambda name: spectrum_label(values={}), get_float=lambda prop: calls.append(prop) or actual[prop])
    result = fake_client._color_scale_readback(layer)
    assert calls == ["Spectrum1.labels.font", "Spectrum1.labels.fsize"]
    assert result["labels"]["font_id"] == 67
    assert result["labels"]["size"] == 8
    assert result["labels"]["font_family"] is None


def test_valid_spectrum_labels_do_not_use_layer_fallback(fake_client):
    calls = []
    layer = SimpleNamespace(label=lambda name: spectrum_label(), get_float=lambda prop: calls.append(prop))
    result = fake_client._color_scale_readback(layer)
    assert calls == []
    assert result["labels"]["size"] == 8


def test_missing_spectrum_never_reads_layer_properties(fake_client):
    calls = []
    layer = SimpleNamespace(label=lambda name: None, get_float=lambda prop: calls.append(prop) or 8)
    result = fake_client._color_scale_readback(layer)
    assert calls == []
    assert result["labels"]["font_id"] is result["labels"]["size"] is None


class ScopedColorReadback:
    def __init__(self, *, fail_execute=False, fail_read=None, values=None):
        self.fail_execute = fail_execute
        self.fail_read = fail_read
        self.values = {"labels.font": 67, "labels.fsize": 8} if values is None else values
        self.vars = {}
        self.scripts = []

    def execute(self, script):
        self.scripts.append(script)
        if self.fail_execute:
            return False
        for name in re.findall(r"double (\w+) = 0/0;", script):
            self.vars[name] = math.nan
        for name, prop in re.findall(r"(\w+) = Spectrum1\.(labels\.(?:font|fsize));", script):
            self.vars[name] = (prop, self.values.get(prop, math.nan))
        return True

    def lt_float(self, name):
        prop, value = self.vars[name]
        if self.fail_read == prop:
            raise RuntimeError("unreadable actual property")
        return value


def scoped_color_layer(op, *, label_values=None):
    values = {"title": 1, "revorder": 0} if label_values is None else label_values
    return SimpleNamespace(
        label=lambda name: spectrum_label(values=values),
        get_float=lambda prop: math.nan,
        obj=SimpleNamespace(LT_execute=op.execute),
    )


def test_scoped_color_fallback_reads_actual_font_and_size_without_graph_writes(fake_client):
    op = ScopedColorReadback()
    fake_client._op = op
    result = fake_client._color_scale_readback(scoped_color_layer(op))
    assert result["labels"]["font_id"] == 67
    assert result["labels"]["size"] == 8
    assert result["title"] == "Measured Z"
    assert result["title_visible"] is True
    assert result["reverse_order"] is False
    assert "= Spectrum1.labels.font;" in op.scripts[0]
    assert "= Spectrum1.labels.fsize;" in op.scripts[0]
    assert op.scripts[-1].startswith("del -al owfcs")
    assert not re.search(r"Spectrum1\.[\w.]+\s*=", " ".join(op.scripts))
    assert not any(token in " ".join(op.scripts).lower() for token in ("win -a", "layer -s", "set "))


def test_scoped_color_failure_preserves_other_actual_properties_and_cleans(fake_client):
    op = ScopedColorReadback(fail_execute=True)
    fake_client._op = op
    result = fake_client._color_scale_readback(scoped_color_layer(op))
    assert result["labels"]["font_id"] is result["labels"]["size"] is None
    assert result["title"] == "Measured Z"
    assert result["title_visible"] is True
    assert result["reverse_order"] is False
    assert op.scripts[-1].startswith("del -al owfcs")


def test_scoped_color_single_field_failure_keeps_readable_field(fake_client):
    op = ScopedColorReadback(fail_read="labels.font")
    fake_client._op = op
    result = fake_client._color_scale_readback(scoped_color_layer(op))
    assert result["labels"]["font_id"] is None
    assert result["labels"]["size"] == 8
    assert result["title"] == "Measured Z"
    assert op.scripts[-1].startswith("del -al owfcs")


def test_scoped_color_only_queries_missing_properties(fake_client):
    op = ScopedColorReadback()
    fake_client._op = op
    result = fake_client._color_scale_readback(scoped_color_layer(op, label_values={"labels.font": 7, "title": 1, "revorder": 0}))
    assert result["labels"]["font_id"] == 7
    assert result["labels"]["size"] == 8
    assert "Spectrum1.labels.font" not in " ".join(op.scripts)


@pytest.mark.parametrize("invalid", [0, -1, math.nan])
def test_scoped_color_invalid_values_stay_unknown(fake_client, invalid):
    op = ScopedColorReadback(values={"labels.font": invalid, "labels.fsize": invalid})
    fake_client._op = op
    result = fake_client._color_scale_readback(scoped_color_layer(op))
    assert result["labels"]["font_id"] is result["labels"]["size"] is None


def test_spectrum_invalid_properties_are_explicitly_unknown(fake_client):
    label = spectrum_label(values={"labels.font": 0, "labels.fsize": -1, "revorder": 2, "title": math.nan}, title="")
    result = fake_client._color_scale_readback(SimpleNamespace(label=lambda name: label))
    assert result["present"] is True
    assert result["title"] is result["title_visible"] is result["reverse_order"] is None
    assert result["labels"]["font_id"] is result["labels"]["size"] is None


def test_layer_info_includes_actual_color_scale(fake_client, fake_op):
    graph = fake_op.new_graph()
    graph[0].labels["Spectrum1"] = spectrum_label()
    assert fake_client._layer_info(graph, 0)["color_scale"]["title"] == "Measured Z"
