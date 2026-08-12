import { google } from "googleapis";
import { assertServiceAccountDestination, config, getServiceAccountEmail } from "./config.js";
import { DocsMcpClient, pickDocumentId } from "./mcpClient.js";
import type { AuthMode, PublishResult } from "./types.js";

function docUrl(docId: string): string {
  return `https://docs.google.com/document/d/${docId}/edit`;
}

async function getGoogleClients() {
  const auth = new google.auth.GoogleAuth({
    keyFile: config.serviceAccountPath,
    scopes: [
      "https://www.googleapis.com/auth/documents",
      "https://www.googleapis.com/auth/drive",
    ],
  });

  return {
    drive: google.drive({ version: "v3", auth }),
    docs: google.docs({ version: "v1", auth }),
  };
}

async function replaceDocContentGoogleApi(docId: string, markdown: string): Promise<void> {
  const { docs } = await getGoogleClients();
  const doc = await docs.documents.get({ documentId: docId });
  const body = doc.data.body?.content ?? [];
  const last = body[body.length - 1];
  const endIndex = (last?.endIndex ?? 1) - 1;

  const requests = [];
  if (endIndex > 1) {
    requests.push({
      deleteContentRange: {
        range: { startIndex: 1, endIndex },
      },
    });
  }

  if (markdown.length > 0) {
    requests.push({
      insertText: {
        location: { index: 1 },
        text: markdown,
      },
    });
  }

  if (requests.length > 0) {
    await docs.documents.batchUpdate({
      documentId: docId,
      requestBody: { requests },
    });
  }
}

function storageQuotaHelp(): string {
  return [
    "Service Account는 Drive 저장 용량이 없어 새 문서를 만들 수 없습니다.",
    "빈 Google Doc를 본인 Drive에 만든 뒤",
    `${getServiceAccountEmail()} 에 Editor로 공유하고`,
    ".env 에 DOCS_TARGET_DOC_ID=<문서ID> 를 설정하세요.",
  ].join(" ");
}

async function publishViaGoogleApi(title: string, markdown: string): Promise<PublishResult> {
  assertServiceAccountDestination();

  if (config.docsTargetDocId) {
    await replaceDocContentGoogleApi(config.docsTargetDocId, markdown);
    return {
      docId: config.docsTargetDocId,
      docUrl: docUrl(config.docsTargetDocId),
      title,
      authMode: "service_account",
    };
  }

  if (!config.docsFolderId) {
    throw new Error(`DOCS_FOLDER_ID 가 필요합니다. 공유 대상: ${getServiceAccountEmail()}`);
  }

  const { drive } = await getGoogleClients();
  let created;
  try {
    created = await drive.files.create({
      requestBody: {
        name: title,
        mimeType: "application/vnd.google-apps.document",
        parents: [config.docsFolderId],
      },
      fields: "id",
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (message.includes("File not found")) {
      throw new Error(
        [
          `Drive 폴더를 찾을 수 없습니다: ${config.docsFolderId}`,
          `폴더를 ${getServiceAccountEmail()} 에 Editor로 공유했는지 확인하세요.`,
        ].join(" "),
      );
    }
    if (message.includes("storage quota") || message.includes("storageQuotaExceeded")) {
      throw new Error(storageQuotaHelp());
    }
    throw error;
  }

  const docId = created.data.id;
  if (!docId) {
    throw new Error("Google Drive API did not return a document id");
  }

  if (markdown.length > 0) {
    await replaceDocContentGoogleApi(docId, markdown);
  }

  return {
    docId,
    docUrl: docUrl(docId),
    title,
    authMode: "service_account",
  };
}

async function publishViaMcp(title: string, markdown: string): Promise<PublishResult> {
  const client = new DocsMcpClient();
  await client.connect();

  try {
    let docId = config.docsTargetDocId;

    if (!docId) {
      const createArgs: Record<string, unknown> = { title };
      if (config.docsFolderId) {
        createArgs.parentFolderId = config.docsFolderId;
      }

      const created = await client.callTool("createDocument", createArgs);
      if (created && typeof created === "object" && "raw" in created) {
        const raw = String((created as { raw?: unknown }).raw ?? "");
        if (raw.includes("Parent folder not found")) {
          throw new Error(
            [
              `Drive 폴더를 찾을 수 없습니다: ${config.docsFolderId}`,
              `폴더를 ${getServiceAccountEmail()} 에 Editor로 공유했는지 확인하세요.`,
            ].join(" "),
          );
        }
        if (
          raw.includes("storage quota") ||
          raw.includes("Permission denied") ||
          raw.includes("storageQuotaExceeded")
        ) {
          throw new Error(storageQuotaHelp());
        }
        throw new Error(raw || "createDocument failed");
      }

      docId = pickDocumentId(created);
      if (!docId) {
        throw new Error(`createDocument did not return documentId: ${JSON.stringify(created)}`);
      }
    }

    if (markdown.length > 0) {
      await client.callTool("replaceDocumentWithMarkdown", {
        documentId: docId,
        markdown,
      });
    }

    return {
      docId,
      docUrl: docUrl(docId),
      title,
      authMode: config.authMode,
    };
  } finally {
    await client.close();
  }
}

export async function publishMarkdownDocument(
  title: string,
  markdown: string,
): Promise<PublishResult> {
  if (config.authMode === "oauth") {
    return publishViaMcp(title, markdown);
  }

  assertServiceAccountDestination();

  try {
    return await publishViaGoogleApi(title, markdown);
  } catch (googleError) {
    console.warn("[publish] googleapis failed, trying MCP:", googleError);
    return publishViaMcp(title, markdown);
  }
}

export async function verifyMcpTools(): Promise<string[]> {
  const client = new DocsMcpClient();
  await client.connect();
  try {
    return await client.listTools();
  } finally {
    await client.close();
  }
}

export function describeAuthMode(): AuthMode {
  return config.authMode;
}
