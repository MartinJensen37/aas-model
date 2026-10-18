#!/usr/bin/env python3
"""Generate aas_pydantic models from IDTA submodel template JSON.

Emits named-field pydantic models from IDTA templates:

    Submodel:  ManufacturerName: ManufacturerName
    SMC:       InterfaceTemplateForMQTT: InterfaceTemplateForMQTT
    SML:       value: List[Item]

Container children are emitted as direct fields using their idShort spelling.
Required and optional fields follow SMT/Cardinality; multi-cardinality
elements become dynamic name-keyed maps, while SubmodelElementLists retain
their list behavior. IDTA example children define the class metadata, including
semantic_id, description, value_type, and supplemental semantic IDs.
"""

import json
import keyword
import os
import re
import sys

# modelType → Python type name
ELEMENT_MAP = {
    "Property": "Property",
    "MultiLanguageProperty": "MultiLanguageProperty",
    "Range": "Range",
    "ReferenceElement": "ReferenceElement",
    "RelationshipElement": "RelationshipElement",
    "File": "File",
    "Blob": "Blob",
    "Capability": "Capability",
    "Operation": "Operation",
}


def safe_name(name: str) -> str:
    # IDTA placeholders like ``Mode__00__`` mean "a repeatable instance whose
    # id_short the user picks" — strip the ``__NN__`` suffix so class and field
    # names are the clean base name (``Mode`` → field ``mode``).
    name = re.sub(r"__\d+__$", "", name or "")
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


_CONCRETE_ID_SHORT = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def id_short_default(el: dict) -> list:
    """The class-level ``id_short`` default: the template's idShort when it is
    a concrete name. Placeholders (``{property_name}``, ``Mode__00__``) and
    missing idShorts (SML items) get none, since the instance name is chosen
    by the author (a dict key or a list position)."""
    raw = el.get("idShort") or ""
    if not _CONCRETE_ID_SHORT.fullmatch(raw) or re.search(r"__\d+__$", raw):
        return []
    return [f"    id_short: AasIdString = {json.dumps(raw)}"]


def snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return s.replace("-", "_").lower()


def field_name(name: str) -> str:
    """Preserve idShort spelling while producing a valid Python identifier.

    IDTA ``__NN__`` placeholder suffixes are stripped; invalid characters are
    replaced with underscores and Python keywords receive a trailing underscore.
    """
    name = re.sub(r"__\d+__$", "", name or "")
    s = safe_name(name)
    if s and s[0].isdigit():
        s = f"_{s}"
    if keyword.iskeyword(s):
        s += "_"
    return s


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_ROOT = os.path.join(_ROOT, "submodel-templates", "published")
OUTPUT_ROOT = os.path.join(_ROOT, "src", "aas_pydantic", "submodel_templates")
TEMPLATES = (
    "Capability Description/1/0/1/IDTA 02020_Template_Capability_Description.json",
    "Control Component Instance/2/0/1/IDTA 02016-2-0-1 _Template_ControlComponentInstance_forAASMetamodelV3.1.json",
    "Control Component Type/2/0/2/IDTA 02015-2-0-2 _Template_ControlComponentType_forAASMetamodelV3.1.json",
    "Hierarchical Structures enabling Bills of Material/1/1/2/IDTA 02011-1-1-2_Template_HSEBoM_forAASMetamodelV3.1.json",
    "Digital nameplate/3/0/2/IDTA 02006-3-0-2_Template_Digital Nameplate.json",
    "Asset Interfaces Mapping Configuration/2/1/IDTA 02027_Template_AIMC.json",
    "Asset Interfaces Description/1/2/IDTA 02017_Template_Asset Interfaces Description.json",
    "Time Series Data/1/1/2/IDTA 02008-1-1-2_Template_TimeSeriesData_forAASMetamodelV3.1.json",
)


def to_camel(name: str) -> str:
    """CamelCase a (snake_case) id_short for a dedicated leaf class name:
    ``year_of_construction`` → ``YearOfConstruction``, ``u_r_i_of_the_product``
    → ``URIOfTheProduct``.  The class name therefore never equals the
    snake_case field name (pydantic rejects field==annotation self-refs), and
    each element's template defaults live on its own named class."""
    parts = re.split(r"[^0-9a-zA-Z]+", name or "")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def sid_namespace_suffix(base_name: str, sid: str) -> str:
    """Readable disambiguation suffix for a class whose id_short collides with
    another element of a *different* semanticId (e.g. AID's nested object-
    schema ``properties`` / ``property_name`` under ``json-schema#properties``
    / ``json-schema#propertyName``).  Prefers the semanticId fragment when it
    differs from the id_short (``json-schema#propertyName`` →
    ``property_name_json_schema``); otherwise uses the last namespace path
    segment (``.../ControlComponent/Skill/Errors/2/0`` → ``Errors_skill``)."""
    frag = sid.split("#")[-1] if "#" in sid else ""
    path = [p for p in sid.split("#")[0].split("/") if p and not p.isdigit()]
    if frag and snake(frag) != snake(base_name):
        return snake(frag)
    ns = path if frag else (path[:-1] if path else [])
    return snake(ns[-1]) if ns else ""


_DICT_CLASH_RE = re.compile(r"^    (\w+): Dict\[str, (\w+)\] = (?:\{\}|Field\()")
_OPT_CLASH_RE = re.compile(r"^    (\w+): Optional\[(\w+)\] = None$")
_REQUIRED_CLASH_RE = re.compile(r"^    (\w+): (\w+)$")
_FIELD_LINE_RE = re.compile(r"^    (\w+): (.+?)(?: = (.*))?$")


def _parse_field_line(line: str):
    match = _FIELD_LINE_RE.match(line)
    if not match:
        return None
    field_name, annotation, default = match.groups()
    optional = annotation.startswith("Optional[") and annotation.endswith("]")
    core = annotation[9:-1] if optional else annotation
    shape = "map" if core.startswith("Dict[") else (
        "list" if core.startswith("List[") else "single"
    )
    required = shape == "single" and not optional and (
        default is None or default.startswith("Field(json_schema_extra=")
    )
    return field_name, core, shape, required, default


def _merge_field_bodies(class_name: str, bodies: list, compatible=None) -> list:
    """Merge repeated definitions of one semantic container concept.

    Fields present in every variant stay required only when they are required
    in every variant. Dynamic maps and list fields keep their empty-container
    defaults when absent from another variant. Conflicting field types or
    repeatable defaults are rejected instead of silently choosing one variant.
    """
    variants = []
    field_order = []
    for body in bodies:
        fields = {}
        for line in body:
            parsed = _parse_field_line(line)
            if parsed is None:
                continue
            field, core, shape, required, default = parsed
            if field in fields:
                raise ValueError(f"Duplicate field {class_name}.{field}")
            fields[field] = (core, shape, required, default)
            if field not in field_order:
                field_order.append(field)
        variants.append(fields)

    merged = []
    for field in field_order:
        definitions = [variant[field] for variant in variants if field in variant]
        core, shape, _, default = definitions[0]
        cores = list(dict.fromkeys(definition[0] for definition in definitions))
        if any(definition[1] != shape for definition in definitions) or (
            len(cores) > 1 and (
                shape != "single" or compatible is None or
                not all(compatible(cores[0], candidate) for candidate in cores[1:])
            )
        ):
            raise ValueError(
                f"Incompatible field types for {class_name}.{field}: "
                f"{', '.join(sorted(cores))}"
            )
        if len(cores) > 1:
            members = []
            for candidate in cores:
                type_members = (candidate[6:-1].split(", ") if candidate.startswith("Union[")
                                and candidate.endswith("]") else [candidate])
                members.extend(member for member in type_members if member not in members)
            core = f"Union[{', '.join(members)}]"
        if shape in ("map", "list"):
            defaults = {definition[3] for definition in definitions}
            if len(defaults) != 1:
                raise ValueError(
                    f"Incompatible repeatable defaults for {class_name}.{field}"
                )
            merged.append(f"    {field}: {core} = {default}")
            continue

        required_everywhere = (
            len(definitions) == len(variants)
            and all(definition[2] for definition in definitions)
        )
        extra = ""
        if default and "json_schema_extra=" in default:
            extra = default.split("json_schema_extra=", 1)[1].rsplit(")", 1)[0]
        if required_everywhere:
            merged.append(
                f"    {field}: {core} = Field(json_schema_extra={extra})"
                if extra else f"    {field}: {core}"
            )
        else:
            merged.append(
                f"    {field}: Optional[{core}] = Field(default=None, json_schema_extra={extra})"
                if extra else f"    {field}: Optional[{core}] = None"
            )
    return merged or ["    pass"]


def _rewrite_clash_fields(body: list, aliases_emitted: set):
    """Alias names where a field would shadow its annotated element class.

    The type is aliased as a ``TypeAlias`` (``security_t: TypeAlias =
    security``) emitted once after class definitions. Postponed annotations
    allow a shared or recursive container class to be declared later."""
    new_body = []
    alias_lines = []
    for line in body:
        m = _DICT_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(f"Dict[str, {t}]", f"Dict[str, {alias}]"))
            continue
        # optional single-cardinality child whose field name equals its type
        # annotation (``enum: Optional[enum] = None``) — pydantic resolves the
        # self-referential name to NoneType, silently dropping the child.
        m = _OPT_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: Optional[{t}] = None",
                f"{t}: Optional[{alias}] = None",
            ))
            continue
        # required (no-default) single-cardinality child whose field name equals
        # its type annotation (``forms: forms``) — same self-reference clash,
        # same alias fix.
        m = _REQUIRED_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: {t}",
                f"{t}: {alias}",
            ))
            continue
        new_body.append(line)
    return new_body, alias_lines


def extract_semantic_id(el: dict) -> str:
    sem = el.get("semanticId") or {}
    for k in sem.get("keys", []) or []:
        if k.get("value"):
            return k.get("value", "")
    return ""


def extract_supplemental_semantic_ids(el: dict) -> list:
    """Supplemental semanticIds (list of IRIs) from ``supplementalSemanticIds``.
    These disambiguate elements that share a main semanticId — e.g. the AID
    ``InterfaceTemplateFor*`` all use ``.../Interface`` but each protocol has a
    unique supplemental IRI (per the IDTA PDF; the published JSON had OPC UA /
    BACnet copy-pasted from MQTT and is patched in the vendored copy)."""
    out = []
    for s in (el.get("supplementalSemanticIds") or []):
        for k in (s.get("keys") or []):
            if k.get("value"):
                out.append(k["value"])
    return out


def extract_description(el: dict) -> str:
    d = el.get("description")
    if isinstance(d, list):  # AAS JSON: [{"language": "en", "text": "..."}]
        return d[0].get("text", "") if d else ""
    if isinstance(d, dict):
        texts = d.get("texts") or []
        return texts[0].get("text", "") if texts else ""
    return ""


def extract_value_type(el: dict) -> str:
    return el.get("valueType", "")


def metadata_lines(el: dict, *, include_empty_semantic_id: bool = True) -> list:
    """Class defaults common to leaves, containers, and list wrappers."""
    lines = id_short_default(el)
    sid = extract_semantic_id(el)
    if sid or include_empty_semantic_id:
        lines.append(f'    semantic_id: str = {json.dumps(sid)}')
    desc = extract_description(el)
    if desc:
        lines.append(f'    description: str = {json.dumps(desc)}')
    supp = extract_supplemental_semantic_ids(el)
    if supp:
        lines.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
    return lines


def extract_cardinality(el: dict) -> str:
    """Cardinality qualifier value (e.g. ``ZeroToMany``, ``ZeroToOne``, ``One``)
    — how many instances of this element a container may hold.

    Templates encode it under the standard qualifier ``type``
    ``SMT/Cardinality``."""
    for q in (el.get("qualifiers") or []):
        if q.get("type") == "SMT/Cardinality":
            return (q.get("value") or "").strip()
    return ""


# Cardinalities that allow more than one instance of an element → the
# values model field becomes a dynamic ``Dict[str, Element]`` (name-keyed),
# so MANY instances are possible — exactly like the pre-values-model dicts.
_MULTI_CARDINALITY = {
    "ZeroToMany", "OneToMany",  # standard SMT encodings
    "TwoToMany", "Three",       # other >1 encodings in the wild
    "Recursive",                # recursive structures allow unbounded nesting
}


def emit_reference(ref: dict, indent: str) -> list:
    """Source lines constructing a pydantic Reference from an AAS JSON
    reference dict (``{"type": ..., "keys": [...]}``)."""
    cls = "ModelReference" if ref.get("type") == "ModelReference" else "ExternalReference"
    key_src = [
        f'{indent}        Key(type_={json.dumps(k.get("type", ""))}, '
        f'value={json.dumps(k.get("value", ""))}),'
        for k in (ref.get("keys") or [])
    ]
    lines = [f"{indent}{cls}("]
    if key_src:
        lines.append(f"{indent}    key=(")
        lines.extend(key_src)
        lines.append(f"{indent}    ),")
    lines.append(f"{indent})")
    return lines


def is_placeholder_endpoint(ref) -> bool:
    """True when a RelationshipElement endpoint is a template placeholder.

    Several templates (e.g. HSEM ``SameAs``) declare ``first``/``second`` as a
    ``ModelReference`` whose only key is a ``GlobalReference`` "EMPTY" — a
    ModelReference's FIRST key must be an Identifiable (AASd-123), so such
    endpoints carry no real target and would make the generated class fail
    validation at import.  Skip them (endpoints stay unset/None).
    """
    if not isinstance(ref, dict):
        return True
    if ref.get("type") == "ModelReference":
        keys = ref.get("keys") or []
        if keys and keys[0].get("type") == "GlobalReference":
            return True
    return False


def children_of(el: dict) -> list:
    return [
        c
        for c in (el.get("submodelElements") or el.get("value")
                  or el.get("statements") or [])
        if isinstance(c, dict)
    ]


_RESERVED_FIELDS = {
    "id", "id_short", "description", "display_name", "semantic_id",
    "supplemental_semantic_ids", "qualifiers", "entity_type", "global_asset_id",
    "type_value_list_element", "value_type_list_element",
    "semantic_id_list_element", "order_relevant", "value",
}


def _annotate_field(line: str, raw: str, minimum: int = 0) -> str:
    """Retain AAS names and repeated-field cardinality without renaming fields."""
    parsed = _FIELD_LINE_RE.match(line)
    renamed = field_name(raw) != raw and not re.search(r"__\d+__$", raw)
    if not parsed or (not renamed and not minimum):
        return line
    field, ann, default = parsed.groups()
    entries = []
    if renamed:
        entries.append(f'"aas_id_short": {json.dumps(raw)}')
    if minimum:
        entries.append(f'"idta_min_cardinality": {minimum}')
    extra = "{" + ", ".join(entries) + "}"
    if default == "{}":
        return f"    {field}: {ann} = Field(default_factory=dict, json_schema_extra={extra})"
    if default is None:
        return f"    {field}: {ann} = Field(json_schema_extra={extra})"
    return f"    {field}: {ann} = Field(default={default}, json_schema_extra={extra})"


def gen_template(template_path: str, output_dir: str):
    with open(template_path) as f:
        data = json.load(f)
    submodels = data.get("submodels", [])
    if not submodels:
        print(f"No submodels in {template_path}")
        return
    sm = submodels[0]
    sm_name = safe_name(sm["idShort"])

    # ── SemanticId-aware class naming ──
    # IDTA templates may use one id_short for several distinct element types
    # distinguished by semanticId (AID: ``properties`` = td#PropertyAffordance
    # vs json-schema#properties; ``property_name`` = PropertyDefinition vs
    # json-schema#propertyName; CCT: Type/Errors vs Skill/Errors).  The first
    # occurrence in document order keeps the plain class name (so every
    # top-level name stays stable — subclasses like mqtt_aid.py keep working);
    # later occurrences with a different semanticId get a disambiguated name
    # via :func:`sid_namespace_suffix`.  All template detail is preserved: the
    # id_short stays the field name and default instance id_short, and each
    # distinct semanticId lives on its own class.
    primary_sid = {}

    def _prescan_primary(el):
        if not isinstance(el, dict):
            return
        nm = safe_name(el.get("idShort", ""))
        if nm and el.get("modelType") in (
            "Submodel", "SubmodelElementCollection", "Entity", "SubmodelElementList",
        ):
            s = extract_semantic_id(el)
            if s and nm not in primary_sid:
                primary_sid[nm] = s
        for c in children_of(el):
            _prescan_primary(c)

    _prescan_primary(sm)

    # resolved class name → (base id_short, semanticId); guards uniqueness
    _name_identity = {}

    def check_class_name(name: str) -> None:
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"Invalid class name from template idShort: {name!r}")

    def resolve_class_name(base: str, sid: str) -> str:
        """Class name for an element with id_short *base* and semanticId *sid*:
        plain name for the primary (document-first) occurrence, disambiguated
        otherwise.  Deterministic — the same (base, sid) always resolves to the
        same name, so recursion-stack lookups and definitions agree."""
        if sid == primary_sid.get(base, sid):
            cand = base
        else:
            suf = sid_namespace_suffix(base, sid)
            cand = f"{base}_{suf}" if suf else base
        i = 2
        c = cand
        while c in _name_identity and _name_identity[c] != (base, sid):
            c = f"{cand}_{i}"
            i += 1
        _name_identity.setdefault(c, (base, sid))
        return c

    # name → (meta_lines, body_lines); order of definition
    classes = {}
    class_body_variants = {}
    order = []
    entity_classes = set()
    sml_classes = set()
    leaf_bases = {}  # dedicated leaf element class name → base (leaf) class name
    leaf_identities = {}  # full definition (including metadata) → class name
    base_aliases = set()
    _used_leaf_types = {
        "Submodel", "SubmodelElement", "SubmodelElementCollection",
        "SubmodelElementList",
    }

    def register(name, meta, body, is_entity=False, is_sml=False):
        if name in leaf_bases or (
            name in classes and (is_entity != (name in entity_classes) or
                                 is_sml != (name in sml_classes))
        ):
            raise ValueError(f"Conflicting element types for generated class {name}")
        if name not in classes:
            classes[name] = (meta, body)
            class_body_variants[name] = [body]
            order.append(name)
        else:
            class_body_variants[name].append(body)
            classes[name] = (
                classes[name][0],
                _merge_field_bodies(
                    name, class_body_variants[name],
                    compatible=lambda a, b: all(
                        member in leaf_bases and other in leaf_bases and
                        leaf_bases[member] == leaf_bases[other] and
                        _name_identity.get(member) == _name_identity.get(other)
                        for member in _leaf_members(a)
                        for other in _leaf_members(b)
                    ),
                ),
            )
        if is_entity:
            entity_classes.add(name)
        if is_sml:
            sml_classes.add(name)

    def _leaf_members(annotation):
        if annotation.startswith("Union[") and annotation.endswith("]"):
            return [member.strip() for member in annotation[6:-1].split(",")]
        return [annotation]

    def _disambiguated_leaf_name(base_name: str, sid: str, leaf_cls: str) -> str:
        """Unique class name for a leaf whose plain CamelCase name is owned by
        a DIFFERENT element (same id_short, different semanticId — e.g. CCI's
        ``Type``: ReferenceElement ``Instance/Type`` vs Property
        ``Skill/Parameter/Type``).  Uses the semanticId namespace suffix
        (``Type`` + ``.../Instance/Type/2/0`` → ``Type_instance``), then
        numeric dedup."""
        suf = sid_namespace_suffix(base_name, sid) or leaf_cls
        cand = f"{base_name}_{suf}"
        i = 2
        c = cand
        while c in leaf_bases or c in classes or (
            c in _name_identity and _name_identity[c] != (base_name, sid)
        ):
            c = f"{cand}_{i}"
            i += 1
        return c

    def leaf_class_for(c: dict, leaf_cls: str) -> str:
        """Register (once) a dedicated subclass of *leaf_cls* carrying the
        element's template defaults — concept semanticId, description,
        supplemental semanticIds, ``value_type`` (Property/Range),
        ``content_type`` (File/Blob), and RelationshipElement endpoints —
        and return its name.

        The class name is the CamelCased id_short (``year_of_construction`` →
        ``YearOfConstruction``).  Class-level defaults survive ANY construction
        path (config dict, partial instance, converter) because pydantic
        validates against the class instead of discarding an instance default.

        A dedicated leaf class is REUSED only when the same (id_short,
        semanticId, base type) recurs; a same-named leaf with a DIFFERENT
        semanticId or modelType gets its own disambiguated class (e.g. CCI
        ``Type`` → ``Type`` Property + ``Type_instance`` ReferenceElement).
        Falls back to the generic *leaf_cls* only when there is no concept
        semanticId or the element has no idShort."""
        sid = extract_semantic_id(c)
        elem_name = to_camel(safe_name(c.get("idShort", "")))
        # Capability is an author-supplied concept in existing subclasses;
        # specializing its field would reject authored Capability instances.
        if not elem_name or (elem_name == leaf_cls and leaf_cls == "Capability") or (
            not sid and not extract_description(c) and not extract_value_type(c)
            and not extract_supplemental_semantic_ids(c)
            and not (c.get("contentType") or c.get("content_type"))
            and not (c.get("first") or c.get("second"))
        ):
            return leaf_cls
        check_class_name(elem_name)
        meta = metadata_lines(c, include_empty_semantic_id=False)
        vt = extract_value_type(c)
        if vt and leaf_cls in ("Property", "Range"):
            meta.append(f'    value_type: str = {json.dumps(vt)}')
        ct = c.get("contentType") or c.get("content_type")
        if ct and leaf_cls in ("File", "Blob"):
            meta.append(f'    content_type: str = {json.dumps(ct)}')
        if leaf_cls == "RelationshipElement":
            for key_name in ("first", "second"):
                ref = c.get(key_name)
                if isinstance(ref, dict) and not is_placeholder_endpoint(ref):
                    ref_src = emit_reference(ref, "    ")
                    ref_cls = ref_src[0].lstrip().rstrip("(").strip()
                    meta.append(f"    {key_name}: {ref_cls} = " + ref_src[0].lstrip())
                    meta.extend(ref_src[1:])
                    # The closing parenthesis is the value; no trailing comma.
        identity = (elem_name, sid, leaf_cls, tuple(meta))
        if identity in leaf_identities:
            return leaf_identities[identity]
        if (elem_name == leaf_cls or elem_name in classes or
                (_name_identity.get(elem_name) is not None and
                 _name_identity[elem_name] != (elem_name, sid))):
            name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
        else:
            name = elem_name
        register(name, meta, [])
        leaf_bases[name] = leaf_cls
        leaf_identities[identity] = name
        # Reserve the name so a later container/leaf of the same base id_short
        # dedups (``SerialNumber_2``) instead of silently shadowing this class.
        _name_identity.setdefault(name, (elem_name, sid))
        return name

    def leaf_annotation(c: dict, cls: str) -> str:
        """Accept an existing authored primary leaf alongside its variant."""
        primary = to_camel(safe_name(c.get("idShort", "")))
        if primary == cls:
            return cls
        if primary in ELEMENT_MAP.values() and cls in leaf_bases:
            base_aliases.add(primary)
            return f"Union[{cls}, {primary}_base]"
        if (primary != cls and primary in leaf_bases and cls in leaf_bases and
                leaf_bases[primary] == leaf_bases[cls] and
                _name_identity.get(primary) == _name_identity.get(cls)):
            return f"Union[{cls}, {primary}]"
        return cls

    def walk(el: dict, stack: tuple = (), name: str = None) -> list:
        """Register the ``{Name}`` container class for *el* with its children
        as DIRECT named fields (field name == id_short) — no ``value`` /
        ``submodel_element`` / ``statements`` wrapper (the standardized
        containers are abolished).

        Children whose template cardinality allows more than one
        (``SMT/Cardinality`` ZeroToMany/OneToMany) become dynamic
        ``Dict[str, Element]`` maps — MANY instances keyed by name.

        ``name`` overrides the class name (used for SML items whose template
        idShort is missing — falls back to ``{ListName}Item``).  ``stack``
        holds ``(id_short, semanticId, resolved_class_name)`` tuples of the
        elements currently being defined.  Recursion is detected by the pair
        (id_short, semanticId) — NOT the bare id_short — so a same-named child
        of a *different* semanticId (AID's nested object-schema ``properties``)
        is a real class, not a false recursion.  Recursive multi-cardinality
        children (HSEM ``Node`` in ``Node``) become empty ``Dict[str, Node]``
        maps; recursive single-cardinality children (AID's ``property_name`` →
        ``properties`` → ``property_name``) are optional (``Optional[X] =
        None``) so nesting stays representable without recursing forever.

        Single-cardinality children obey the template's ``SMT/Cardinality``:
        ``One`` (or a missing qualifier, which the templates use for mandatory
        elements) is required with NO default — pydantic rejects a constructed
        instance that omits it, so a mandatory element must be explicitly
        configured or the build fails; ``ZeroToOne`` is ``Optional[X] = None``
        and only present once set.
        """
        cname = resolve_class_name(name or safe_name(el.get("idShort", "")),
                                   extract_semantic_id(el))
        mt_el = el.get("modelType", "")
        check_class_name(cname)
        kids = children_of(el)
        stack_map = {(b, s): r for b, s, r in stack}
        lines = []
        field_id_shorts = {}
        field_minimums = {}
        for c in kids:
            child_name = safe_name(c.get("idShort", ""))
            child_sid = extract_semantic_id(c)
            child_resolved = resolve_class_name(child_name, child_sid)
            skey = field_name(c.get("idShort", child_name))  # field = id_short
            if skey in _RESERVED_FIELDS:
                raise ValueError(f"Child field reserved by AAS model: {skey} in {cname}")
            raw_name = c.get("idShort", child_name)
            if skey in field_id_shorts:
                raise ValueError(f"Duplicate or colliding idShorts in {cname}: {raw_name!r} and {field_id_shorts[skey]!r}")
            field_id_shorts[skey] = raw_name
            mt = c.get("modelType", "")
            if mt not in ELEMENT_MAP and mt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported modelType {mt!r} for {cname}.{skey}")
            if mt == "Operation" and any(c.get(k) for k in (
                "inputVariables", "outputVariables", "inoutputVariables", "inOutputVariables"
            )):
                raise ValueError(f"Operation variables are not supported for {cname}.{skey}")
            card = extract_cardinality(c)
            multi = card in _MULTI_CARDINALITY
            field_minimums[skey] = {"OneToMany": 1, "TwoToMany": 2, "Three": 3}.get(card, 0)
            # A missing ``SMT/Cardinality`` qualifier defaults to ``One`` — the
            # element is mandatory (the only missing-qualifier cases in the
            # templates are ``forms`` / ``fileName`` / ``definesSecurityScheme``
            # / ``iolv_payloadMappingElement``).
            required = card in ("One", None, "")
            if multi:
                # multi-cardinality → dynamic name-keyed map of this element.
                # Generic-leaf elements get a dedicated subclass carrying the
                # concept semanticId (e.g. ``class SameAs(RelationshipElement)``
                # with ``semantic_id``) — back-conversion groups by the
                # resolved element class, so no ``_multi_cardinality`` ClassVar
                # is needed.
                if mt in ("SubmodelElementCollection", "Entity"):
                    if (child_name, child_sid) in stack_map:
                        # recursive child (e.g. HSEM Node in Node) — an empty
                        # Dict[str, <container>] map; no instantiation, so the
                        # default cannot recurse.
                        lines.append(
                            f"    {skey}: Dict[str, {stack_map[(child_name, child_sid)]}] = {{}}"
                        )
                        continue
                    walk(c, stack + ((child_name, child_sid, child_resolved),))
                    lines.append(f"    {skey}: Dict[str, {child_resolved}] = {{}}")
                elif mt == "SubmodelElementList":
                    _walk_sml(c, stack)
                    lines.append(f"    {skey}: Dict[str, {child_resolved}] = {{}}")
                else:
                    leaf_cls = ELEMENT_MAP.get(mt, "Property")
                    _used_leaf_types.add(leaf_cls)
                    elem_cls = leaf_class_for(c, leaf_cls)
                    lines.append(f"    {skey}: Dict[str, {elem_cls}] = {{}}")
                continue
            if mt in ("SubmodelElementCollection", "Entity"):
                if (child_name, child_sid) in stack_map:
                    # Recursive single-cardinality child (AID object schema:
                    # ``property_name → properties → property_name``).  These
                    # are ZeroToOne in the templates — optional, so not
                    # instantiated unless set (this also breaks the recursion
                    # cleanly).
                    rec = stack_map[(child_name, child_sid)]
                    lines.append(f"    {skey}: Optional[{rec}] = None")
                    continue
                walk(c, stack + ((child_name, child_sid, child_resolved),))
                if required:
                    lines.append(f"    {skey}: {child_resolved}")
                else:
                    lines.append(f"    {skey}: Optional[{child_resolved}] = None")
            elif mt == "SubmodelElementList":
                _walk_sml(c, stack)
                if required:
                    lines.append(f"    {skey}: {child_resolved}")
                else:
                    lines.append(f"    {skey}: Optional[{child_resolved}] = None")
            else:
                leaf_cls = ELEMENT_MAP.get(mt, "Property")
                _used_leaf_types.add(leaf_cls)
                elem_cls = leaf_annotation(c, leaf_class_for(c, leaf_cls))
                if required:
                    lines.append(f"    {skey}: {elem_cls}")
                else:
                    lines.append(f"    {skey}: Optional[{elem_cls}] = None")
        if not lines:
            lines.append("    pass")
        else:
            lines = [
                _annotate_field(
                    line,
                    field_id_shorts[_FIELD_LINE_RE.match(line).group(1)],
                    field_minimums[_FIELD_LINE_RE.match(line).group(1)],
                )
                for line in lines
            ]
        # container class: attributes (semantic_id, ...) + the typed child
        # fields directly (no ``value``/``submodel_element``/``statements``
        # wrapper).  Required children have NO default — pydantic enforces they
        # are provided.
        meta = metadata_lines(el)
        is_entity = mt_el == "Entity"
        if is_entity:
            _used_leaf_types.add("Entity")
            meta.append(
                f'    entity_type: str = {json.dumps(el.get("entityType", "CoManagedEntity"))}'
            )
            gid = el.get("globalAssetId")
            if gid:
                meta.append(f'    global_asset_id: str = {json.dumps(gid)}')
        register(cname, meta, lines, is_entity=is_entity)
        return lines

    def _walk_sml(c: dict, stack: tuple):
        """Register an SML class with a typed ``value: List[Item]`` (AASd-108:
        homogeneous lists only — heterogeneous ones start empty)."""
        cname = resolve_class_name(safe_name(c.get("idShort", "")),
                                   extract_semantic_id(c))
        check_class_name(cname)
        item_kids = children_of(c)
        sub_meta = metadata_lines(c)
        declared_item = c.get("typeValueListElement")
        if declared_item:
            sub_meta.append(f'    type_value_list_element: str = {json.dumps(declared_item)}')
        declared_value_type = c.get("valueTypeListElement")
        if declared_value_type:
            sub_meta.append(f'    value_type_list_element: str = {json.dumps(declared_value_type)}')
        declared_sid = extract_semantic_id({"semanticId": c.get("semanticIdListElement")})
        if declared_sid:
            sub_meta.append(f'    semantic_id_list_element: str = {json.dumps(declared_sid)}')
        if "orderRelevant" in c:
            sub_meta.append(f'    order_relevant: bool = {bool(c["orderRelevant"])}')
        item_classes = set()  # for AASd-108 homogeneity check
        stack_map = {(b, s): r for b, s, r in stack}
        for item in item_kids:
            imt = item.get("modelType", "")
            if imt not in ELEMENT_MAP and imt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported list item modelType {imt!r} for {cname}")
            if imt in ("SubmodelElementCollection", "Entity"):
                item_name = safe_name(item.get("idShort", f"{cname}Item"))
                item_sid = extract_semantic_id(item)
                if (item_name, item_sid) in stack_map:
                    # Recursive item — skip entirely.
                    continue
                item_resolved = resolve_class_name(item_name, item_sid)
                walk(item, stack + ((item_name, item_sid, item_resolved),),
                     name=item_name)
                item_classes.add(item_resolved)
            elif imt == "SubmodelElementList":
                item_classes.add("SubmodelElementList")
            else:
                leaf_cls = ELEMENT_MAP[imt]
                _used_leaf_types.add(leaf_cls)
                item_classes.add(leaf_cls)
        if declared_item in ELEMENT_MAP and not any(
            item.get("modelType") in ("SubmodelElementCollection", "Entity")
            for item in item_kids
        ):
            item_classes = {ELEMENT_MAP[declared_item]}
        if declared_value_type and item_classes == {"Property"}:
            item_name = f"{cname}Item"
            item_meta = [f'    value_type: str = {json.dumps(declared_value_type)}']
            if item_name in classes and classes[item_name][0] != item_meta:
                raise ValueError(f"Conflicting list item class metadata: {item_name}")
            if item_name not in classes:
                register(item_name, item_meta, [])
                leaf_bases[item_name] = "Property"
            item_classes = {item_name}
        if item_classes and len(item_classes) == 1:
            # Homogeneous list — declare item_type so back-conversion can
            # restore item types (AASd-114 strips item semanticIds in basyx),
            # but start EMPTY: the template's example items are empty
            # scaffolding and would leak into every generated instance (e.g.
            # nameplate ``Markings`` carrying an empty ``marking_name`` SMC).
            item_cls = next(iter(item_classes))
            sub_meta.append(f"    item_type: ClassVar = {item_cls}")
            sml_body = [f"    value: List[{item_cls}] = []"]
        else:
            # Heterogeneous or empty (e.g. CapabilityPropertyType lists
            # Range/Property/MLP exemplars) — basyx cannot represent a
            # mixed-type SML (AASd-108), so start empty; users populate it
            # with a homogeneous list.
            sml_body = ["    value: List[Any] = []"]
        register(cname, sub_meta, sml_body, is_sml=True)

    sm_meta = metadata_lines(sm)
    walk(sm)

    admin = sm.get("administration", {})
    sm_meta.append(f'    VERSION: ClassVar[str] = "{admin.get("version", "1")}"')
    sm_meta.append(f'    REVISION: ClassVar[str] = "{admin.get("revision", "0")}"')
    # prepend the Submodel-level meta (walk registered semantic_id/description)
    classes[sm_name] = (sm_meta, classes[sm_name][1])

    # ── Assemble file ──
    # Build the body first (clash aliases are emitted during assembly), then
    # derive the imports from the assembled text so nothing is missed.
    body = []
    aliases_emitted = set()
    alias_definitions = []
    for name in order:
        meta, cbody = classes[name]
        if name == sm_name:
            base = "Submodel"
        elif name in entity_classes:
            base = "Entity"
        elif name in sml_classes:
            base = "SubmodelElementList"
        elif name in leaf_bases:
            base = leaf_bases[name]
        else:
            base = "SubmodelElementCollection"
        # Pydantic rejects a field whose name equals its type annotation
        # (e.g. ``items: items``); alias the type and emit aliases after all
        # classes so later-defined shared concepts are available too.
        cbody, alias_lines = _rewrite_clash_fields(cbody, aliases_emitted)
        for a in alias_lines:
            alias_definitions.append(
                f"# alias so field ``{a.split(':')[0]}`` can name a class of the same id_short"
            )
            alias_definitions.append(a)
        body.append(f"class {name}({base}):")
        body.extend(meta)
        body.extend(cbody)
        body.append('')

    # Postponed annotations let aliases follow their definitions. This matters
    # for recursive/list graphs where a same-named referenced container is
    # registered later in document traversal order.
    body.extend(alias_definitions)
    for base in sorted(base_aliases):
        body.append(f"{base}_base: TypeAlias = {base}")

    body.append('# ── Resolve forward references (Pydantic circular refs) ──')
    for name in order:
        body.append(f'{name}.model_rebuild()')
    body.append('')

    all_src = "\n".join(body)
    lines = []
    template_abs = os.path.abspath(template_path)
    relative_to = (
        TEMPLATE_ROOT
        if os.path.commonpath((TEMPLATE_ROOT, template_abs)) == TEMPLATE_ROOT
        else _ROOT
    )
    source_path = os.path.relpath(template_abs, relative_to)
    lines.append(f'"""{sm_name} - generated from IDTA template.')
    lines.append(f"Source: {source_path}")
    lines.append('"""')
    lines.append('')
    lines.append('from __future__ import annotations')
    lines.append('')
    typing_names = ["Any", "ClassVar", "List"]
    if "Dict[" in all_src:
        typing_names.append("Dict")
    if "Optional[" in all_src:
        typing_names.append("Optional")
    if "Union[" in all_src:
        typing_names.append("Union")
    if ": TypeAlias" in all_src:
        typing_names.append("TypeAlias")
    lines.append(f"from typing import {', '.join(typing_names)}")
    lines.append('from aas_pydantic import (')
    aas_types = {"Submodel", "SubmodelElement", "SubmodelElementCollection",
                 "SubmodelElementList", "Entity", "Qualifier",
                 "ExternalReference", "ModelReference", "Key"}
    aas_types |= set(ELEMENT_MAP.values())
    imports = sorted(t for t in _used_leaf_types if t in aas_types)
    # Reference endpoints (first/second) use ExternalReference/ModelReference/Key.
    if "ExternalReference(" in all_src:
        imports = sorted(set(imports) | {"ExternalReference", "Key"})
    if "ModelReference(" in all_src:
        imports = sorted(set(imports) | {"ModelReference", "Key"})
    lines.append('    ' + ', '.join(imports) + ',')
    lines.append(')')
    if "Field(" in all_src:
        lines.append('from pydantic import Field')
    if ": AasIdString" in all_src:
        lines.append('from aas_pydantic.aas_model import AasIdString')
    lines.append('')

    lines.extend(body)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{snake(sm_name)}.py")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ {out_path}")
    print(f"   {sm_name}(Submodel) + {len(order) - 1} classes")


if __name__ == "__main__":
    # Resolve relative to the aas-model repo root (scripts/ is one level down),
    # so this works from any working directory.
    if len(sys.argv) >= 2:
        tmpl = sys.argv[1]
        if not os.path.isabs(tmpl):
            tmpl = os.path.join(TEMPLATE_ROOT, tmpl)
        gen_template(tmpl, sys.argv[2] if len(sys.argv) > 2 else OUTPUT_ROOT)
    else:
        for template in TEMPLATES:
            gen_template(os.path.join(TEMPLATE_ROOT, template), OUTPUT_ROOT)
        print(f"\nGenerated {len(TEMPLATES)} templates into {OUTPUT_ROOT}")
