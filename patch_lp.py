def patch(filename, lead_magnet, pdf, pdf_name, ls_sub, ls_dis):
    with open(filename, 'r', encoding='utf-8') as f:
        c = f.read()

    c = c.replace('<script charset="utf-8" src="//js-eu1.hsforms.net/forms/embed/v2.js" type="text/javascript"></script>\n', '')

    idx = -1
    for tag in [
        '<script>\n/* ============================================================\n   INT\u00c9GRATION HUBSPOT',
        '<script>\n/* ============================================================\n   INTEGRATION HUBSPOT'
    ]:
        idx = c.find(tag)
        if idx != -1:
            break

    snippet = """<script>
const BREVO_CONFIG = {{
  WORKER_ENDPOINT: '/api/submit',
  LEAD_MAGNET: '{lead}',
  PAGE_NAME: 'Methode {LEAD} - Manuel Ravier',
  PDF_URL: '{pdf}',
  PDF_DOWNLOAD_NAME: '{pdf_name}',
  LS_SUBMITTED_KEY: '{ls_sub}',
  LS_DISMISSED_KEY: '{ls_dis}'
}};
function triggerPDFDownload(){{if(!BREVO_CONFIG.PDF_URL)return;var a=document.createElement('a');a.href=BREVO_CONFIG.PDF_URL;a.download=BREVO_CONFIG.PDF_DOWNLOAD_NAME;a.target='_blank';a.rel='noopener';document.body.appendChild(a);a.click();document.body.removeChild(a);}}
function submitToBrevo(event,formEl){{event.preventDefault();var isPopup=formEl.dataset.brevoForm==='popup';var feedback=isPopup?document.getElementById('popup-feedback'):ensureInlineFeedback(formEl);feedback.className='form-feedback';feedback.textContent='Envoi en cours...';var data=new FormData(formEl);var payload={{firstname:(data.get('firstname')||'').trim(),lastname:(data.get('lastname')||'').trim(),email:(data.get('email')||'').trim().toLowerCase(),phone:(data.get('phone')||'').trim(),leadMagnet:BREVO_CONFIG.LEAD_MAGNET,pageUri:window.location.href,pageName:BREVO_CONFIG.PAGE_NAME,honeypot:(data.get('website')||'').trim()}};triggerPDFDownload();fetch(BREVO_CONFIG.WORKER_ENDPOINT,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}}).then(function(r){{return r.json().then(function(body){{if(!r.ok)throw {{status:r.status,body:body}};return body;}});}}).then(function(){{showSuccess(feedback,isPopup?closeLeadPopup:null);}}).catch(function(err){{feedback.classList.add('is-error');feedback.textContent='Une erreur est survenue. Veuillez reessayer.';}});return false;}}
function showSuccess(f,cb){{f.classList.add('is-success');f.textContent='Merci ! Votre guide est en telechargement. Vous allez recevoir un email de confirmation dans la minute.';try{{localStorage.setItem(BREVO_CONFIG.LS_SUBMITTED_KEY,'1');}}catch(e){{}}if(cb)setTimeout(cb,1800);}}
function ensureInlineFeedback(f){{var fb=f.querySelector('.form-feedback');if(!fb){{fb=document.createElement('div');fb.className='form-feedback';fb.setAttribute('role','status');fb.setAttribute('aria-live','polite');f.appendChild(fb);}}return fb;}}
var POPUP_DELAY_MS=8000;
function openLeadPopup(){{var o=document.getElementById('lead-popup');if(!o)return;o.classList.add('is-open');o.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';}}
function closeLeadPopup(){{var o=document.getElementById('lead-popup');if(!o)return;o.classList.remove('is-open');o.setAttribute('aria-hidden','true');document.body.style.overflow='';try{{localStorage.setItem(BREVO_CONFIG.LS_DISMISSED_KEY,String(Date.now()));}}catch(e){{}}}}
function setupPopupListeners(){{var cb=document.getElementById('popup-close');if(cb)cb.addEventListener('click',closeLeadPopup);var o=document.getElementById('lead-popup');if(o){{o.addEventListener('click',function(e){{if(e.target===o)closeLeadPopup();}});}}document.addEventListener('keydown',function(e){{if(e.key==='Escape'){{var o=document.getElementById('lead-popup');if(o&&o.classList.contains('is-open'))closeLeadPopup();}}}});}}
(function initPopup(){{if(/[?&]testpopup/.test(window.location.search)){{setTimeout(openLeadPopup,1000);setupPopupListeners();return;}}try{{if(localStorage.getItem(BREVO_CONFIG.LS_SUBMITTED_KEY)==='1')return;var d=parseInt(localStorage.getItem(BREVO_CONFIG.LS_DISMISSED_KEY)||'0',10);if(d&&(Date.now()-d)<86400000)return;}}catch(e){{}}setTimeout(openLeadPopup,POPUP_DELAY_MS);setupPopupListeners();}})();
</script>
</body></html>""".format(lead=lead_magnet, LEAD=lead_magnet.upper(), pdf=pdf, pdf_name=pdf_name, ls_sub=ls_sub, ls_dis=ls_dis)

    new_c = c[:idx] + snippet
    new_c = new_c.replace('data-hubspot-form="inline"', 'data-brevo-form="inline"')
    new_c = new_c.replace('data-hubspot-form="popup"', 'data-brevo-form="popup"')
    new_c = new_c.replace('onsubmit="return submitToHubSpot(event, this);"', 'onsubmit="return submitToBrevo(event, this);"')

    honeypot = '\n<input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">'
    pos = 0
    for _ in range(2):
        p = new_c.find('</form>', pos)
        if p == -1:
            break
        new_c = new_c[:p] + honeypot + new_c[p:]
        pos = p + len(honeypot) + 7 + 1

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_c)

    print(filename + ': submitToBrevo=' + str(new_c.count('submitToBrevo')) + ' HubSpot=' + str(new_c.count('hsforms.net')))

patch('La_Methode_STRUCTURE_6.html','structure','guide-structure.pdf','La-Methode-STRUCTURE-Manuel-Ravier.pdf','il_lead_submitted_structure_v3','il_popup_dismissed_structure_v3')
patch('La_Methode_TRUST_6.html','trust','guide-trust.pdf','La-Methode-TRUST-Manuel-Ravier.pdf','il_lead_submitted_trust_v3','il_popup_dismissed_trust_v3')
