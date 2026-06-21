import api from "../lib/axios";

export const sendChatMessage = async (query) => {
  const response = await api.post("/chat", { query });
  return response.data;
};

export const getChatHistory = async () => {
  const response = await api.get("/chat/history");
  return response.data;
};
