import { NextRequest } from "next/server";

import { getAppConfig } from "@/server/read-config.mjs";

export const runtime = "nodejs";

function backendUrl(path: string[]): string {
  const backendProxyTarget = getAppConfig().frontend.backend_proxy_url;
  const baseUrl = backendProxyTarget.replace(/\/$/, "");
  return `${baseUrl}/api/${path.map(encodeURIComponent).join("/")}`;
}

async function proxyRequest(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const targetUrl = new URL(backendUrl(path));
  targetUrl.search = request.nextUrl.search;

  const response = await fetch(targetUrl, {
    method: request.method,
    headers: request.headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : request.body,
    duplex: "half",
  } as RequestInit);

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
