/**
 * DealHunter - Webhook de suivi des achats/reventes
 *
 * INSTALLATION :
 * 1. Crée un Google Sheet vide, renomme la première feuille "Achats".
 * 2. Ligne 1 (en-têtes) : id | date | titre | site | prix_achat | url |
 *    image | etat | prix_revente_suggere | statut | annonce_titre |
 *    annonce_description | prix_conseille
 * 3. Extensions > Apps Script, colle ce fichier entier (remplace le contenu).
 * 4. Déployer > Nouveau déploiement > Type "Application Web".
 *    - Exécuter en tant que : Moi
 *    - Qui a accès : Tout le monde
 * 5. Copie l'URL du déploiement -> variable d'env GOOGLE_SHEET_WEBHOOK_URL
 *    sur le service Render de DealHunter.
 */

const SHEET_NAME = "Achats";

function getSheet_() {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
}

function doPost(e) {
  const body = JSON.parse(e.postData.contents);
  const action = body.action;

  if (action === "log_achat") {
    return logAchat_(body.data);
  }
  if (action === "update_achat") {
    return updateAchat_(body.id, body.data);
  }
  return jsonOut_({ ok: false, error: "action inconnue" });
}

function doGet(e) {
  const action = e.parameter.action;
  if (action === "list_achats") {
    return jsonOut_({ achats: listAchats_() });
  }
  return jsonOut_({ error: "action inconnue" });
}

function logAchat_(data) {
  const sheet = getSheet_();
  const id = Utilities.getUuid();
  sheet.appendRow([
    id,
    new Date().toISOString(),
    data.titre || "",
    data.site || "",
    data.prix_achat || "",
    data.url || "",
    data.image || "",
    data.etat || "",
    data.prix_revente_suggere || "",
    "a_revendre",
    "", "", "",
  ]);
  return jsonOut_({ ok: true, id: id });
}

function updateAchat_(id, updates) {
  const sheet = getSheet_();
  const values = sheet.getDataRange().getValues();
  const headers = values[0];
  const idCol = headers.indexOf("id");

  for (let i = 1; i < values.length; i++) {
    if (values[i][idCol] === id) {
      Object.keys(updates).forEach((key) => {
        const col = headers.indexOf(key);
        if (col !== -1) sheet.getRange(i + 1, col + 1).setValue(updates[key]);
      });
      return jsonOut_({ ok: true });
    }
  }
  return jsonOut_({ ok: false, error: "id introuvable" });
}

function listAchats_() {
  const sheet = getSheet_();
  const values = sheet.getDataRange().getValues();
  const headers = values[0];
  const rows = values.slice(1);

  return rows.map((row) => {
    const obj = {};
    headers.forEach((h, i) => (obj[h] = row[i]));
    return obj;
  });
}

function jsonOut_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
