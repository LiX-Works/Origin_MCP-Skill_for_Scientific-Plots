"""Offline checks of S2 adapters. Never import or attach to real originpro."""
from pathlib import Path
from types import SimpleNamespace
import sys
import re

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp" / "src"))

from origin_mcp.models import FigureSpec, FigureStyleSpec
from origin_mcp.tools import figurespec
from origin_mcp.client.graph_formatting_helpers import _GraphFormattingHelperMixin as Inspector
from origin_mcp.client.graph_formatting import _GraphFormattingMixin
from origin_mcp.errors import OriginOperationError


def spec(style, tmp_path):
    data_path = tmp_path / "synthetic.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    return FigureSpec.model_validate({
        "figure": {"id": "offline"},
        "data": [{"id": "d", "source": str(data_path), "roles": {"x": "x", "y": "y"}}],
        "layers": [{"id": "a", "data_ref": "d"}],
        "plots": [{"id": "p", "layer": "a", "type": "line_symbol", "map": {"x": "x", "y": "y"}}],
        "annotations": [{"id": "legend", "type": "legend", "layer": "a"}],
        "style": style,
    })


class StyleClient:
    def __init__(self):
        self.calls = []

    def apply_nature_style(self, **kwargs):
        self.calls.append(("nature", kwargs))
        return {"applied": True}

    def format_legend(self, **kwargs):
        self.calls.append(("legend", kwargs))
        return {"legend": True}

    def run_labtalk(self, script):
        self.calls.append(("text_only", script))
        return {"result": True}


def test_explicit_sizes_below_20_reach_existing_nature_and_legend(monkeypatch, tmp_path):
    style = {"theme": "nature", "font_family": "Arial", "axis_title_size": 10,
             "tick_label_size": 8, "legend_font_size": 9}
    figure = spec(style, tmp_path)
    fake = StyleClient()
    monkeypatch.setattr(figurespec, "client", fake)
    figurespec._apply_figure_typography(figure, "Graph1", {"a": 0}, figure.plots[0])
    figurespec._apply_annotations(figure, "Graph1", {"a": 0})
    nature = fake.calls[0][1]
    assert {k: nature[k] for k in style if k != "theme"} == {k: v for k, v in style.items() if k != "theme"}
    assert nature["chart_type"] == "line_symbol"
    assert nature["run_diagnostics"] is False
    assert fake.calls[1][1]["font_size"] == 9
    assert fake.calls[1][1]["font_family"] == "Arial"


@pytest.mark.parametrize("theme", ["nature", "origin_default", "template", "none"])
def test_absent_typography_preserves_existing_defaults(monkeypatch, theme, tmp_path):
    figure = spec({"theme": theme}, tmp_path)
    fake = StyleClient()
    monkeypatch.setattr(figurespec, "client", fake)
    assert figurespec._apply_figure_typography(figure, "Graph1", {"a": 0}, figure.plots[0]) == []
    assert fake.calls == []
    assert figure.style.axis_title_size is None
    assert figure.style.tick_label_size is None
    assert figure.style.legend_font_size is None


def test_non_nature_font_does_not_apply_nature_palette(monkeypatch, tmp_path):
    figure = spec({"theme": "template", "font_family": "Arial", "tick_label_size": 8}, tmp_path)
    fake = StyleClient()
    monkeypatch.setattr(figurespec, "client", fake)
    update = figurespec._apply_figure_typography(figure, "Graph1", {"a": 0}, figure.plots[0])
    assert [name for name, _ in fake.calls] == ["text_only"]
    assert update[0]["requested_typography"] == {"font_family": "Arial", "tick_label_size": 8}
    assert update[0]["size_unit"] == "pt"


@pytest.mark.parametrize("field", ["axis_title_size", "tick_label_size", "legend_font_size"])
def test_font_size_validation_is_positive_not_20_minimum(field):
    assert getattr(FigureStyleSpec.model_validate({field: 6}), field) == 6
    with pytest.raises(ValidationError):
        FigureStyleSpec.model_validate({field: 0})


class Properties:
    def __init__(self, values):
        self.values = values

    def get_float(self, prop):
        if prop not in self.values:
            raise RuntimeError("unsupported property")
        return self.values[prop]

    def set_float(self, prop, value):
        self.values[prop] = value

    def set_int(self, prop, value):
        self.values[prop] = value


def test_actual_dimensions_and_typography_are_read_from_objects():
    layer = Properties({"left": 12, "top": 10, "width": 74, "height": 79, "unit": 1,
                        "x.label.font": 16, "x.label.pt": 8})
    layer.label = lambda name: {"xb": Properties({"font": 16, "fsize": 10}),
                                "Legend": Properties({"font": 16, "fsize": 9})}.get(name)
    assert Inspector._geometry_readback(layer, page=False)["width"] == 74
    assert Inspector._geometry_readback(layer, page=False)["unit"] == "percent_of_page"
    typography = Inspector._typography_readback(layer)
    assert typography["x_axis_title"]["size"] == 10
    assert typography["x_tick_label"]["size"] == 8
    assert typography["legend"]["size"] == 9
    assert typography["legend"]["font_family"] is None
    assert typography["y_axis_title"]["status"] == "unavailable_or_partial"


def test_unsupported_or_invalid_readback_stays_unknown():
    unknown = Properties({"width": 0, "height": float("nan"), "x.label.font": 0, "x.label.pt": -1})
    geometry = Inspector._geometry_readback(unknown, page=True)
    assert geometry["width"] is None and geometry["height"] is None
    assert geometry["unit"] == "printer_dot"
    title = Inspector._typography_readback(unknown)["x_axis_title"]
    assert title["font_id"] is None and title["size"] is None
    assert title["font_family_status"] == "unavailable"


class RangeReader:
    """A tiny semantic LT mock: scratch vars change, source data never does."""
    def __init__(self, sources, rows=None):
        self.sources = sources
        self.rows = rows
        self.variables = {}

    def lt_exec(self, script):
        for command in script.split(";"):
            command = command.strip()
            if not command:
                continue
            match = re.fullmatch(r"range -w([xy]) (\w+) = (.+)", command)
            if match:
                self.variables[match[2]] = self.sources[match[1]]
                continue
            match = re.fullmatch(r"range (\w+) = (.+)", command)
            if match:
                self.variables[match[1]] = match[2]
                continue
            match = re.fullmatch(r"double (\w+) = -1", command)
            if match:
                self.variables[match[1]] = -1
                continue
            match = re.fullmatch(r"get (\w+) -([be]) (\w+)", command)
            if match:
                if self.rows is not None:
                    self.variables[match[3]] = self.rows[0 if match[2] == "b" else 1]
                continue
            match = re.fullmatch(r"string (\w+)\$ = %\((\w+)\)", command)
            if match:
                self.variables[match[1]] = self.variables[match[2]]
                continue
            match = re.fullmatch(r"del -(?:ra|al) (\w+)", command)
            if match:
                self.variables.pop(match[1], None)
                continue
            raise AssertionError(f"Unexpected command: {command}")
        return True

    def get_lt_str(self, variable):
        return self.variables[variable]

    def lt_float(self, variable):
        return self.variables[variable]


def read_binding(raw_x, raw_y, rows=None):
    fake = RangeReader({"x": raw_x, "y": raw_y}, rows=rows)
    inspector = Inspector()
    inspector._op = fake
    plot = SimpleNamespace(lt_range=lambda: "[Graph1]1!1")
    result = inspector._plot_data_binding(plot)
    assert fake.variables == {}
    assert fake.sources == {"x": raw_x, "y": raw_y}
    return result


def test_source_range_decodes_only_native_xy_range():
    binding = read_binding("[Book1]Sheet1!A[2:6]", "[Book1]Sheet1!B[2:6]")
    assert binding["worksheet"] == "[Book1]Sheet1"
    assert binding["x"] == {"worksheet": "[Book1]Sheet1", "column": "A", "row_range": [2, 6]}
    assert binding["y"] == {"worksheet": "[Book1]Sheet1", "column": "B", "row_range": [2, 6]}
    assert binding["row_index_base"] == 1
    assert binding["status"] == "available"


@pytest.mark.parametrize("raw", [None, "[Graph1]1!1", "unexpected", "[Book1]Sheet1!A[6:2]"])
def test_plot_address_or_unreadable_range_is_not_a_data_binding(raw):
    binding = read_binding(raw, raw)
    assert binding["status"] == "unavailable"
    assert binding["worksheet"] is None
    assert binding["x"] is None and binding["y"] is None
    assert binding["plot_range"] == "[Graph1]1!1"


def test_missing_range_rows_remain_explicitly_unknown():
    binding = read_binding("[Book1]Sheet1!A", "[Book1]Sheet1!B")
    assert binding["worksheet"] == "[Book1]Sheet1"
    assert binding["row_range"] is None
    assert binding["status"] == "partial"


@pytest.mark.parametrize("unit,width,height", [("inch", 90/25.4, 65/25.4), ("mm", 90, 65), ("cm", 9, 6.5)])
def test_page_size_converts_physical_dimensions_using_actual_resolution(unit, width, height):
    page = Properties({"width": 1, "height": 1, "resx": 600, "resy": 300, "kar": 0})
    client = _GraphFormattingMixin()
    client._find_or_active_graph = lambda name: page
    result = client.set_graph_page("Graph1", width=width, height=height, unit=unit)
    assert page.values["width"] == pytest.approx(90/25.4*600)
    assert page.values["height"] == pytest.approx(65/25.4*300)
    assert result["page_readback"]["physical_size_mm"] == pytest.approx({"width": 90, "height": 65})


def test_page_conversion_failure_does_not_partially_write_width():
    page = Properties({"width": 200, "height": 100, "resx": 600})
    client = _GraphFormattingMixin()
    client._find_or_active_graph = lambda name: page
    with pytest.raises(OriginOperationError):
        client.set_graph_page("Graph1", width=90, height=65, unit="mm")
    assert page.values == {"width": 200, "height": 100, "resx": 600}
    with pytest.raises(OriginOperationError):
        client.set_graph_page("Graph1", width=90, unit="pixel")


@pytest.mark.parametrize("rows", ["", "[2:6]"])
def test_live_range_format_includes_optional_column_display_name(rows):
    raw_x = '[Book2]Sheet1!A"Time (s)"' + rows
    raw_y = '[Book2]Sheet1!B"Response"' + rows
    binding = read_binding(raw_x, raw_y)
    assert binding["raw_data_ranges"] == {"x": raw_x, "y": raw_y}
    assert binding["x"]["column"] == "A"
    assert binding["x"]["long_name"] == "Time (s)"
    assert binding["y"]["column"] == "B"
    assert binding["worksheet"] == "[Book2]Sheet1"
    assert binding["row_range"] == ([2, 6] if rows else None)


class AspectLockedPage(Properties):
    def set_float(self, prop, value):
        if self.values["kar"] == 1 and prop in ("width", "height"):
            old_ratio = self.values["width"] / self.values["height"]
            other = "height" if prop == "width" else "width"
            self.values[other] = value / old_ratio if prop == "width" else value * old_ratio
        super().set_float(prop, value)


def test_two_explicit_dimensions_temporarily_unlock_and_restore_page_ratio():
    page = AspectLockedPage({"width": 2400, "height": 1700, "resx": 600, "resy": 600, "kar": 1})
    client = _GraphFormattingMixin()
    client._find_or_active_graph = lambda name: page
    result = client.set_graph_page("Graph1", width=90, height=65, unit="mm")
    assert result["page_readback"]["physical_size_mm"] == pytest.approx({"width": 90, "height": 65})
    assert page.values["kar"] == 1


def test_single_explicit_dimension_retains_existing_aspect_lock():
    page = AspectLockedPage({"width": 2400, "height": 1700, "resx": 600, "resy": 600, "kar": 1})
    client = _GraphFormattingMixin()
    client._find_or_active_graph = lambda name: page
    client.set_graph_page("Graph1", width=90, unit="mm")
    assert page.values["width"] / page.values["height"] == pytest.approx(2400 / 1700)
    assert page.values["kar"] == 1


def test_actual_graph_display_rows_are_read_when_source_range_omits_rows():
    binding = read_binding('[Book2]Sheet1!A"Time (s)"', '[Book2]Sheet1!B"Response"', rows=[1, 11])
    assert binding["row_range"] == [1, 11]
    assert binding["row_range_source"] == "LabTalk.get-graph-range-b-e"
    assert binding["status"] == "available"


@pytest.mark.parametrize("rows", [[0, 11], [6, 2], [1, float("nan")]])
def test_invalid_graph_display_rows_stay_unknown(rows):
    binding = read_binding("[Book2]Sheet1!A", "[Book2]Sheet1!B", rows=rows)
    assert binding["row_range"] is None
    assert binding["status"] == "partial"
