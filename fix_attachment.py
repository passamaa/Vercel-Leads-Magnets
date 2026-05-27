with open('api/submit.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Ajouter l'attachement PDF dans le payload de l'email transactionnel
old = """      tags: ['lead-magnet', leadMagnet, 'welcome']"""
new = """      tags: ['lead-magnet', leadMagnet, 'welcome'],
      attachment: [
        {
          url: `${PDF_BASE_URL}/${config.pdfFilename}`,
          name: config.pdfDownloadName
        }
      ]"""

c = c.replace(old, new)

with open('api/submit.js', 'w', encoding='utf-8') as f:
    f.write(c)
print('OK:', 'attachment' in c)
