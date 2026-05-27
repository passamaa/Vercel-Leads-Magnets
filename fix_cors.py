with open('api/submit.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Ajouter CORS headers dans la fonction json()
c = c.replace(
    "headers: { 'content-type': 'application/json; charset=utf-8' }",
    "headers: { 'content-type': 'application/json; charset=utf-8', 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type' }"
)

# Gérer preflight OPTIONS
c = c.replace(
    "  if (request.method !== 'POST') {",
    "  if (request.method === 'OPTIONS') {\n    return new Response(null, { status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type' }});\n  }\n  if (request.method !== 'POST') {"
)

with open('api/submit.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('access-control-allow-origin count:', c.count('access-control-allow-origin'))
