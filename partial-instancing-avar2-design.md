# Partial-Instancing of avar2: Design Document

Author: behdad + Claude
Date: 2026-02-26


## 1. Problem Statement

When partial-instancing a variable font with an avar2 table — e.g. restricting
`wght=500:700:900` — we must produce a valid font that renders identically to
the original for all user coordinates within the restricted range. With avar
version 1, this is straightforward: the instancer renormalizes the segment maps
and the variation data (gvar, HVAR, etc.) in tandem. With avar version 2, the
problem is fundamentally harder because:

1. The avar2 ItemVariationStore (IVS) computes **deltas that are added to
   intermediate axis coordinates**. These deltas are in the same coordinate
   units as the axis values themselves — not in font units like gvar deltas.

2. When fvar is updated (new min/default/max), the normalization changes. The
   intermediate coordinate space changes. The avar2 deltas, designed for the
   old coordinate space, become wrong.

3. Naively scaling the deltas to the new coordinate space fails because the
   negative and positive sides of an axis can have different scale factors, and
   a delta can push a coordinate across the default point (from one scale
   factor to the other). This is the "non-homogeneous stretching" problem
   identified in the earlier [partial-instancing.pdf](partial-instancing.pdf).

This document describes an approach that sidesteps the delta scaling problem
entirely.


## 2. Background

### 2.1 avar2 Processing Pipeline

For a given set of user coordinates, the font engine processes axis values in
three stages:

1. **fvar normalization**: user coordinates → normalized `[-1, +1]`
2. **avar v1 segment maps**: piecewise-linear per-axis remapping, still
   `[-1, +1]`. We call these **intermediate coordinates**.
3. **avar v2 delta application**: for each axis `i`, compute an interpolated
   delta from the IVS using ALL intermediate coordinates, add it to
   `intermediate[i]`, clamp to `[-1, +1]`. The result is the **final
   normalized coordinate**.

```c++
// Pseudocode from the avar2 spec
std::vector<int> out;
for (unsigned i = 0; i < coords.size(); i++) {
    int v = coords[i];
    uint32_t varidx = (axisIdxMap) ? axisIdxMap.map(i) : i;
    float delta = (varStore) ? varStore.get_delta(varidx, coords) : 0;
    v += std::roundf(delta);
    v = std::clamp(v, -(1<<14), +(1<<14));
    out.push_back(v);
}
// coords = out (all at once, not iteratively)
```

Key observation: **all deltas are computed from the same input coordinates**
(the intermediate values from step 2). The update is not iterative — axis A's
delta does not see axis B's adjusted value. The outputs are written to a
separate buffer and copied back.

The final normalized coordinates are then used by **all** variation tables:
gvar, HVAR, MVAR, GDEF, CFF2, etc.

### 2.2 The Additive Complication

Each axis's delta is **added** to its current intermediate value:

```
final[i] = intermediate[i] + delta_i(all_intermediates)
```

This additive structure is the core challenge. The delta function and the
identity function (`intermediate[i]` itself) live in the same coordinate space
and are summed. When the coordinate space changes (due to fvar update), both
terms change, and their interaction must be preserved.

For a **public** axis that the user controls: the intermediate value ranges
over the axis range, and the delta shifts it. The total function is
`f(x) = x + delta(x)` — the "mountain range" from
[partial-instancing.pdf](partial-instancing.pdf).

For a **private** (hidden) axis: the intermediate is always 0 (the user can't
change it), and the delta alone determines the final value: `f = 0 + delta`.

### 2.3 Spec Constraints

Two constraints restrict our design space:

**C1. avar v1 identity at endpoints.** The avar v1 segment map must include the
entries `{-1: -1, 0: 0, 1: 1}`. This means avar v1 CANNOT map the new default
to a non-zero intermediate value. ([OpenType avar spec][avar-spec])

**C2. All-defaults produce all-zeros.** At the default instance (all user axes
at default), the final normalized coordinates are all zero. This follows from:
- fvar normalization maps default → 0
- avar v1 maps 0 → 0 (C1)
- The OT variation scalar rule: "if the instance coordinate is at the default
  value (0) ... then the scalar is zero" — so all IVS region scalars are 0 at
  all-zero coords, producing zero delta.

**Note on directionality.** The approach does NOT require a unidirectional model
(i.e., private axes can appear as inputs in avar2 IVS regions). The IVS is
evaluated at **intermediate coordinates** (post-avar-v1, pre-avar-v2) for ALL
axes simultaneously. Private axes always have intermediate = 0, so their scalar
contribution is fixed regardless of instancing. We don't rebase private axes, so
their region contributions are unchanged.

[avar-spec]: https://learn.microsoft.com/en-us/typography/opentype/spec/avar


## 3. Previous Approach & Why It Fails

The approach in PR #3485 attempted to scale avar2 deltas inversely to the
coordinate stretch factor when fvar is updated. This fails because:

1. **Asymmetric stretching.** When the new default differs from the old, the
   negative and positive sides have different stretch factors. A delta of `d`
   added to intermediate `x` might produce `x + d` on the other side of the
   default, requiring a different scale factor.

2. **Pinned axes.** When an axis is pinned, its range collapses to zero. The
   stretch factor is infinite. No finite scaling can represent this.

3. **The delta IS the coordinate.** Unlike gvar deltas (which are in font
   units, independent of axis normalization), avar2 deltas are in the same
   normalized-coordinate units that change under renormalization. Scaling them
   requires knowing whether the _result_ (intermediate + delta) lands on the
   positive or negative side, which depends on the input — creating a circular
   dependency.


## 4. Proposed Approach: Offset Compensation

### 4.1 Core Insight

Instead of scaling avar2 deltas (problematic), we:

1. **Rebase the IVS regions** to the new intermediate coordinate space using
   the standard `rebaseTent` solver (this handles the input/scalar side
   correctly).

2. **Add offset compensation deltas** to the IVS that account for the
   difference between old and new intermediate coordinates (this handles the
   additive `intermediate[i]` term).

3. **Keep gvar and all other variation tables unchanged** — they remain in the
   original final-coordinate space.

The offset compensation ensures that the avar2 output (final coordinates) is
in the **old** coordinate space, matching the unrenamed gvar data.

### 4.2 Why It Works (Proof)

Define:
- `x_old[i]` = old intermediate coordinate for axis `i` at some user value
- `x_new[i]` = new intermediate coordinate (after updated fvar + avar v1)
- `inv_renorm_i(x_new)` = the old intermediate value corresponding to
  `x_new[i]`, i.e., `x_old[i] = inv_renorm_i(x_new[i])`
- `offset_i(x_new) = x_old[i] - x_new[i]`

After rebasing the IVS regions for all restricted axes (via `rebaseTent`), the
rebased delta at `x_new` equals the old delta at `x_old`:

```
rebased_delta_i(x_new) = old_delta_i(x_old)
```

This is guaranteed by `rebaseTent`: it reshapes the tent functions so that the
scalar product at any `x_new` equals the scalar product at the corresponding
`x_old`. Since the delta values are scaled by the tent-decomposition scalars,
the total weighted sum is preserved. This works for multi-axis regions because
the scalar is a product of independent per-axis terms, and rebasing processes
one axis at a time.

Adding the offset compensation:

```
final[i] = x_new[i] + rebased_delta_i(x_new) + offset_i(x_new[i])
         = x_new[i] + old_delta_i(x_old) + (x_old[i] - x_new[i])
         = x_old[i] + old_delta_i(x_old)
         = old_final[i]                                             ✓
```

The final coordinate equals the original font's final coordinate at the same
user input. Since gvar is in the old final-coordinate space, it evaluates
correctly.

### 4.3 The Offset Function

For each restricted axis `i`, the offset is:

```
offset_i(x_new) = inv_renorm_i(x_new) - x_new
```

This is a piecewise-linear function with a kink at `x_new = 0` (where the
renormalization changes slope, since the negative and positive sides of the
axis may have different stretch factors).

Define:
- `a_i` = old intermediate value at the new minimum user value
- `d_i` = old intermediate value at the new default user value
- `b_i` = old intermediate value at the new maximum user value

These are computed as `old_avar1(norm_old(u))` where `u` is the new
min/default/max in user space. If the old font has no avar v1 segment map for
this axis (identity), then `a_i = norm_old(new_min)`, etc.

The offset function evaluates to:
- At `x_new = -1`: `offset = a_i - (-1) = a_i + 1`
- At `x_new = 0`: `offset = d_i - 0 = d_i`
- At `x_new = +1`: `offset = b_i - 1`

When the default doesn't change (`d_i = 0`), the offset at the default is zero
and the function is a simple two-piece linear function through the origin.

When the default DOES change (`d_i ≠ 0`), the offset at the default is
non-zero.

### 4.4 Encoding the Offset in the avar2 IVS

The offset function is decomposed into three IVS delta sets per axis:

| # | Region | Delta value | At `x=0` |
|---|--------|-------------|----------|
| 1 | **Empty** (no axes listed) | `d_i` | `d_i` |
| 2 | Tent `(-1, -1, 0)` on axis `i` | `a_i + 1 - d_i` | 0 |
| 3 | Tent `(0, +1, +1)` on axis `i` | `b_i - 1 - d_i` | 0 |

Verification at the three key points:
- `x = -1`: `d_i + (a_i + 1 - d_i)·1 + (b_i - 1 - d_i)·0 = a_i + 1` ✓
- `x = 0`: `d_i + 0 + 0 = d_i` ✓
- `x = +1`: `d_i + (a_i + 1 - d_i)·0 + (b_i - 1 - d_i)·1 = b_i - 1` ✓

### 4.5 The Empty-Region Bias Trick

The first entry uses an **empty region** — a VariationRegion where no axis
participates. By the OpenType variation scalar algorithm, the scalar for such
a region is the product of per-axis terms where each non-participating axis
contributes `1.0`, giving a total scalar of **1** at all coordinates.

In IVS format 1 (standard `VarRegionList`), each region has one entry per
axis. An "empty region" is encoded as all axes having
`StartCoord=0, PeakCoord=0, EndCoord=0`. The per-axis scalar rule:
"if peak is 0, return 1" applies to each axis, giving scalar `1^n = 1`.

In IVS format 2 (`SparseVarRegionList`), the region simply lists zero axes.
The loop body never executes, and the initial scalar `1.0` is returned.

This allows encoding a constant "bias" delta that shifts the axis even at the
default location. This is essential when the default changes (`d_i ≠ 0`).

**Spec considerations:**

- The empty region is valid by the ItemVariationStore mechanics. The scalar
  computation is well-defined (empty product = 1).
- However, it means the default instance has non-zero final coordinates. This
  is unusual — conventionally, all-defaults map to all-zeros. But:
  - The avar v2 spec does not explicitly prohibit non-zero deltas at default.
  - The constraint C2 (all-defaults → all-zeros) arises from the scalar rule
    "at default, scalar is 0 for non-zero peaks." An empty region has **no**
    peaks, so this rule does not apply.
  - Most renderers optimize all-zero-coords by skipping variation processing.
    But this optimization applies to **gvar/HVAR/etc processing**, not to the
    **avar2 IVS processing** itself. The avar2 loop unconditionally calls
    `get_delta` for every axis. So the bias IS evaluated.
  - Since the bias produces non-zero final coordinates, the renderer will NOT
    skip gvar processing (the all-zero fast-path doesn't trigger on the
    post-avar2 coordinates).

**HarfBuzz verification (confirmed):**

1. **Empty region scalar = 1.** In standard `VarRegionList` (IVS format 1),
   each region has one `VarRegionAxis` per axis. When `peakCoord == 0`, the
   per-axis scalar is `1.f` (`hb-ot-layout-common.hh:2472-2474`). A region
   with all peaks at 0 gives scalar `1^n = 1`. In `SparseVarRegionList`
   (IVS format 2), an empty `SparseVariationRegion` (length 0) has an empty
   loop that returns the initial `v = 1.f` (`hb-ot-layout-common.hh:2808-2820`).
   Both formats produce scalar 1.0 for the "all-zero-peaks" / "empty" region.

2. **avar2 loop has no all-zero fast-path.** The `map_coords_16_16` function
   (`hb-ot-var-avar-table.hh:366-412`) unconditionally iterates all axes and
   calls `var_store.get_delta(varidx, ...)` for each. There is no early return
   or skip when input coordinates are all zero. The bias delta IS computed.

3. **`has_nonzero_coords` is set AFTER avar processing.** The font coordinate
   setting flow is: `hb_font_set_var_coords_design()` → `hb_ot_var_normalize_coords()`
   (which applies fvar normalization + `avar->map_coords_16_16()` including
   v1+v2, `hb-ot-var.cc:328-332`) → `_hb_font_adopt_var_coords()` (which sets
   `has_nonzero_coords` from the **post-avar** coordinates, `hb-font.cc:2151`).
   So at the new default: fvar → 0, avar v1 → 0, avar v2 adds bias → non-zero
   coords → `has_nonzero_coords = true` → gvar processing is NOT skipped.

### 4.6 Interaction of Offset with Rebased Deltas

The rebased IVS deltas and offset compensation deltas coexist in the same IVS.
They are independent and additive:

- **Rebased deltas**: handle the change in the delta function's input
  coordinates (via reshaped regions). They produce old-space delta values at
  new-space input coordinates.
- **Offset deltas**: handle the change in the identity term (the intermediate
  coordinate that the delta is added to). They add `x_old - x_new` to
  compensate.

The offset is **per-axis** (only involves axis `i`'s own coordinate). The
rebased deltas may be **multi-axis** (regions involving multiple axes). Their
sum is correct because the offset only adds to axis `i`'s output, while the
rebased delta preserves the multi-axis scalar structure.

### 4.7 Default Deltas

The standard `instantiateItemVariationStore` function subtracts "default
deltas" — the residual variation at the new default (all-zero new-space
coords) — and returns them for addition to base values (glyph outlines,
metrics, etc.).

For avar2, we must **not** subtract default deltas. They must remain in the
IVS because:

1. The rebased delta at all-zero new coords = `old_delta(d_1, d_2, ..., d_n)`
   (the old delta evaluated at the old intermediates for the new defaults).
   This is the correct delta at the new default and must be preserved.

2. The offset bias `d_i` adds the intermediate-coordinate contribution.

3. Together: `0 + old_delta_i(d_1,...,d_n) + d_i = old_final_i` at the new
   default. This is the correct old-space final coordinate.

Implementation: either modify `instantiateItemVariationStore` to skip default
delta subtraction, or run it normally and add the default deltas back as part
of the offset compensation (folded into the empty-region bias).

The latter is cleaner — the total empty-region bias becomes:

```
bias_i = d_i + default_delta_i
```

where `default_delta_i` is the value returned by `instantiateItemVariationStore`
for axis `i`'s varIdx.


## 5. Detailed Algorithm

### 5.1 Inputs

- A variable font with avar2 table
- Axis limits: a dict mapping axis tags to `(min, default, max)` triples or
  single (pinned) values, in user space

### 5.2 Step 1: Compute Old Intermediate Values

For each restricted (not pinned) axis `i`:

```python
old_norm_min = normalize(new_min, old_fvar_triple)
old_norm_def = normalize(new_default, old_fvar_triple)
old_norm_max = normalize(new_max, old_fvar_triple)

a_i = piecewiseLinearMap(old_norm_min, old_avar1_segment_map)
d_i = piecewiseLinearMap(old_norm_def, old_avar1_segment_map)
b_i = piecewiseLinearMap(old_norm_max, old_avar1_segment_map)
```

If no avar v1 segment map exists for axis `i` (identity): `a_i = old_norm_min`,
etc.

For pinned axes (kept as hidden): `v_i = piecewiseLinearMap(normalize(
pinned_value, old_fvar_triple), old_avar1_segment_map)`.

**This must be computed BEFORE avar v1 is modified.**

### 5.3 Step 2: Instance avar v1 (Standard)

Apply the standard avar v1 instancing: renormalize segment maps for restricted
axes. This satisfies the spec constraint C1 (`-1→-1, 0→0, 1→1`). Pinned axes
have their segment maps removed.

This is the existing `instantiateAvar` logic for avar v1 (lines 1497–1536 of
`instancer/__init__.py`), unchanged.

### 5.4 Step 3: Instance avar v2 IVS

#### 5.4.1 Rebase Regions

Compute the intermediate-space axis limits for each restricted axis. These are
the old intermediate values mapped through the renormalization:

```python
intermediate_limits = {}
for axis_tag in restricted_axes:
    # After standard avar v1 renormalization, the intermediate space
    # maps [-1, 0, 1] to [-1, 0, 1]. But the IVS regions are in
    # the OLD intermediate space. We need to tell rebaseTent what
    # subset of the old space is reachable.
    intermediate_limits[axis_tag] = NormalizedAxisTripleAndDistances(
        a_i, d_i, b_i,
        distanceNegative = ...,  # from old fvar
        distancePositive = ...,
    )
```

Run `instantiateItemVariationStore(avar_varstore, fvarAxes,
intermediate_limits)`. This:

- Rebases regions via `rebaseTent` to the new intermediate space
- Returns default deltas (the residual at the new default)

The default deltas are **not** applied to base values. They are saved for
use in the bias computation (step 5.4.3).

#### 5.4.2 Handle Axes Without Existing avar v2 Mappings

Some restricted axes may have no existing avar v2 mapping (their VarIdxMap
entry is `NO_VARIATION_INDEX` or they rely on the implicit identity). For
example, in a parametric font, `wght` drives private axes but has no
self-referencing — its own final coordinate equals its intermediate coordinate.

After instancing, gvar sees the new-space intermediate coordinate for `wght`,
not the old-space one. The offset compensation must correct this. So we need
to **create** avar v2 entries (VarIdxMap mapping + delta set) for these axes.

For each restricted axis `i` that has `NO_VARIATION_INDEX` in VarIdxMap:
- Create a new delta set in the IVS (allocate a new varIdx)
- Update VarIdxMap to point axis `i` to this new varIdx
- The delta set will contain only the offset compensation entries (bias +
  tents)

#### 5.4.3 Add Offset Compensation

For each restricted axis `i`, add three entries to the IVS at axis `i`'s
varIdx:

| Region | Delta |
|--------|-------|
| Empty (no axes) | `d_i + default_delta_i` |
| `(-1, -1, 0)` on axis `i` (new space) | `a_i + 1 - d_i` |
| `(0, +1, +1)` on axis `i` (new space) | `b_i - 1 - d_i` |

Note: `default_delta_i` is the value returned by
`instantiateItemVariationStore` for axis `i`'s varIdx. For axes that had
`NO_VARIATION_INDEX` (no prior avar v2 mapping), `default_delta_i = 0`.

The tent regions are in the **new** intermediate space (post-renormalization),
because the IVS regions have been rebased to this space.

For pinned axes (kept as hidden with `min=default=max`):

| Region | Delta |
|--------|-------|
| Empty (no axes) | `v_i + default_delta_i` |

No tents needed (the axis has zero range).

For free (unrestricted) axes: no offset needed (`x_old = x_new`).

For private axes: no offset needed (intermediate is always 0, fvar unchanged).
But their `default_delta` may be non-zero and must be preserved. Add:

| Region | Delta |
|--------|-------|
| Empty (no axes) | `default_delta_j` |

(This is only needed if `default_delta_j ≠ 0`.)

#### 5.4.4 IVS Structure Considerations

The offset compensation entries share the IVS with the rebased entries. In the
ItemVariationStore structure:

- **VarRegionList**: append the empty region (all axes with
  `StartCoord=PeakCoord=EndCoord=0`) and per-axis tent regions to the global
  list. Note: fonttools's `VarRegionList.preWrite` forces `RegionAxisCount`
  equal to `fvar.axisCount`, so regions always have entries for all axes.
- **VarData**: each VarData contains multiple items (delta rows), all sharing
  the same set of VarRegionIndex entries. The offset compensation for axis `i`
  (with varIdx `= major << 16 | minor`) adds new VarRegionIndex entries to
  VarData `major`, with non-zero delta only for item `minor` and zero for all
  other items.

If different axes are in different VarDatas (different outer indices), each
VarData gets its own set of offset regions and deltas.

The empty region can be shared across VarDatas (it's a single entry in
VarRegionList). Each VarData references it via its own VarRegionIndex entry.

### 5.5 Step 4: Skip gvar/HVAR/etc. Instancing for Restricted Axes

For restricted axes, gvar and all other variation tables (HVAR, MVAR, VVAR,
GDEF/GPOS ItemVariationStores, CFF2) are **not modified**. They remain in the
old final-coordinate space. The offset compensation ensures that avar2 outputs
old-space final coordinates, so these tables evaluate correctly.

For pinned axes that are self-contained (final coord is fixed — see §6.2):
standard instancing can fold their contribution into base values. The pinned
value used for folding is the **old-space final coordinate**:

```
pinned_final_i = v_i + default_delta_i
```

For pinned axes that are NOT self-contained (final coord varies with other
axes): keep as hidden axes — do not fold in gvar.

**Implementation**: when the font has avar v2, pass only removable-pinned-axis
limits to the gvar/HVAR/etc. instancing functions. Restricted axes are excluded
from these limits, so the instancer leaves them untouched.

### 5.6 Step 5: Update fvar

Standard fvar instancing:
- Restricted axes: update `minValue`, `defaultValue`, `maxValue`
- Removable pinned axes: remove from axis list
- Non-removable pinned axes: keep, set hidden flag,
  `minValue = defaultValue = maxValue = pinned_value`
- Free axes: unchanged
- Private axes: unchanged

### 5.7 Step 6: Update VarIdxMap

- Remove entries for removed axes (renumber remaining indices)
- Add entries for axes that now have avar v2 mappings (§5.4.2)
- Update axis indices to match the new fvar axis order


## 6. Axis Classification and Handling

### 6.1 Summary Table

| Axis type | fvar | avar v1 | avar v2 IVS | gvar etc. |
|-----------|------|---------|-------------|-----------|
| **Restricted** (range narrowed) | Update range | Standard renorm | Rebase + offset | Unchanged |
| **Pinned, removable** | Remove | Remove segment map | Fold as input, drop as output | Fold at fixed final coord |
| **Pinned, non-removable** | Hidden, zero range | Map to constant `v_i` | Fold as input, keep as output | Unchanged |
| **Free** (unrestricted) | Unchanged | Unchanged | Unchanged | Unchanged |
| **Private** (hidden) | Unchanged | Unchanged | Unchanged | Unchanged |

### 6.2 Determining Removability of Pinned Axes

A pinned axis `i` is removable if its **final coordinate is constant** — i.e.,
it doesn't vary with other axes. After instancing the avar v2 IVS for the
pinned axis (folding it as input), check whether the IVS still has any
remaining variation at axis `i`'s varIdx:

- If the remaining delta set is all zeros (no active regions): the final coord
  is the constant `v_i + default_delta_i`. Axis is removable.
- If non-zero regions remain: the final coord varies. Axis must be kept.

Alternatively, use the closure computation: if the closure gives a single
point (min = default = max) for the pinned axis, it's removable.


## 7. Worked Example

Consider a parametric font like RobotoFlex with:
- Public axes: `wght` (100:400:900), `wdth` (25:100:151), `opsz` (8:14:144)
- Private axes: `XOPQ`, `YOPQ`, `XTRA`, etc.
- avar v2 maps public → private (no self-referencing of public axes)

### Restriction: `wght=500:700:900`

**Step 1: Compute old intermediate values for wght**

```
old_norm(500) = (500 - 400) / (900 - 400) = 0.2
old_norm(700) = (700 - 400) / (900 - 400) = 0.6
old_norm(900) = (900 - 400) / (900 - 400) = 1.0
```

Assuming identity avar v1 for wght: `a = 0.2, d = 0.6, b = 1.0`

**Step 2: Standard avar v1 renormalization**

New fvar: wght 500:700:900
New normalization: `norm_new(500) = -1, norm_new(700) = 0, norm_new(900) = 1`

avar v1 segment map (after standard renormalization):
`{-1: -1, 0: 0, 1: 1}` (identity, since the old map was identity)

**Step 3: Offset compensation for wght**

```
bias     = d + default_delta_wght = 0.6 + 0  = 0.6
neg_tent = a + 1 - d              = 0.2 + 1 - 0.6 = 0.6
pos_tent = b - 1 - d              = 1.0 - 1 - 0.6 = -0.6
```

(`default_delta_wght = 0` because wght has no avar v2 self-referencing)

Since wght had `NO_VARIATION_INDEX`, create a new avar v2 entry.

**Verification at key points:**

| `x_new` (wght) | offset | `x_new + offset` | expected `x_old` |
|------|--------|-----------|-----------|
| -1 (wght=500) | 0.6 + 0.6·1 + (-0.6)·0 = **1.2** | -1 + 1.2 = **0.2** | 0.2 ✓ |
| 0 (wght=700) | 0.6 + 0.6·0 + (-0.6)·0 = **0.6** | 0 + 0.6 = **0.6** | 0.6 ✓ |
| +1 (wght=900) | 0.6 + 0.6·0 + (-0.6)·1 = **0.0** | 1 + 0.0 = **1.0** | 1.0 ✓ |

**Effect on private axis XOPQ:**

XOPQ's intermediate is always 0. Its avar v2 delta is a function of wght's
intermediate (and possibly other public axes). After rebasing the IVS regions
for wght:
- At `x_new = 0` (wght=700): XOPQ delta = old delta at wght intermediate 0.6
- This is the `default_delta_XOPQ`, preserved via the empty-region bias.

At `x_new = -1` (wght=500): XOPQ delta = old delta at wght intermediate 0.2.
The rebased IVS produces this value because `rebaseTent` preserves the scalar
product.

gvar sees old-space final coordinates for both wght and XOPQ → correct
outlines.


## 8. Interaction with Other Font Tables

### 8.1 gvar, cvar

Not modified for restricted axes. The offset compensation ensures old-space
final coordinates. For removable pinned axes, standard folding applies.

### 8.2 HVAR, VVAR, MVAR

Same as gvar — not modified for restricted axes. These use
ItemVariationStores evaluated at the final normalized coordinates.

### 8.3 GDEF/GPOS ItemVariationStores

Same treatment. Not modified for restricted axes.

### 8.4 CFF2

CFF2 contains its own ItemVariationStore for blend operations. Same treatment
as gvar — not modified for restricted axes.

### 8.5 Base Values (glyf, hmtx, CFF, etc.)

**Not updated.** The base values remain from the original font's default
instance. At the new default, the font renders correctly because:

1. avar v1 maps norm 0 → 0 (intermediate)
2. avar v2 adds bias `d_i` → final coord = `d_i` (non-zero, old-space)
3. gvar evaluates at `d_i` → produces the delta from old base to new default
4. Rendered glyph = old base + gvar delta = correct outline at new default

The base outlines do not match the named default, but the font renders
correctly in all avar2-capable engines. This is acceptable because:

- avar2 fonts inherently require avar processing for correct rendering.
- Stripping avar from an avar2 font breaks it regardless.
- Updating base values without renormalizing gvar is intractable (see §3).

### 8.6 Named Instances, STAT, name

Standard instancer handling — filter/update based on new axis ranges. No
avar2-specific changes needed.


## 9. Edge Cases

### 9.1 Self-Referencing Public Axes

If a public axis has avar v2 deltas targeting itself (designspace warping),
the rebased delta + offset still produces the correct old-space final
coordinate. The proof in §4.2 applies regardless of self-referencing.

### 9.2 Axis With Non-Trivial avar v1 Segment Map

The old intermediate values (`a_i`, `d_i`, `b_i`) are computed via the old
avar v1 segment map. The offset function is:

```
offset(z) = renormalize_to_inverse(z) - z
```

where `z` is the new-space intermediate coordinate (post-avar-v1-renorm).

**The three-entry decomposition is always exact**, regardless of avar v1
complexity. Here's why: `renormalize_to_inverse(z)` maps new-space
intermediate back to old-space intermediate. After standard avar v1
renormalization:

- At `z = -1`: old intermediate = `a_i`
- At `z = 0`: old intermediate = `d_i`
- At `z = +1`: old intermediate = `b_i`

`renormalize_to_inverse` is ALWAYS two-piece linear (one linear piece for
`z ∈ [-1, 0]`, another for `z ∈ [0, +1]`), because the standard
renormalization maps two linear segments (negative and positive sides) to
`[-1, 0]` and `[0, +1]` respectively. The inverse of a linear function is
linear, regardless of how complex the original avar v1 segment map is.

Therefore `offset(z) = renormalize_to_inverse(z) - z` is always two-piece
linear with at most one kink at `z = 0`. This is exactly representable by
three IVS entries (empty-region bias + two tents).

### 9.3 Multiple Restricted Axes

Each restricted axis gets its own offset compensation (bias + two tents). The
offsets are independent and per-axis. The IVS rebasing handles multi-axis
regions correctly (processing one axis at a time, as per standard instancer
behavior).

### 9.4 Clamping

The avar2 pseudocode clamps final coordinates to `[-1, +1]`. Since the offset
compensation produces `old_final[i]`, which was already in `[-1, +1]` in the
original font, clamping has no effect. Correct.

### 9.5 F2DOT14 Precision

Offset compensation values are in the range `[-2, +2]` (differences of
normalized coordinates in `[-1, +1]`). F2DOT14 can represent values in
`[-2.0, +1.99994]`. All offset values fit within this range.

### 9.6 Fonts With No avar v1 Segment Maps

If the original font has avar v2 but no avar v1 segment maps (empty segments),
the approach still works. The old intermediate values are simply the old
normalized values (`a_i = norm_old(new_min)`, etc.). The avar v1 instancer
may create new segment maps as needed.


## 10. Known Limitations

1. **Base values not updated.** The stored glyph outlines and metrics
   represent the original default, not the new default. This is inherent to
   the offset compensation approach — updating base values would require
   shifting gvar deltas, reintroducing the delta scaling problem. The font
   renders correctly but may confuse tools that inspect base values directly.

2. **Pinned axis removal is limited.** Only self-contained pinned axes (whose
   final coord doesn't vary with other axes) can be removed. Non-self-contained
   pinned axes are kept as hidden axes.


## 11. Future Work

### 11.1 Full Pinned Axis Removal

For non-self-contained pinned axes, investigate encoding the residual
variation as additional entries in other axes' delta sets.


## 12. Implementation

### Phase 1: Core — IMPLEMENTED

Modifications to `Lib/fontTools/varLib/instancer/__init__.py`:

1. **Removed `NotImplementedError`** in `AxisLimits.normalize()`.
   For avar2 partial instancing, computes normalized limits using avar v1 only
   (`renormalizeAxisLimits` with `versionOneOnly=True`).

2. **Modified `instantiateVariableFont()`**: detects avar2 fonts and skips
   gvar/HVAR/MVAR/CFF2/cvar/VARC/OTL/FeatureVariations instancing for
   non-self-contained axes. After avar instancing, runs variation instancing
   for self-contained pinned axes at their old-space final coordinates.

3. **Modify `instantiateAvar()`**: replace the WIP code with:
   a. Compute old intermediate values (`a_i`, `d_i`, `b_i`) before avar v1
      instancing.
   b. For avar2, keep identity segments for hidden pinned axes (compile()
      needs segment entries for all fvar axes).
   c. Run standard avar v1 instancing.
   d. Run `_instantiateAvarV2()`: rebase IVS, detect self-contained axes,
      add offset compensation, return self-contained axes dict.

4. **Handle VarIdxMap updates** for added/removed axes.

### Phase 2: Pinned Axes — IMPLEMENTED

5. **Self-containment detection** in `_instantiateAvarV2()`: after IVS rebasing,
   a pinned axis is self-contained if it has `NO_VARIATION_INDEX` or no remaining
   TupleVariation has a non-zero delta at its inner position. These axes' offset
   compensation is skipped.

6. **Selective variation instancing**: `instantiateVariableFont()` runs
   gvar/CFF2/cvar/MVAR/HVAR/VVAR/OTL/FeatureVariations instancing for
   self-contained axes, pinned at their old-space final coordinates.

7. **fvar update**: `_instantiateFvarForAvar2()` removes self-contained axes
   from fvar, updates VarIdxMap indices, removes avar segments. Non-self-
   contained pinned axes kept as hidden.

8. **VarRegionList alignment**: self-contained axes removed from
   `tupleVarStore.axisOrder` before building VarStore, so VarRegionList
   matches post-removal fvar axis count.

### Phase 3: Optimization — IMPLEMENTED

9. **Variation culling — IMPLEMENTED.** `_cullVariationsForAvar2()` removes
   dead variations whose axis regions fall outside the reachable old-space
   final-coord range. Applies to all variation tables:
   - **gvar/cvar**: removes dead TupleVariations.
   - **HVAR/VVAR/MVAR/GDEF**: converts IVS to TupleVariations, culls dead
     ones, converts back.
   - NO_VARIATION_INDEX axes: exact bounds [a_i, b_i] from `oldIntermediates`.
   - IVS axes: bounds from `getExtremes` on the instanced avar v2
     VarStore (including offset compensation). Private axes (originally hidden,
     not user-restricted) are pinned at (0,0,0) in axis limits because their
     intermediate coordinate is always 0, so regions referencing them get
     scalar = 0. This dramatically tightens bounds for parametric fonts.
   - `getExtremes` fixes: bias subtracted from VarStoreInstancer evaluations
     to avoid double-counting across recursion levels. Identity range always
     evaluated even when no region involves the identity axis.

10. Optimize IVS (merge regions, remove zero deltas) — not yet implemented.
