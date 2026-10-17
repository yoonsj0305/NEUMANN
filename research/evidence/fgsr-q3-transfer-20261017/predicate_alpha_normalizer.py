"""Source-neutral, fail-closed Horn relation alpha normalizer.

Transforms *only* Int... -> Bool predicate names, preserving original source
by returning a copy and a reversible rename map. Does not invent semantic
operator categories, new lemmas, or variable relations.
"""
import re

TOKEN = re.compile(r'\|(?:\\.|[^|])*\||;[^\n]*|\s+|[()]|[^\s();]+')
DECL = re.compile(r'\(\s*declare-fun\s+(\|(?:\\.|[^|])*\||[^\s()]+)\s*\(\s*([^)]*?)\s*\)\s+Bool\s*\)', re.S)

class UnsupportedSource(ValueError): pass

def unquote(t):
    return t[1:-1] if t.startswith('|') and t.endswith('|') else t

def _rename_tokens(source, old_to_new):
    def conv(m):
        token=m.group(0)
        if token.startswith(';') or token.isspace():return token
        target=old_to_new.get(unquote(token))
        return '|'+target+'|' if target is not None else token
    return TOKEN.sub(conv,source)

def normalize(source):
    seen=[];names={}
    for m in DECL.finditer(source):
        symbol=unquote(m.group(1));domains=m.group(2).split()
        if not domains:continue
        if any(sort!='Int' for sort in domains):
            raise UnsupportedSource('non-Int predicate domain: '+symbol)
        if symbol in names:raise UnsupportedSource('duplicate predicate declaration')
        name='inv_r'+str(len(seen))
        if name in source:raise UnsupportedSource('reserved canonical name collision')
        seen.append({'original_symbol':symbol,'canonical_symbol':name,'arity':len(domains)})
        names[symbol]=name
    if not seen:raise UnsupportedSource('no positive-arity Int predicate declarations')
    # A relation symbol must not be re-bound as a quantified local variable.
    for old in names:
        escaped=re.escape(old)
        if re.search(r'\(\s*\|?'+escaped+r'\|?\s+(?:Int|Bool)\s*\)',source):
            raise UnsupportedSource('predicate/variable shadowing')
    rendered=_rename_tokens(source,names)
    inverse={x['canonical_symbol']:x['original_symbol'] for x in seen}
    if _rename_tokens(rendered,inverse).replace('|','')!=source.replace('|',''):
        raise UnsupportedSource('not alpha reversible')
    return rendered,seen

def restore_definitions(definitions,mapping):
    inverse={x['canonical_symbol']:x['original_symbol'] for x in mapping}
    return _rename_tokens(definitions,inverse)
