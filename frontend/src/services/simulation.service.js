import api from "../lib/axios";

export const simulateScenario = async (payload) => {
  const response = await api.post("/schemes/simulate", payload);
  return response.data;
};
