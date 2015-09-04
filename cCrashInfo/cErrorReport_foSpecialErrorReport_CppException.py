import re;

# Hide some functions at the top of the stack that are merely helper functions and not relevant to the error:
asHiddenTopFrames = [
  "KERNELBASE.dll!RaiseException",
  "msvcrt.dll!CxxThrowException",
  "msvcrt.dll!_CxxThrowException",
  "MSVCR110.dll!CxxThrowException",
  "MSVCR110.dll!_CxxThrowException",
]
# Some C++ exceptions may be out-of-memory errors.
dtxErrorTranslations = {
  "OOM": (
    "The process triggered a C++ exception to indicate it was unable to allocate enough memory",
    None,
    [
      [
        "KERNELBASE.dll!RaiseException",
        "msvcrt.dll!_CxxThrowException",
        "jscript9.dll!Js::Throw::OutOfMemory",
      ],
    ],
  ),
};

def cErrorReport_foSpecialErrorReport_CppException(oErrorReport, oCrashInfo):
  # Attempt to get the symbol of the virtual function table of the object that was thrown and add that the the type id:
  oException = oErrorReport.oException;
  assert len(oException.auParameters) >= 3, \
      "Expected a C++ Exception to have at least 3 parameters, got %d" % len(oException.auParameters);
  poException = oException.auParameters[1];
  asExceptionVFtablePointer = oCrashInfo._fasSendCommandAndReadOutput("dps 0x%X L1" % poException);
  if not oCrashInfo._bCdbRunning: return None;
  sCarriedLine = "";
  for sLine in asExceptionVFtablePointer:
    oExceptionVFtablePointerMatch = re.match(r"^[0-9A-F`]+\s*[0-9A-F`\?]+(?:\s+(.+))?\s*$", asExceptionVFtablePointer[0], re.I);
    assert oExceptionVFtablePointerMatch, "Unexpected dps result:\r\n%s" % "\r\n".join(asExceptionVFtablePointer);
    sExceptionObjectVFTablePointerSymbol = oExceptionVFtablePointerMatch.group(1);
    if sExceptionObjectVFTablePointerSymbol is None: break;
    sExceptionObjectSymbol = sExceptionObjectVFTablePointerSymbol.rstrip("::`vftable'");
    sCdbModuleId, sExceptionClassName = sExceptionObjectSymbol.split("!", 1);
    oErrorReport.sErrorTypeId += ":%s" % sExceptionClassName;
    break;
  oErrorReport.oStack.fHideTopFrames(asHiddenTopFrames);
  return oErrorReport.foTranslateError(dtxErrorTranslations);
