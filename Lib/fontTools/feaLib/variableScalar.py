from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib.ttFont import TTFont
from fontTools.varLib.models import VariationModel, normalizeValue, piecewiseLinearMap

import typing

if typing.TYPE_CHECKING:
    from typing import Self

LocationTuple = tuple[tuple[str, float], ...]
"""A hashable location."""


def Location(location: Mapping[str, float]) -> LocationTuple:
    """Create a hashable location from a dictionary-like location."""
    return tuple(sorted(location.items()))


class VariableScalar:
    """A scalar with different values at different points in the designspace."""

    values: dict[LocationTuple, int]
    """The values across various user-locations. Must always include the default
    location by time of building."""

    def __init__(self, location_value={}):
        self.values = {
            Location(location): value for location, value in location_value.items()
        }

    def __repr__(self):
        items = []
        for location, value in self.values.items():
            loc = ",".join(
                [
                    f"{ax}={int(coord) if float(coord).is_integer() else coord}"
                    for ax, coord in location
                ]
            )
            items.append("%s:%i" % (loc, value))
        return "(" + (" ".join(items)) + ")"

    @property
    def does_vary(self) -> bool:
        values = list(self.values.values())
        return any(v != values[0] for v in values[1:])

    def add_value(self, location: Mapping[str, float], value: int):
        self.values[Location(location)] = value


@dataclass
class VariableScalarBuilder:
    """A helper class for building variable scalars, or otherwise interrogating
    their variation model for interpolation or similar."""

    axis_triples: dict[str, tuple[float, float, float]]
    """Minimum, default, and maximum for each axis in user-coordinates."""
    axis_mappings: dict[str, Mapping[float, float]]
    """Optional mappings from normalized user-coordinates to normalized
    design-coordinates."""

    model_cache: dict[tuple[LocationTuple, ...], VariationModel]
    """We often use the same exact locations (i.e. font sources) for a large
    number of variable scalars. Instead of creating a model for each, cache
    them. Cache by user-location to avoid repeated mapping computations."""

    @classmethod
    def from_ttf(cls, ttf: TTFont) -> Self:
        return cls(
            axis_triples={
                axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue)
                for axis in ttf["fvar"].axes
            },
            axis_mappings=(
                {}
                if (avar := ttf.get("avar")) is None
                else {axis: segments for axis, segments in avar.segments.items()}
            ),
            model_cache={},
        )

    @classmethod
    def from_designspace(cls, doc: DesignSpaceDocument) -> Self:
        return cls(
            axis_triples={
                axis.tag: (axis.minimum, axis.default, axis.maximum)
                for axis in doc.axes
            },
            axis_mappings={
                axis.tag: {
                    normalizeValue(
                        user, (axis.minimum, axis.default, axis.maximum)
                    ): normalizeValue(
                        design,
                        (
                            axis.map_forward(axis.minimum),
                            axis.map_forward(axis.default),
                            axis.map_forward(axis.maximum),
                        ),
                    )
                    for user, design in axis.map.items()
                }
                for axis in doc.axes
                if axis.map is not None
            },
            model_cache={},
        )

    def normalise_location(self, location: LocationTuple) -> LocationTuple:
        """Fully-specify, validate, and normalize a user-location."""

        full = {}

        # Normalize explicit axes, and error for unrecognised ones.
        for axtag, value in location:
            axis = self.axis_triples.get(axtag)
            if axis is None:
                raise ValueError("Unknown axis %s in %s" % (axtag, location))

            axis_min, axis_default, axis_max = axis
            full[axtag] = normalizeValue(value, (axis_min, axis_default, axis_max))

        # Populate implicit axes.
        for axtag in self.axis_triples:
            if axtag in full:
                continue
            full[axtag] = 0.0

        return Location(full)

    def normalised_values(self, scalar: VariableScalar) -> dict[LocationTuple, int]:
        """Get the values of a variable scalar with fully-specified, normalized
        and validated user-locations."""

        return {
            self.normalise_location(location): value
            for location, value in scalar.values.items()
        }

    def default_value(self, scalar: VariableScalar) -> int:
        """Get the default value of a variable scalar."""

        full_values = self.normalised_values(scalar)
        default_loc = Location({tag: 0.0 for tag in self.axis_triples})

        default_value = full_values.get(default_loc)
        if default_value is None:
            raise ValueError("Default value could not be found")

        return default_value

    def value_at_location(
        self, scalar: VariableScalar, location: LocationTuple
    ) -> float:
        """Interpolate the value of a scalar from a user-location."""

        location = self.normalise_location(location)
        full_values = self.normalised_values(scalar)

        exact = full_values.get(location)
        if exact is not None:
            return exact

        values = list(full_values.values())
        design_location = {
            axis_tag: (
                value
                if (mapping := self.axis_mappings.get(axis_tag)) is None
                else piecewiseLinearMap(value, mapping)
            )
            for axis_tag, value in location
        }

        value = self.model(scalar).interpolateFromMasters(design_location, values)
        if value is None:
            raise ValueError("Insufficient number of values to interpolate")

        return value

    def model(self, scalar: VariableScalar) -> VariationModel:
        """Return a variation model based on a scalar's values.

        Variable scalars with the same fully-specified user-location will use
        the same cached variation model."""

        full_values = self.normalised_values(scalar)
        cache_key = tuple(full_values.keys())

        cached_model = self.model_cache.get(cache_key)
        if cached_model is not None:
            return cached_model

        design_locations = [
            {
                axis_tag: (
                    value
                    if (mapping := self.axis_mappings.get(axis_tag)) is None
                    else piecewiseLinearMap(value, mapping)
                )
                for axis_tag, value in location
            }
            for location in full_values.keys()
        ]
        model = self.model_cache[cache_key] = VariationModel(design_locations)

        return model

    def get_deltas_and_supports(self, scalar: VariableScalar):
        """Calculate deltas and supports from this scalar's variation model."""
        values = list(scalar.values.values())
        return self.model(scalar).getDeltasAndSupports(values)

    def add_to_variation_store(
        self, scalar: VariableScalar, store_builder
    ) -> tuple[int, int]:
        """Serialise this scalar's variation model to a store, returning the
        default value and variation index."""

        deltas, supports = self.get_deltas_and_supports(scalar)
        store_builder.setSupports(supports)
        index = store_builder.storeDeltas(deltas)

        # NOTE: Default value should be an exact integer by construction of
        #       VariableScalar.
        return int(self.default_value(scalar)), index
