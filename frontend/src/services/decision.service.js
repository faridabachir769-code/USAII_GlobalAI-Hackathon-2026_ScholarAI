import api from "../lib/axios";

export const generateDecisionReport =
  async (payload) => {
    const response = await api.post(
      "/decision-report",
      payload
    );

    return response.data;
  };