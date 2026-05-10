function readStringEnv(name, fallback) {
  const value = process.env[name];
  if (typeof value !== "string" || value.trim() === "") {
    return fallback;
  }

  return value.trim();
}

function readPortEnv(name, fallback) {
  const value = process.env[name];
  if (typeof value !== "string" || value.trim() === "") {
    return fallback;
  }

  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65535) {
    throw new Error(`Invalid env var '${name}'. Expected integer from 1 to 65535.`);
  }

  return parsed;
}

export function getFrontendRuntimeConfig() {
  return {
    host: readStringEnv("FRONTEND_HOST", "0.0.0.0"),
    port: readPortEnv("FRONTEND_PORT", 3000),
    backendProxyUrl: readStringEnv("BACKEND_PROXY_URL", "http://localhost:8000"),
  };
}
