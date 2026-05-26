/* ================================================================
   BREVO PROXY — Vercel Edge Function
   ----------------------------------------------------------------
   Endpoint : POST /api/submit (depuis les LP du même domaine)
   Rôle     : reçoit le formulaire, crée/maj contact Brevo, l'ajoute
              à la liste qui déclenche le workflow nurturing, envoie
              l'email transactionnel immédiat avec le PDF en lien.

   Pourquoi Edge Runtime ?
   - Latence basse (~50ms cold start vs ~300ms Node.js)
   - API fetch native (même code que le Worker)
   - Gratuit dans le plan Hobby (jusqu'à 500k req/mois)

   Secrets à configurer dans Vercel Dashboard → Settings → Environment Variables :
     BREVO_API_KEY        — clé API v3 (xkeysib-...)
     PDF_BASE_URL         — ex: https://lp.investissement-locatif.com
                            (laisse vide si les PDF sont à la racine du même domaine)

   Pas de variable ALLOWED_ORIGINS : comme l'API est sur le même
   domaine que les LP (Vercel sert les deux), il n'y a pas de CORS.
   ================================================================ */

export const config = {
  runtime: 'edge'
};

const LEAD_MAGNETS = {
  structure: {
    listId: 296,                           // TODO Benjamin : remplir après création liste Brevo
    pdfFilename: 'guide-structure.pdf',
    pdfDownloadName: 'La-Methode-STRUCTURE-Manuel-Ravier.pdf',
    welcomeTemplateId: 323,                // TODO Benjamin : remplir après création template
    pageLabel: 'Méthode STRUCTURE'
  },
  trust: {
    listId: 308,                           // TODO Benjamin
    pdfFilename: 'guide-trust.pdf',
    pdfDownloadName: 'La-Methode-TRUST-Manuel-Ravier.pdf',
    welcomeTemplateId: 323,                // TODO Benjamin
    pageLabel: 'Méthode TRUST'
  }
};

const BREVO_API = 'https://api.brevo.com/v3';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

export default async function handler(request) {
  // GET / = health check
  if (request.method === 'GET') {
    return json({ ok: true, service: 'brevo-proxy-il' });
  }

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type' }});
  }
  if (request.method !== 'POST') {
    return json({ error: 'method_not_allowed' }, 405);
  }

  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return json({ error: 'invalid_json' }, 400);
  }

  const { firstname, lastname, email, phone, leadMagnet, pageUri, honeypot } = payload || {};

  // Anti-spam : honeypot doit être vide
  if (honeypot) {
    console.warn('[brevo-proxy] honeypot filled, dropping silently:', email);
    return json({ ok: true, dropped: true });
  }

  // Validation
  if (!email || !EMAIL_RE.test(email)) {
    return json({ error: 'invalid_email' }, 400);
  }
  if (!firstname || firstname.length < 2 || firstname.length > 80) {
    return json({ error: 'invalid_firstname' }, 400);
  }
  if (!leadMagnet || !LEAD_MAGNETS[leadMagnet]) {
    return json({ error: 'invalid_lead_magnet', allowed: Object.keys(LEAD_MAGNETS) }, 400);
  }

  const config = LEAD_MAGNETS[leadMagnet];
  const rawPhone = (phone || '').replace(/[^\d+]/g, '');
  let cleanPhone = rawPhone;
  if (rawPhone.match(/^0[0-9]/)) {
    cleanPhone = '+33' + rawPhone.slice(1);
  }
  const BREVO_API_KEY = process.env.BREVO_API_KEY;
  const PDF_BASE_URL = process.env.PDF_BASE_URL || 'https://lp.investissement-locatif.com';

  if (!BREVO_API_KEY) {
    console.error('[brevo-proxy] BREVO_API_KEY missing in env');
    return json({ error: 'server_misconfigured' }, 500);
  }

  // 1. UPSERT contact dans Brevo
  const contactPayload = {
    email: email.toLowerCase().trim(),
    attributes: {
      PRENOM: firstname.trim(),
      NOM: (lastname || '').trim(),
      
      SOURCE_LP: config.pageLabel,
      DATE_OPTIN: new Date().toISOString()
    },
    listIds: [config.listId].filter(Boolean),
    updateEnabled: true
  };

  let contactRes;
  try {
    contactRes = await fetch(`${BREVO_API}/contacts`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'content-type': 'application/json',
        'api-key': BREVO_API_KEY
      },
      body: JSON.stringify(contactPayload)
    });
  } catch (e) {
    console.error('[brevo-proxy] contact fetch failed:', e.message);
    return json({ error: 'brevo_unreachable' }, 502);
  }

  const contactBody = await safeJson(contactRes);

  const contactOk =
    contactRes.status === 201 ||
    contactRes.status === 204 ||
    (contactRes.status === 400 && /exist/i.test(JSON.stringify(contactBody || '')));

  if (!contactOk) {
    console.error('[brevo-proxy] contact upsert failed:', contactRes.status, contactBody);
    return json({ error: 'brevo_contact_failed', status: contactRes.status, detail: contactBody }, 502);
  }

  // Si contact pré-existant, on force son ajout à la liste pour déclencher le workflow
  if (contactRes.status === 400 && config.listId) {
    try {
      await fetch(`${BREVO_API}/contacts/lists/${config.listId}/contacts/add`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'content-type': 'application/json',
          'api-key': BREVO_API_KEY
        },
        body: JSON.stringify({ emails: [email.toLowerCase().trim()] })
      });
    } catch (e) {
      console.warn('[brevo-proxy] list add fallback failed:', e.message);
    }
  }

  // 2. Email transactionnel immédiat avec le PDF en lien (pas en pièce jointe)
  if (config.welcomeTemplateId) {
    const pdfUrl = `${PDF_BASE_URL}/${config.pdfFilename}`;
    const txEmailPayload = {
      to: [{ email: email.toLowerCase().trim(), name: `${firstname} ${lastname || ''}`.trim() }],
      templateId: config.welcomeTemplateId,
      params: {
        PRENOM: firstname.trim(),
        PDF_URL: pdfUrl,
        PDF_NAME: config.pdfDownloadName,
        PAGE_LABEL: config.pageLabel
      },
      tags: ['lead-magnet', leadMagnet, 'welcome'],
      attachment: [
        {
          url: `${PDF_BASE_URL}/${config.pdfFilename}`,
          name: config.pdfDownloadName
        }
      ]
    };

    try {
      const txRes = await fetch(`${BREVO_API}/smtp/email`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'content-type': 'application/json',
          'api-key': BREVO_API_KEY
        },
        body: JSON.stringify(txEmailPayload)
      });
      if (!txRes.ok) {
        const txBody = await safeJson(txRes);
        console.warn('[brevo-proxy] tx email failed:', txRes.status, txBody);
        // On ne bloque pas l'utilisateur : le contact est créé, le workflow tournera
      }
    } catch (e) {
      console.warn('[brevo-proxy] tx email exception:', e.message);
    }
  }

  return json({ ok: true, leadMagnet, listId: config.listId });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'access-control-allow-origin': '*', 'access-control-allow-methods': 'POST, OPTIONS', 'access-control-allow-headers': 'content-type' }
  });
}

async function safeJson(res) {
  try { return await res.json(); }
  catch (e) {
    try { return { _raw: await res.text() }; }
    catch (e2) { return null; }
  }
}
