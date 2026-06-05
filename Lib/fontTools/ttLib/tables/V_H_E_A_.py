from ._v_h_e_a import table__v_h_e_a, vheaFormat


class table_V_H_E_A_(table__v_h_e_a):
    dependencies = ["VMTX", "GLYF"]
    tableFormat = vheaFormat.replace("numberOfVMetrics:\tH", "numberOfVMetrics:\tL")
    glyphTableTag = "GLYF"
    metricsTableTag = "VMTX"
    outlineTags = ("GLYF",)
