"""TimeSeries SMCs in Variables — the DMP profile of IDTA 02008.

These tests drive the production path (Python Resource -> exported JSON ->
Pydantic -> BaSyx), as the registration service builds a resource.
"""

from __future__ import annotations

import pytest
from basyx.aas.model import datatypes

from aas_pydantic import Operation, Property
from aas_model import Resource, build_from_model
from aas_model.submodel_templates.time_series import (
    IDTA_TIME_SERIES, RecordField, TimeSeriesRecord, linked_segment, operation_log,
    record_field, record_group, time_series,
)
from aas_model.submodel_templates.variables import (
    LogGroup, MeasurementsGroup, StateGroup, Variables,
)


CONCEPT = "https://w3id.org/2026/apex/semantic/state/operational"


def _station_state():
    return time_series(name="Station state", measurement="station_state", fields={
        "PackMLState": record_field("xs:string", column="PackMLState", concept=CONCEPT),
        "Position": record_group({"X": record_field("xs:double", column="Position.X")}),
    })


def _publish(variables: Variables) -> dict:
    asset = Resource(id_short="seriesTestAAS", variables=variables)
    restored = Resource.model_validate_json(asset.model_dump_json())
    sm = {s.id_short: s for s in build_from_model(restored)}["Variables"]
    return {e.id_short: e for e in sm.submodel_element}


def _children(element) -> dict:
    return {c.id_short: c for c in element.value}


def _semantic_id(element) -> str:
    return element.semantic_id.key[0].value


def _series():
    variables = Variables(id_short="Variables", State=StateGroup(value={"Station": _station_state()}))
    return _children(_publish(variables)["State"])["Station"]


def test_groups_appear_only_when_authored():
    assert set(_publish(Variables(id_short="Variables"))) == set()
    groups = _publish(Variables(
        id_short="Variables", State=StateGroup(), Measurements=MeasurementsGroup(), Log=LogGroup(),
    ))
    assert set(groups) == {"State", "Measurements", "Log"}


def test_series_round_trips_through_rest_json():
    from aas_model._serde import parse_submodel_dict
    from basyx.aas.adapter.json import json_serialization
    import json

    variables = Variables(id_short="Variables", id="urn:sm:Variables",
                          State=StateGroup(value={"Station": _station_state()}))
    asset = Resource(id_short="seriesTestAAS", variables=variables)
    sm = {s.id_short: s for s in build_from_model(asset)}["Variables"]
    rest = json.loads(json.dumps(sm, cls=json_serialization.AASToJsonEncoder))
    back = parse_submodel_dict(rest, Variables)
    series = back.State.value["Station"]
    assert type(series).__name__ == "TimeSeriesCollection"
    fields = series.Metadata.Record.field
    assert fields["PackMLState"].column == "PackMLState"
    assert fields["PackMLState"].supplemental_semantic_ids == [CONCEPT]
    assert fields["Position"].field["X"].column == "Position.X"
    target = series.Segments.LinkedSegment["Live"].InfluxDb2Target
    assert target.Measurement.value == "station_state"
    assert target.Tags.tag["asset"].value == "seriesTestAAS"


def test_series_is_an_smc_with_the_idta_id_as_supplemental():
    series = _series()
    assert type(series).__name__ == "SubmodelElementCollection"
    assert [k.value for s in series.supplemental_semantic_id for k in s.key] == [IDTA_TIME_SERIES]
    assert set(_children(series)) == {"Metadata", "Segments"}


def test_record_holds_the_row_shape_with_explicit_columns():
    record = _children(_children(_series())["Metadata"])["Record"]
    fields = _children(record)
    assert _semantic_id(fields["Time"]) == "https://admin-shell.io/idta/TimeSeries/UtcTime/1/1"
    assert fields["Time"].value_type is datatypes.DateTime
    assert [(q.type, q.value) for q in fields["PackMLState"].qualifier] == [("Column", "PackMLState")]
    position = _children(fields["Position"])
    assert [(q.type, q.value) for q in position["X"].qualifier] == [("Column", "Position.X")]


def test_linked_segment_names_its_target_and_the_owning_aas():
    live = _children(_children(_series())["Segments"])["Live"]
    parts = _children(live)
    assert parts["Endpoint"].value == "http://influxdb:8086/api/v2/query?org=ap2030"
    assert parts["State"].value == "InProgress"
    target = _children(parts["InfluxDb2Target"])
    assert target["Bucket"].value == "ap2030"
    assert target["Measurement"].value == "station_state"
    assert {t.id_short: t.value for t in target["Tags"].value} == {"asset": "seriesTestAAS"}
    query = parts["Query"].value
    assert 'r["_measurement"] == "station_state"' in query
    assert 'r["asset"] == "seriesTestAAS"' in query
    assert '{{y-value}}' in query


def test_a_segment_with_an_end_time_is_completed_and_without_one_in_progress():
    live = linked_segment(measurement="m", tags={}, start_time="2026-10-20T00:00:00Z")
    assert (live.StartTime.value, live.EndTime, live.State.value) == ("2026-10-20T00:00:00Z", None, "InProgress")
    batch = linked_segment(measurement="m", tags={}, start_time="2026-10-20T00:00:00Z",
                           end_time="2026-10-20T08:00:00+02:00")
    assert (batch.EndTime.value, batch.State.value) == ("2026-10-20T08:00:00+02:00", "Completed")


@pytest.mark.parametrize("times", [
    {"start_time": "yesterday"},
    {"start_time": "2026-10-20T00:00:00"},
    {"start_time": "2026-10-20T08:00:00Z", "end_time": "2026-10-20T07:00:00Z"},
])
def test_segment_times_are_offset_date_times_in_order(times):
    with pytest.raises(ValueError):
        linked_segment(measurement="m", tags={}, **times)


def test_a_record_field_without_a_column_is_rejected():
    with pytest.raises(Exception, match="Column"):
        RecordField(id_short="PackMLState")


def test_columns_must_be_distinct_across_groups():
    with pytest.raises(Exception, match="not distinct"):
        TimeSeriesRecord(field={
            "A": record_field("xs:string", column="Same"),
            "G": record_group({"B": record_field("xs:string", column="Same")}),
        })


def test_time_is_not_a_field():
    with pytest.raises(Exception, match="Time"):
        TimeSeriesRecord(field={"Time": record_field("xs:dateTime", column="Time")})


def test_identifiers_spliced_into_flux_are_checked():
    with pytest.raises(ValueError, match="measurement"):
        linked_segment(measurement='bad"name', tags={})


def test_operation_log_keeps_the_variables_types():
    operation = Operation(
        id_short="operation",
        input_variable=[Property(id_short="Weight", value_type="xs:double")],
        in_output_variable=[Property(id_short="Uuid")],
        output_variable=[Property(id_short="State")],
    )
    log = operation_log(operation, name="Occupy", measurement="operation_occupy")
    fields = log.Metadata.Record.field
    assert list(fields) == ["Outcome", "DurationMs", "Weight", "Uuid", "State"]
    assert fields["DurationMs"].value_type == "xs:long"
    assert fields["Weight"].value_type == "xs:double"
    assert fields["Uuid"].column == "Uuid"


def test_operation_log_rejects_a_variable_clashing_with_a_log_field():
    operation = Operation(id_short="operation", output_variable=[Property(id_short="Outcome")])
    with pytest.raises(ValueError, match="clash"):
        operation_log(operation, name="Occupy", measurement="operation_occupy")
