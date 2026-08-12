import { google } from "googleapis";

const keyFile =
  process.env.SERVICE_ACCOUNT_PATH ??
  "C:/02Workspaces/99CursorAI/symmetric-lore-504707-s0-bc9098aa1ff0.json";

const auth = new google.auth.GoogleAuth({
  keyFile,
  scopes: ["https://www.googleapis.com/auth/drive"],
});

const drive = google.drive({ version: "v3", auth });

const folders = await drive.files.list({
  pageSize: 20,
  q: "mimeType='application/vnd.google-apps.folder' and trashed=false",
  fields: "files(id,name,shared,owners)",
  supportsAllDrives: true,
  includeItemsFromAllDrives: true,
  corpora: "allDrives",
});

console.log("folders:", JSON.stringify(folders.data.files, null, 2));

const docs = await drive.files.list({
  pageSize: 20,
  q: "mimeType='application/vnd.google-apps.document' and trashed=false",
  fields: "files(id,name,shared,parents)",
});

console.log("docs:", JSON.stringify(docs.data.files, null, 2));

const sheets = await drive.files.list({
  pageSize: 20,
  q: "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
  fields: "files(id,name,shared,parents)",
});

console.log("sheets:", JSON.stringify(sheets.data.files, null, 2));
