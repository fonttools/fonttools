from ._h_h_e_a import hheaFormat, table__h_h_e_a


class table_H_H_E_A_(table__h_h_e_a):
    dependencies = ["HMTX", "GLYF", "CFF ", "CFF2"]
    tableFormat = hheaFormat.replace(
        "numberOfHMetrics:       H", "numberOfHMetrics:       L"
    )
    glyphTableTag = "GLYF"
    metricsTableTag = "HMTX"
    outlineTags = ("GLYF", "CFF ", "CFF2")
