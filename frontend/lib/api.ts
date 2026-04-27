import { API_URL } from "@/lib/api-url";

async function sendChatMessage(message: string) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  
  if (!response.ok) throw new Error("Failed to send message");
  return response.json();
}

async function getIntegrations() {
  const response = await fetch(`${API_URL}/integrations`);
  if (!response.ok) throw new Error("Failed to fetch integrations");
  return response.json();
}

async function triggerSync(integrationId: string) {
  const response = await fetch(`${API_URL}/sync/${integrationId}/trigger`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to trigger sync");
  return response.json();
}


export { sendChatMessage, getIntegrations, triggerSync };