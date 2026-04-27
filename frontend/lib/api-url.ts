const LOCAL_API_URL = "http://localhost:8000";
const PROD_FALLBACK_API_URL = "https://integrateai-backend.onrender.com";

const devApiUrl = process.env.NEXT_PUBLIC_API_URL_DEV?.trim();
const prodApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export const API_URL =
  process.env.NODE_ENV === "production"
    ? prodApiUrl || PROD_FALLBACK_API_URL
    : devApiUrl || LOCAL_API_URL;
