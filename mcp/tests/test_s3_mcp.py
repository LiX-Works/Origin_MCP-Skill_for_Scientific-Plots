"""Bounded inspection tests; these fakes do not establish Origin runtime behavior."""

from __future__ import annotations

import math
import re
from types import SimpleNamespace

import pytest

from origin_mcp.errors import OriginOperationError


class ReadbackOp:
    def __init__(self, *, bin_sheet="[Bin1]Binn1", width=0.5, begin=-1, end=2, fail=False, fail_sheet=False, fail_flag=None):
        self.bin_sheet = bin_sheet
        self.values = {"hbs": width, "hbb": begin, "hbe": end, "b": 1, "e": 12}
        self.vars = {}
        self.scripts = []
        self.fail = fail
        self.fail_sheet = fail_sheet
        self.fail_flag = fail_flag

    def lt_exec(self, script):
        self.scripts.append(script)
        if self.fail:
            return False
        if (self.fail_sheet and "-nhw " in script) or (self.fail_flag and f"-{self.fail_flag} " in script):
            return False
        for name in re.findall(r"double (\w+) = 0/0;", script):
            self.vars[name] = math.nan
        for name, value in re.findall(r"double (\w+) = (-?\d+);", script):
            self.vars[name] = float(value)
        for name in re.findall(r'string (\w+)\$ = "";', script):
            self.vars[name] = ""
        for flag, name in re.findall(r"get [^;]+ -(hbs|hbb|hbe|b|e) (\w+);", script):
            self.vars[name] = self.values[flag]
        for name in re.findall(r"get [^;]+ -nhw (\w+);", script):
            self.vars[name] = self.bin_sheet
        for axis, name in re.findall(r"range -w([xy]) (\w+) =", script):
            self.vars[name] = f"[Raw]Sheet1!{'A' if axis == 'x' else 'B'}[1:12]"
        for name, source in re.findall(r"string (\w+)\$ = %\((\w+)\);", script):
            self.vars[name] = self.vars[source]
        return True

    def lt_float(self, name):
        return self.vars[name]

    def get_lt_str(self, name):
        return self.vars[name]


def native_plot(pid, op=None):
    def numeric(prop):
        assert prop == "plot1.pid"
        return pid

    return SimpleNamespace(name="Raw_B", layer=SimpleNamespace(GetNumProp=numeric, LT_execute=op.lt_exec if op else lambda script: False), index=lambda: 0, lt_range=lambda: "[Hist]1!1")


def test_histogram_inspector_reads_actual_values_without_creating_bin_sheet(fake_client):
    op = ReadbackOp()
    fake_client._op = op
    result = fake_client._plot_info(native_plot(219, op), 0)
    histogram = result["histogram"]
    assert result["native_type_id"] == 219
    assert histogram["status"] == "available"
    assert (histogram["bin_width"], histogram["begin"], histogram["end"]) == (0.5, -1, 2)
    assert histogram["bin_worksheet"] == "[Bin1]Binn1"
    assert histogram["normalization"] is None
    assert histogram["normalization_status"] == "unavailable"
    assert histogram["counts_status"] == "not_read"
    assert not any(token in " ".join(op.scripts).lower() for token in ("-nhwc", "openbinwks", "win -a", "set "))


def test_histogram_binding_has_only_observations(fake_client):
    op = ReadbackOp()
    fake_client._op = op
    result = fake_client._plot_data_binding(native_plot(219))
    assert result["kind"] == "observations"
    assert result["x"] is result["y"] is None
    assert result["observations"]["worksheet"] == "[Raw]Sheet1"
    assert result["observations"]["column"] == "B"
    assert result["raw_data_ranges"] == {"observations": "[Raw]Sheet1!B[1:12]"}
    assert result["row_range"] == [1, 12]
    assert "range -wx" not in " ".join(op.scripts)


def test_xy_binding_still_reads_both_columns(fake_client):
    fake_client._op = ReadbackOp()
    result = fake_client._plot_data_binding(native_plot(202))
    assert result["kind"] == "xy"
    assert result["x"]["column"] == "A"
    assert result["y"]["column"] == "B"
    assert result["observations"] is None
    assert result["status"] == "available"


def test_missing_bin_sheet_stays_unavailable_and_is_not_created(fake_client):
    fake_client._op = ReadbackOp(bin_sheet="")
    result = fake_client._histogram_readback(native_plot(219, fake_client._op))
    assert result["bin_worksheet"] is None
    assert result["bin_worksheet_status"] == "unavailable"
    assert result["counts_status"] == "not_read"
    assert "-nhwc" not in " ".join(fake_client._op.scripts)


@pytest.mark.parametrize("width,begin,end", [(0, -1, -1), (math.nan, math.nan, math.nan), (-1, 3, 2)])
def test_invalid_histogram_readback_does_not_claim_available(fake_client, width, begin, end):
    fake_client._op = ReadbackOp(width=width, begin=begin, end=end)
    result = fake_client._histogram_readback(native_plot(219, fake_client._op))
    assert result["status"] == "unavailable"
    assert result["bin_width"] is None
    assert result["begin"] is result["end"] is None


def test_failed_readback_cleans_variables_and_keeps_unavailable(fake_client):
    fake_client._op = ReadbackOp(fail=True)
    result = fake_client._histogram_readback(native_plot(219, fake_client._op))
    assert result["status"] == "unavailable"
    assert fake_client._op.scripts[-1].startswith("del -al owfh")


@pytest.mark.parametrize("code,name", [(2, "text_from_dataset"), (7, "column_headings"), (9, "categorical")])
def test_tick_label_readback_uses_documented_type_codes(fake_client, code, name):
    def numeric(prop):
        assert prop == "x.label.type"
        return code

    def string(prop):
        assert prop == "x.label.dataset"
        return "Raw_A"

    axis = SimpleNamespace(ax="x", layer=SimpleNamespace(GetNumProp=numeric, GetStrProp=string))
    info = fake_client._axis_info(axis)
    assert info["tick_label"]["type_code"] == code
    assert info["tick_label"]["type_name"] == name
    assert info["tick_label"]["dataset"] == "Raw_A"


def test_non_histogram_plot_does_not_get_histogram_metadata(fake_client):
    fake_client._op = ReadbackOp()
    assert "histogram" not in fake_client._plot_info(native_plot(202), 0)


@pytest.mark.parametrize("template,expected", [(None, "Hist"), ("OwnHistogram.otpu", "OwnHistogram.otpu")])
def test_histogram_creation_uses_native_default_and_preserves_custom(fake_client, template, expected):
    calls = []
    graph = object()

    def new_graph(**kwargs):
        calls.append(kwargs)
        return graph

    fake_client._op = SimpleNamespace(new_graph=new_graph)
    assert fake_client._new_graph("histogram", None, template) is graph
    assert calls == [{"template": expected}]


@pytest.mark.parametrize("positional_fallback", [False, True])
def test_none_graph_reports_template_creation_failure(fake_client, positional_fallback):
    def new_graph(*args, **kwargs):
        if positional_fallback and kwargs:
            raise TypeError("legacy signature")
        return None

    fake_client._op = SimpleNamespace(new_graph=new_graph)
    with pytest.raises(OriginOperationError, match="failed to create graph from template 'Hist'") as error:
        fake_client._new_graph("histogram", None)
    assert error.value.error_code == "graph_creation_failed"


def test_bin_sheet_failure_preserves_independent_number_readback(fake_client):
    op = ReadbackOp(width=1, begin=0, end=5, fail_sheet=True)
    fake_client._op = op
    result = fake_client._histogram_readback(native_plot(219, op))
    assert result["status"] == "available"
    assert (result["bin_width"], result["begin"], result["end"]) == (1, 0, 5)
    assert result["bin_worksheet"] is None
    assert result["bin_worksheet_status"] == "unavailable"
    assert all("get [Hist]" not in script for script in op.scripts)
    assert any("get Raw_B -hbb" in script for script in op.scripts)


def test_individual_number_failure_retains_other_settings(fake_client):
    op = ReadbackOp(fail_flag="hbb")
    fake_client._op = op
    result = fake_client._histogram_readback(native_plot(219, op))
    assert result["status"] == "partial"
    assert result["bin_width"] == 0.5
    assert result["begin"] is None
    assert result["end"] == 2


def test_plot_table_sizes_new_single_column_sheet_before_import(fake_client, tmp_path, monkeypatch):
    from fake_origin import FakeWorksheet

    events = []
    original_from_df = FakeWorksheet.from_df
    original_set_cols = FakeWorksheet.cols.fset

    def set_cols(sheet, count):
        events.append(("cols", count))
        original_set_cols(sheet, count)

    def from_df(sheet, df, c1=0):
        events.append(("from_df", len(df.columns)))
        assert events[-2] == ("cols", len(df.columns))
        original_from_df(sheet, df, c1)

    monkeypatch.setattr(FakeWorksheet, "cols", property(FakeWorksheet.cols.fget, set_cols))
    monkeypatch.setattr(FakeWorksheet, "from_df", from_df)
    csv = tmp_path / "observations.csv"
    csv.write_text("Obs\n0.2\n0.7\n1.4\n", encoding="utf-8")
    worksheet, _ = fake_client.plot_table(path=csv, kind="histogram", x_col="Obs", y_cols=["Obs"], style_mode="none", histogram_bin_width=1)
    assert worksheet.columns == ["Obs"]
    assert fake_client.op.books[-1][0].cols == 1
    assert events == [("cols", 1), ("from_df", 1)]
