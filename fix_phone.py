with open('api/submit.js', 'r', encoding='utf-8') as f:
    c = f.read()

old = "const cleanPhone = (phone || '').replace(/[^\\d+]/g, '');"
new = """const rawPhone = (phone || '').replace(/[^\\d+]/g, '');
  let cleanPhone = rawPhone;
  if (rawPhone.match(/^0[0-9]/)) {
    cleanPhone = '+33' + rawPhone.slice(1);
  }"""

c = c.replace(old, new)

with open('api/submit.js', 'w', encoding='utf-8') as f:
    f.write(c)
print('OK:', 'cleanPhone' in c)
