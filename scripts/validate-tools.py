#!/usr/bin/env python3
"""
validate-tools.py - Validacao rapida de suporte a tool use via API Ollama.
Uso: python3 scripts/validate-tools.py <model_name>

Anti-pattern documentado: deepseek-r1:8b tinha tag mas retornava erro 400.
"""

import sys
import json
import urllib.request
import urllib.error
import time

OLLAMA_API = "http://localhost:11434/api/chat"

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "get_system_status",
        "description": "Retorna o status atual do sistema.",
        "parameters": {
            "type": "object",
            "properties": {
                "component": {
                    "type": "string",
                    "description": "Componente a verificar: cpu, memory ou disk"
                }
            },
            "required": ["component"]
        }
    }
}

PROMPT = "Verifique o status de memoria do sistema usando a ferramenta disponivel."

def validate(model):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "tools": [TOOL_DEF],
        "stream": False,
        "options": {"temperature": 0}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            elapsed = round(time.time() - t0, 2)
            result = json.loads(resp.read())
            message = result.get("message", {})
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                fn = tool_calls[0].get("function", {})
                return {
                    "status": "PASS",
                    "tool": fn.get("name", "?"),
                    "args": fn.get("arguments", {}),
                    "elapsed_s": elapsed
                }
            else:
                content = message.get("content", "")[:150]
                return {"status": "FAIL - sem tool_calls", "response": content, "elapsed_s": elapsed}
    except urllib.error.HTTPError as e:
        return {"status": f"ERRO HTTP {e.code}", "detail": e.reason, "elapsed_s": round(time.time() - t0, 2)}
    except Exception as e:
        return {"status": "ERRO", "detail": str(e), "elapsed_s": round(time.time() - t0, 2)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 validate-tools.py <model_name>")
        sys.exit(1)
    model = sys.argv[1]
    print(f"\n{'='*55}")
    print(f" VALIDACAO TOOL USE: {model}")
    print(f"{'='*55}")
    r = validate(model)
    if "PASS" in r["status"]:
        print(f" OK  tool chamada : {r['tool']}")
        print(f"     argumentos   : {r['args']}")
    else:
        print(f" FALHA: {r['status']}")
        detail = r.get("response") or r.get("detail", "")
        if detail:
            print(f"     detalhe: {detail}")
    print(f" tempo: {r['elapsed_s']}s")
    print(f"{'='*55}\n")
