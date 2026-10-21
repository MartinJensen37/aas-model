"""TimeSeries SMC — the DMP profile of IDTA 02008 (Time Series Data 1.1).

Layering: the generated IDTA template
(``aas_pydantic.submodel_templates.time_series``) stays PRISTINE. This module
shapes one time series as an SMC inside ``Variables`` instead of a submodel of
its own: the SMC carries this project's id with the IDTA TimeSeries id as a
supplemental id, and everything inside it keeps the IDTA ids, so splitting it
out into a TimeSeries submodel stays mechanical.

Structure::

    <series>                     TimeSeriesCollection (TS_COLLECTION + IDTA TimeSeries)
    ├── Metadata
    │   ├── Name
    │   └── Record               the row schema: one row = one sample
    │       ├── Time             UtcTime (xs:dateTime)
    │       ├── <field>          RecordField, its InfluxDB column in a Column qualifier
    │       └── <group>          RecordGroup of further fields
    └── Segments
        └── LinkedSegment[]
            ├── Endpoint         InfluxDB 2 query URL (IDTA)
            ├── Query            Flux for the web UI (IDTA)
            └── DmpTarget        Bucket, Measurement, Tags (DMP extension)

A series groups what is sampled together, never one variable each. The DMP
addresses the LinkedSegment; it reads the Record as the row shape and writes or
reads one point per row. Nothing is derived from names: every field declares its
column, and the tags name the AAS that owns the series (``{aas_id_short}``,
resolved when the resource is built).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Union

from pydantic import model_validator

from aas_pydantic import Operation, Property, Qualifier, SubmodelElementCollection
from aas_pydantic.aas_model import AasIdString, DynamicSubmodelElementCollection
from aas_pydantic.submodel_templates.time_series import (
    Endpoint, LinkedSegment as _LinkedSegment, Metadata as _Metadata, Name,
    Query, Segments as _Segments, State,
)

from aas_model.constants import (
    INFLUX_BUCKET, INFLUX_ORG, INFLUX_ORIGIN,
    TS_COLLECTION, TS_COLUMN, TS_DMP_TARGET, TS_DMP_TARGET_BUCKET,
    TS_DMP_TARGET_MEASUREMENT, TS_DMP_TARGET_TAG, TS_DMP_TARGET_TAGS,
    TS_RECORD_FIELD, TS_RECORD_GROUP,
)

IDTA_TIME_SERIES = "https://admin-shell.io/idta/TimeSeries/1/1"
IDTA_RECORD = "https://admin-shell.io/idta/TimeSeries/Record/1/1"
IDTA_UTC_TIME = "https://admin-shell.io/idta/TimeSeries/UtcTime/1/1"

# Measurement names, tag keys and values are spliced into Flux string literals.
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.\-{}]+$")


# ── Record ───────────────────────────────────────────────────────────────────

class Column(Qualifier):
    """The InfluxDB field a Record field is stored in. Authored explicitly and
    kept when the field is renamed, so a rename never splits its history."""
    type_: str = "Column"
    semantic_id: str = TS_COLUMN
    kind: str = "ConceptQualifier"


class UtcTime(Property):
    """The row's time. A value the transformation returns is the point's time;
    without one the DMP stamps the time of evaluation."""
    id_short: AasIdString = "Time"
    semantic_id: str = IDTA_UTC_TIME
    value_type: str = "xs:dateTime"


class RecordField(Property):
    """One column of the row. The concept it measures rides as a supplemental
    semantic id, as on a ``VariableProp``."""
    semantic_id: str = TS_RECORD_FIELD

    @model_validator(mode="after")
    def _one_column(self):
        columns = [q for q in self.qualifiers if q.type_ == "Column"]
        if len(columns) != 1 or not columns[0].value:
            raise ValueError(f"Record field {self.id_short!r} needs exactly one Column")
        return self

    @property
    def column(self) -> str:
        return next(q.value for q in self.qualifiers if q.type_ == "Column")


class RecordGroup(SubmodelElementCollection):
    """Fields that belong together within a row (``Position.X``)."""
    semantic_id: str = TS_RECORD_GROUP
    field: Dict[str, "RecordEntry"] = {}


RecordEntry = Union[RecordField, RecordGroup]


def _columns(fields: Dict[str, RecordEntry]) -> List[str]:
    out: List[str] = []
    for entry in fields.values():
        out.extend(_columns(entry.field) if isinstance(entry, RecordGroup) else [entry.column])
    return out


class TimeSeriesRecord(SubmodelElementCollection):
    id_short: AasIdString = "Record"
    semantic_id: str = IDTA_RECORD
    Time: UtcTime = UtcTime()
    field: Dict[str, RecordEntry] = {}

    @model_validator(mode="after")
    def _distinct_columns(self):
        if "Time" in self.field:
            raise ValueError("'Time' is the row's time, not a field")
        columns = _columns(self.field)
        duplicates = sorted({c for c in columns if columns.count(c) > 1})
        if duplicates:
            raise ValueError(f"Record columns are not distinct: {duplicates}")
        return self


class TimeSeriesMetadata(_Metadata):
    Record: TimeSeriesRecord


# ── LinkedSegment write target (DMP extension) ───────────────────────────────

class Bucket(Property):
    id_short: AasIdString = "Bucket"
    semantic_id: str = TS_DMP_TARGET_BUCKET


class Measurement(Property):
    id_short: AasIdString = "Measurement"
    semantic_id: str = TS_DMP_TARGET_MEASUREMENT


class Tag(Property):
    """One series tag: the idShort is the tag key, the value its value."""
    semantic_id: str = TS_DMP_TARGET_TAG


class Tags(SubmodelElementCollection):
    id_short: AasIdString = "Tags"
    semantic_id: str = TS_DMP_TARGET_TAGS
    tag: Dict[str, Tag] = {}


class DmpTarget(SubmodelElementCollection):
    """Where the DMP writes and reads the segment's points. The IDTA Query is
    for people and the web UI; the DMP never parses it."""
    id_short: AasIdString = "DmpTarget"
    semantic_id: str = TS_DMP_TARGET
    Bucket: Bucket
    Measurement: Measurement
    Tags: Tags


class DmpLinkedSegment(_LinkedSegment):
    DmpTarget: DmpTarget


class TimeSeriesSegments(_Segments):
    LinkedSegment: Dict[str, DmpLinkedSegment] = {}


class TimeSeriesCollection(SubmodelElementCollection):
    semantic_id: str = TS_COLLECTION
    supplemental_semantic_ids: List[str] = [IDTA_TIME_SERIES]
    Metadata: TimeSeriesMetadata
    Segments: TimeSeriesSegments


RecordGroup.model_rebuild()
TimeSeriesRecord.model_rebuild()


# ── Authoring helpers ────────────────────────────────────────────────────────

def record_field(value_type: str, *, column: str, concept: str = "",
                 description: str = "") -> RecordField:
    """A Record field stored in *column*. The column is always explicit."""
    return RecordField(
        value_type=value_type, description=description,
        supplemental_semantic_ids=[concept] if concept else [],
        qualifiers=[Column(value=column)],
    )


def record_group(fields: Dict[str, RecordEntry], *, description: str = "") -> RecordGroup:
    return RecordGroup(field=fields, description=description)


def _check_identifier(kind: str, value: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"{kind} {value!r} must match {_IDENTIFIER.pattern}")
    return value


def flux_query(bucket: str, measurement: str, tags: Dict[str, str]) -> str:
    """The segment's Query: its points in the web UI's time range, one field
    per selected Record field (``{{y-value}}``, substituted by the UI)."""
    lines = [
        f'from(bucket: "{bucket}")',
        "  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)",
        f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")',
        *(f'  |> filter(fn: (r) => r["{key}"] == "{value}")' for key, value in tags.items()),
        '  |> filter(fn: (r) => r["_field"] == "{{y-value}}")',
    ]
    return "\n".join(lines)


def linked_segment(*, measurement: str, tags: Dict[str, str],
                   bucket: str = INFLUX_BUCKET, description: str = "") -> DmpLinkedSegment:
    """An open-ended segment on the workspace's InfluxDB."""
    _check_identifier("bucket", bucket)
    _check_identifier("measurement", measurement)
    for key, value in tags.items():
        _check_identifier("tag key", key)
        _check_identifier("tag value", value)
    return DmpLinkedSegment(
        description=description,
        State=State(value="InProgress"),
        Endpoint=Endpoint(value=f"{INFLUX_ORIGIN}/api/v2/query?org={INFLUX_ORG}"),
        Query=Query(value=flux_query(bucket, measurement, tags)),
        DmpTarget=DmpTarget(
            Bucket=Bucket(value=bucket),
            Measurement=Measurement(value=measurement),
            Tags=Tags(tag={key: Tag(value=value) for key, value in tags.items()}),
        ),
    )


def time_series(*, name: str, measurement: str, fields: Dict[str, RecordEntry],
                tags: Optional[Dict[str, str]] = None, description: str = "",
                segment: str = "Live") -> TimeSeriesCollection:
    """A series with one LinkedSegment. *tags* default to the owning AAS."""
    tags = {"asset": "{aas_id_short}"} if tags is None else tags
    return TimeSeriesCollection(
        description=description,
        Metadata=TimeSeriesMetadata(
            Name=Name(value={"en": name}),
            Record=TimeSeriesRecord(field=fields),
        ),
        Segments=TimeSeriesSegments(LinkedSegment={
            segment: linked_segment(measurement=measurement, tags=tags),
        }),
    )


def _operation_fields(variables) -> Dict[str, RecordEntry]:
    fields: Dict[str, RecordEntry] = {}
    for variable in variables:
        if isinstance(variable, Property):
            entry: RecordEntry = record_field(
                variable.value_type, column=variable.id_short,
                concept=variable.semantic_id, description=variable.description,
            )
        elif isinstance(variable, DynamicSubmodelElementCollection):
            entry = record_group(_operation_fields(variable.value.values()),
                                 description=variable.description)
        else:
            raise ValueError(
                f"Operation variable {variable.id_short!r} ({type(variable).__name__}) "
                "has no Record column form"
            )
        fields[variable.id_short] = entry
    return fields


def operation_log(operation: Operation, *, name: str, measurement: str) -> TimeSeriesCollection:
    """A typed log series of one Operation: its outcome and duration next to its
    input, InOut and output variables, which keep their valueTypes."""
    fields: Dict[str, RecordEntry] = {
        "Outcome": record_field("xs:string", column="Outcome",
                                description="How the invocation ended"),
        "DurationMs": record_field("xs:long", column="DurationMs",
                                   description="Time from accepting the call to its answer"),
    }
    for variable_fields in (
        _operation_fields(operation.input_variable),
        _operation_fields(operation.in_output_variable),
        _operation_fields(operation.output_variable),
    ):
        clash = sorted(set(fields) & set(variable_fields))
        if clash:
            raise ValueError(f"Operation variables clash with log fields: {clash}")
        fields.update(variable_fields)
    return time_series(name=name, measurement=measurement, fields=fields)
