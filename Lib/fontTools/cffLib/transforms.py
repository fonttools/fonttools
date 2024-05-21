from fontTools.misc.psCharStrings import SimpleT2Decompiler


class StopHintCountEvent(Exception):
    pass


class _DesubroutinizingT2Decompiler(SimpleT2Decompiler):
    stop_hintcount_ops = (
        "op_hintmask",
        "op_cntrmask",
        "op_rmoveto",
        "op_hmoveto",
        "op_vmoveto",
    )

    def __init__(self, localSubrs, globalSubrs, private=None):
        SimpleT2Decompiler.__init__(self, localSubrs, globalSubrs, private)

    def execute(self, charString):
        self.need_hintcount = True  # until proven otherwise
        for op_name in self.stop_hintcount_ops:
            setattr(self, op_name, self.stop_hint_count)

        if hasattr(charString, "_desubroutinized"):
            # If a charstring has already been desubroutinized, we will still
            # need to execute it if we need to count hints in order to
            # compute the byte length for mask arguments, and haven't finished
            # counting hints pairs.
            if self.need_hintcount and self.callingStack:
                try:
                    SimpleT2Decompiler.execute(self, charString)
                except StopHintCountEvent:
                    del self.callingStack[-1]
            return

        charString._patches = []
        SimpleT2Decompiler.execute(self, charString)
        desubroutinized = charString.program[:]
        for idx, expansion in reversed(charString._patches):
            assert idx >= 2
            assert desubroutinized[idx - 1] in [
                "callsubr",
                "callgsubr",
            ], desubroutinized[idx - 1]
            assert type(desubroutinized[idx - 2]) == int
            if expansion[-1] == "return":
                expansion = expansion[:-1]
            desubroutinized[idx - 2 : idx] = expansion
        if not self.private.in_cff2:
            if "endchar" in desubroutinized:
                # Cut off after first endchar
                desubroutinized = desubroutinized[
                    : desubroutinized.index("endchar") + 1
                ]

        charString._desubroutinized = desubroutinized
        del charString._patches

    def op_callsubr(self, index):
        subr = self.localSubrs[self.operandStack[-1] + self.localBias]
        SimpleT2Decompiler.op_callsubr(self, index)
        self.processSubr(index, subr)

    def op_callgsubr(self, index):
        subr = self.globalSubrs[self.operandStack[-1] + self.globalBias]
        SimpleT2Decompiler.op_callgsubr(self, index)
        self.processSubr(index, subr)

    def stop_hint_count(self, *args):
        self.need_hintcount = False
        for op_name in self.stop_hintcount_ops:
            setattr(self, op_name, None)
        cs = self.callingStack[-1]
        if hasattr(cs, "_desubroutinized"):
            raise StopHintCountEvent()

    def op_hintmask(self, index):
        SimpleT2Decompiler.op_hintmask(self, index)
        if self.need_hintcount:
            self.stop_hint_count()

    def processSubr(self, index, subr):
        cs = self.callingStack[-1]
        if not hasattr(cs, "_desubroutinized"):
            cs._patches.append((index, subr._desubroutinized))


def desubroutinize(cff):
    for fontName in cff.fontNames:
        font = cff[fontName]
        cs = font.CharStrings
        for c in cs.values():
            c.decompile()
            subrs = getattr(c.private, "Subrs", [])
            decompiler = _DesubroutinizingT2Decompiler(subrs, c.globalSubrs, c.private)
            decompiler.execute(c)
            c.program = c._desubroutinized
            del c._desubroutinized
        # Delete all the local subrs
        if hasattr(font, "FDArray"):
            for fd in font.FDArray:
                pd = fd.Private
                if hasattr(pd, "Subrs"):
                    del pd.Subrs
                if "Subrs" in pd.rawDict:
                    del pd.rawDict["Subrs"]
        else:
            pd = font.Private
            if hasattr(pd, "Subrs"):
                del pd.Subrs
            if "Subrs" in pd.rawDict:
                del pd.rawDict["Subrs"]
    # as well as the global subrs
    cff.GlobalSubrs.clear()
