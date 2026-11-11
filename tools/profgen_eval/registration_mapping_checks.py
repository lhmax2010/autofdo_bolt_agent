"""Registration checks on static maps and explicitly synthetic entries only.

No file or formal-profile reader, no statistical quality metrics.
"""
import hashlib
import json

from v17_rules import classify_body


def frozen_sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def compare_relations(expected, observed):
    """Retain address multiplicity even when two addresses have the same key."""
    def index(records):
        out = {}
        for r in records:
            address = (r['group'], r['address'])
            if address in out:
                raise ValueError('duplicate_address_record')
            out[address] = r
        return out
    a, b = index(expected), index(observed)
    return [dict(group=k[0], address=k[1], expected=a.get(k), observed=b.get(k))
            for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]


def validate_correspondence(states):
    closed = {'reference_executed', 'reference_unexecuted', 'identity_ambiguous',
              'not_instrumented', 'system_header_no_reference', 'macro_generated_function'}
    if any(s not in closed for s in states):
        raise ValueError('reference_unresolved_registration_failure')


def classify_entry(raw_key, inventory_names, group_roles, mapping, *,
                   unavailable=(), effective_key=None):
    """Never strip a raw profile name, even if a stripped name is in the ELF."""
    key = raw_key if effective_key is None else effective_key
    if key != raw_key:
        return 'unaligned', 'raw_key_changed'
    name = key[0][0]
    if name in unavailable:
        return 'boundary_unavailable', 'boundary_unavailable'
    known = all(frame[0] in inventory_names for frame in key)
    encoded = json.dumps(key, separators=(',', ':'))
    value = mapping.get(encoded)
    return classify_body(dict(known_name=known,
      reference_resolved=group_roles.get(name) != 'pending',
      known_out_of_scope=group_roles.get(name) == 'known_out_of_scope',
      registered_key=value is not None, value_status=(value or {}).get('status'),
      unexecuted_source=(value or {}).get('status') == 'reference_unexecuted',
      excluded=(value or {}).get('excluded', False), in_U=(value or {}).get('in_U', False)))


def classify_synthetic_run(entries, names, groups, mapping, *, unavailable=(), zero_fill='none'):
    if zero_fill != 'none':
        raise ValueError('zero_fill_profile_not_admitted_to_quality_metrics')
    results = [classify_entry(key, names, groups, mapping, unavailable=unavailable)
               for key, count in entries]
    return dict(defined=all(category != 'unaligned' for category, _ in results), entries=results)


def whole_group_unavailable(range_proofs):
    return any(r['boundary_available'] is not True for r in range_proofs)


def previous_instruction(address, instructions):
    """Synthetic reference: previous layout instruction, no backward decoding."""
    positions = {r['address']:i for i, r in enumerate(instructions)}
    i = positions[address]
    if i and instructions[i-1]['range'] == instructions[i]['range'] and \
            instructions[i-1]['address']+instructions[i-1]['size'] == address:
        return instructions[i-1]['address']
    return address


def line_has_ambiguous_key(values):
    """A line with both ambiguous and ordinary contributing keys stays excluded."""
    return any(len({tuple(v) for v in candidates}) > 1 for candidates in values)
