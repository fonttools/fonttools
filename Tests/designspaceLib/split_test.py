import math
import shutil
from pathlib import Path

import pytest
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.designspaceLib.split import (
    _conditionSetFrom,
    convert5to4,
    splitInterpolable,
    splitVariableFonts,
)
from fontTools.designspaceLib.types import ConditionSet, Range

from .fixtures import datadir

UPDATE_REFERENCE_OUT_FILES_INSTEAD_OF_TESTING = False


@pytest.mark.parametrize(
    "test_ds,expected_interpolable_spaces",
    [
        (
            "test_v5_aktiv.designspace",
            [
                (
                    {},
                    {
                        "AktivGroteskVF_Italics_Wght",
                        "AktivGroteskVF_Italics_WghtWdth",
                        "AktivGroteskVF_Wght",
                        "AktivGroteskVF_WghtWdth",
                        "AktivGroteskVF_WghtWdthItal",
                    },
                )
            ],
        ),
        (
            "test_v5_sourceserif.designspace",
            [
                (
                    {"italic": 0},
                    {"SourceSerif4Variable-Roman"},
                ),
                (
                    {"italic": 1},
                    {"SourceSerif4Variable-Italic"},
                ),
            ],
        ),
        (
            "test_v5_MutatorSans_and_Serif.designspace",
            [
                (
                    {"serif": 0},
                    {
                        "MutatorSansVariable_Weight_Width",
                        "MutatorSansVariable_Weight",
                        "MutatorSansVariable_Width",
                    },
                ),
                (
                    {"serif": 1},
                    {
                        "MutatorSerifVariable_Width",
                    },
                ),
            ],
        ),
    ],
)
def test_split(datadir, tmpdir, test_ds, expected_interpolable_spaces):
    data_in = datadir / test_ds
    temp_in = Path(tmpdir) / test_ds
    shutil.copy(data_in, temp_in)
    doc = DesignSpaceDocument.fromfile(temp_in)

    for i, (location, sub_doc) in enumerate(splitInterpolable(doc)):
        expected_location, expected_vf_names = expected_interpolable_spaces[i]
        assert location == expected_location
        vfs = list(splitVariableFonts(sub_doc))
        assert expected_vf_names == set(vf[0] for vf in vfs)

        loc_str = "_".join(
            f"{name}_{value}" for name, value in sorted(location.items())
        )
        data_out = datadir / "split_output" / f"{temp_in.stem}_{loc_str}.designspace"
        temp_out = Path(tmpdir) / "out" / f"{temp_in.stem}_{loc_str}.designspace"
        temp_out.parent.mkdir(exist_ok=True)
        sub_doc.write(temp_out)

        if UPDATE_REFERENCE_OUT_FILES_INSTEAD_OF_TESTING:
            data_out.write_text(temp_out.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            assert data_out.read_text(encoding="utf-8") == temp_out.read_text(
                encoding="utf-8"
            )

        for vf_name, vf_doc in vfs:
            data_out = (datadir / "split_output" / vf_name).with_suffix(".designspace")
            temp_out = (Path(tmpdir) / "out" / vf_name).with_suffix(".designspace")
            temp_out.parent.mkdir(exist_ok=True)
            vf_doc.write(temp_out)

            if UPDATE_REFERENCE_OUT_FILES_INSTEAD_OF_TESTING:
                data_out.write_text(
                    temp_out.read_text(encoding="utf-8"), encoding="utf-8"
                )
            else:
                assert data_out.read_text(encoding="utf-8") == temp_out.read_text(
                    encoding="utf-8"
                )


@pytest.mark.parametrize(
    "test_ds,expected_vfs",
    [
        (
            "test_v5_aktiv.designspace",
            {
                "AktivGroteskVF_Italics_Wght",
                "AktivGroteskVF_Italics_WghtWdth",
                "AktivGroteskVF_Wght",
                "AktivGroteskVF_WghtWdth",
                "AktivGroteskVF_WghtWdthItal",
            },
        ),
        (
            "test_v5_sourceserif.designspace",
            {
                "SourceSerif4Variable-Italic",
                "SourceSerif4Variable-Roman",
            },
        ),
    ],
)
def test_convert5to4(datadir, tmpdir, test_ds, expected_vfs):
    data_in = datadir / test_ds
    temp_in = tmpdir / test_ds
    shutil.copy(data_in, temp_in)
    doc = DesignSpaceDocument.fromfile(temp_in)

    variable_fonts = convert5to4(doc)

    assert variable_fonts.keys() == expected_vfs
    for vf_name, vf in variable_fonts.items():
        data_out = (datadir / "convert5to4_output" / vf_name).with_suffix(
            ".designspace"
        )
        temp_out = (Path(tmpdir) / "out" / vf_name).with_suffix(".designspace")
        temp_out.parent.mkdir(exist_ok=True)
        vf.write(temp_out)

        if UPDATE_REFERENCE_OUT_FILES_INSTEAD_OF_TESTING:
            data_out.write_text(temp_out.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            assert data_out.read_text(encoding="utf-8") == temp_out.read_text(
                encoding="utf-8"
            )


@pytest.mark.parametrize(
    ["unbounded_condition"],
    [
        ({"name": "Weight", "minimum": 500},),
        ({"name": "Weight", "maximum": 500},),
        ({"name": "Weight", "minimum": 500, "maximum": None},),
        ({"name": "Weight", "minimum": None, "maximum": 500},),
    ],
)
def test_optional_min_max(unbounded_condition):
    """Check that split functions can handle conditions that are partially
    unbounded without tripping over None values and missing keys."""
    doc = DesignSpaceDocument()

    doc.addAxisDescriptor(
        name="Weight", tag="wght", minimum=400, maximum=1000, default=400
    )

    doc.addRuleDescriptor(
        name="unbounded",
        conditionSets=[[unbounded_condition]],
    )

    assert len(list(splitInterpolable(doc))) == 1
    assert len(list(splitVariableFonts(doc))) == 1


@pytest.mark.parametrize(
    ["condition", "expected_set"],
    [
        (
            {"name": "axis", "minimum": 0.5},
            {"axis": Range(minimum=0.5, maximum=math.inf)},
        ),
        (
            {"name": "axis", "maximum": 0.5},
            {"axis": Range(minimum=-math.inf, maximum=0.5)},
        ),
        (
            {"name": "axis", "minimum": 0.5, "maximum": None},
            {"axis": Range(minimum=0.5, maximum=math.inf)},
        ),
        (
            {"name": "axis", "minimum": None, "maximum": 0.5},
            {"axis": Range(minimum=-math.inf, maximum=0.5)},
        ),
    ],
)
def test_optional_min_max_internal(condition, expected_set: ConditionSet):
    """Check that split's internal helper functions produce the correct output
    for conditions that are partially unbounded."""
    assert _conditionSetFrom([condition]) == expected_set


def test_avar2(datadir):
    ds = DesignSpaceDocument()
    ds.read(datadir / "test_avar2.designspace")
    _, subDoc = next(splitInterpolable(ds))
    assert len(subDoc.axisMappings) == 1

    subDocs = list(splitVariableFonts(ds))
    assert len(subDocs) == 5
    for i, (_, subDoc) in enumerate(subDocs):
        # Only the first one should have a mapping, according to the document
        if i == 0:
            assert len(subDoc.axisMappings) == 1
        else:
            assert len(subDoc.axisMappings) == 0
