"""Prepare the compiled scorer for internally generated user locations."""

from . import _mapping
from fontTools.varLib.varStore import NO_VARIATION_INDEX


class _ForwardScorer:
    def __init__(self, forward, pinned=None):
        import numpy as np

        self.tags = forward.tags
        self.pins = np.array(
            [(pinned or {}).get(tag, np.nan) for tag in self.tags], dtype=float
        )
        self.defaults = tuple(forward.triples[tag][1] for tag in self.tags)
        self.triples = np.array(
            [forward.triples[tag] for tag in self.tags], dtype=float
        ).reshape((-1, 3))
        segments = [sorted(forward.segments.get(tag, {}).items()) for tag in self.tags]
        segment_data = _mapping.packSegments(segments)
        instancer = forward._instancer
        rows, supports, regions = [], [], {}
        for index in (
            forward._indices if instancer is not None else [None] * len(self.tags)
        ):
            row = []
            if index is not None and index != NO_VARIATION_INDEX:
                major, minor = index >> 16, index & 0xFFFF
                if major < len(instancer._varData) and minor < len(
                    instancer._varData[major].Item
                ):
                    data = instancer._varData[major]
                    # Preserve each row's order and duplicate region indices.
                    # Assembling the continuous matrix can reorder or combine
                    # terms, which is unsuitable for exact rounded scoring.
                    for region, delta in zip(data.VarRegionIndex, data.Item[minor]):
                        if not delta:
                            continue
                        if region not in regions:
                            regions[region] = len(supports)
                            support = instancer._getSupport(region)
                            supports.append(
                                [
                                    (i, *support[tag])
                                    for i, tag in enumerate(self.tags)
                                    if tag in support
                                    and support[tag][0]
                                    <= support[tag][1]
                                    <= support[tag][2]
                                    and not support[tag][0] < 0 < support[tag][2]
                                ]
                            )
                        row.append((regions[region], delta))
            rows.append(row)
        offsets, factors = [0], []
        for support in supports:
            factors.extend(support)
            offsets.append(len(factors))
        row_offsets, entries = [0], []
        for row in rows:
            entries.extend(row)
            row_offsets.append(len(entries))
        self.data = (
            *segment_data,
            np.array(offsets, dtype="l"),
            np.array([f[0] for f in factors], dtype="l"),
            *(np.array([f[j] for f in factors], dtype=float) for j in (1, 2, 3)),
            np.array(row_offsets, dtype="l"),
            np.array([r[0] for r in entries], dtype="l"),
            np.array([r[1] for r in entries], dtype=float),
            forward.version == 2,
            instancer is not None,
            self.tags,
        )

    def __call__(self, location):
        import numpy as np

        # Internal callers generate validated, complete user-coordinate dicts.
        # The public ForwardMapper API and its optional dependencies are unchanged.
        user = np.array(
            [
                location.get(tag, default)
                for tag, default in zip(self.tags, self.defaults)
            ],
            dtype=float,
        )
        return _mapping.score(user, self.triples, *self.data)

    def batch(self, coordinates):
        return _mapping.scoreBatch(coordinates, self.pins, self.triples, *self.data)
