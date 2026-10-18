"""Fail-closed placement checker for original C //@ assert source annotation.

This is a parser-only location validator; it MUST NOT alter the original
source passed to Z3 or weaken existing original-C guards.
"""
from __future__ import annotations
import re

from pycparser import c_ast,c_parser

MARKER="__neumann_original_assert_site_marker__"
PATTERN=re.compile(r"^[ \t]*//@[ \t]*assert[ \t]*\((.+)\)[ \t]*;[ \t]*$")

class OriginalAssertionSiteError(ValueError):pass

def require_original_after_loop_assertion(code: str)->dict:
    """Accept only one standalone annotation at loop exit in main."""
    if MARKER in code:raise OriginalAssertionSiteError("MARKER_COLLISION_IN_SOURCE")
    lines=code.splitlines(keepends=True)
    matching=[]
    for n,line in enumerate(lines):
        m=PATTERN.fullmatch(line.rstrip("\r\n"))
        if m:matching.append((n,m.group(1)))
    if len(matching)!=1:raise OriginalAssertionSiteError("NOT_ONE_STANDALONE_ORIGINAL_ASSERTION")
    index,label=matching[0]
    lines[index]=re.sub(r"^[ \t]*//@.*$",f"{MARKER}();",
                        lines[index].rstrip("\r\n"))+(
                            "\n" if lines[index].endswith("\n") else "")
    modified="".join(lines)
    modified=re.sub(r"/\*.*?\*/","",modified,flags=re.S)
    modified=re.sub(r"//[^\n]*","",modified)
    pp=[l.strip() for l in modified.splitlines() if l.lstrip().startswith("#")]
    for p in pp:
        if not (p.startswith("#include <stdlib.h>") or
                p.startswith("#define assume(e) if(!(e)) exit(-1);")):
            raise OriginalAssertionSiteError("UNSUPPORTED_PREPROCESSOR")
    modified="\n".join(l for l in modified.splitlines() if not l.lstrip().startswith("#"))
    try:tree=c_parser.CParser().parse(modified)
    except Exception as ex:
        raise OriginalAssertionSiteError("SOURCE_ANNOTATION_SITE_PARSE_FAILURE: "+str(ex)[:130]) from ex
    mains=[e for e in tree.ext if isinstance(e,c_ast.FuncDef) and e.decl.name=="main"]
    if len(mains)!=1:raise OriginalAssertionSiteError("NO_UNIQUE_MAIN_FOR_SOURCE_ASSERTION")
    items=mains[0].body.block_items or []
    loops=[i for i,e in enumerate(items) if isinstance(e,(c_ast.While,c_ast.For))]
    if len(loops)!=1:raise OriginalAssertionSiteError("NOT_ONE_TOP_LEVEL_MAIN_LOOP")
    idx=loops[0]
    following=idx+1
    while following<len(items) and isinstance(items[following],c_ast.EmptyStatement):
        following+=1
    if following>=len(items):raise OriginalAssertionSiteError("ASSERTION_NOT_AFTER_MAIN_LOOP")
    stmt=items[following]
    if not (isinstance(stmt,c_ast.FuncCall) and
            isinstance(stmt.name,c_ast.ID) and stmt.name.name==MARKER and
            stmt.args is None):
        def is_marker(node):
            return (isinstance(node,c_ast.FuncCall) and
                    isinstance(node.name,c_ast.ID) and node.name.name==MARKER)
        top=[j for j,node in enumerate(items) if is_marker(node)]
        if len(top)==1 and top[0]<idx:
            detail="ASSERTION_BEFORE_MAIN_LOOP"
        elif len(top)==1 and top[0]>idx:
            detail="ASSERTION_AFTER_LOOP_BUT_NOT_IMMEDIATE"
        elif len(top)>1:
            detail="MULTIPLE_ASSERTION_ANCHORS"
        else:
            class Locator(c_ast.NodeVisitor):
                found=False
                def visit_FuncCall(self,node):
                    if is_marker(node):self.found=True
                    self.generic_visit(node)
            def inside(node):
                found=Locator();found.visit(node)
                return found.found
            if inside(items[idx]):
                detail="ASSERTION_NESTED_IN_MAIN_LOOP"
            elif any(inside(items[j]) for j in range(idx)):
                detail="ASSERTION_NESTED_BEFORE_MAIN_LOOP"
            elif any(inside(items[j]) for j in range(idx+1,len(items))):
                detail="ASSERTION_NESTED_AFTER_MAIN_LOOP"
            elif any(inside(e) for e in tree.ext if e is not mains[0]):
                detail="ASSERTION_IN_OTHER_FUNCTION_OR_GLOBAL_CONTEXT"
            else:
                detail="ASSERTION_SITE_UNRECOGNIZED_NOT_TOP_LEVEL_MAIN"
        raise OriginalAssertionSiteError(detail)
    # All normal original-source execution rules continue to be imposed by
    # model_original; this check is a strictly *additional* rejection gate.
    return {
        "marker_location":"IMMEDIATE_MAIN_LOOP_EXIT",
        "original_line_1based":index+1,
        "original_annotation_expression_length":len(label),
        "main_loop_kind":type(items[idx]).__name__,
    }
