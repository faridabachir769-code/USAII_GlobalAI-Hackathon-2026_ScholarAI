import api from "../lib/axios";

// Dashboard recommendations
export const getRecommendedSchemes = async () => {
  const response = await api.get("/schemes/recommended");
  return response.data;
};

// Get all schemes
export const getSchemes = async (params) => {
  const response = await api.get("/schemes", {
    params,
  });

  return response.data;
};

// Get one scheme
export const getScheme = async (id) => {
  const response = await api.get(`/schemes/${id}`);
  return response.data;
};

// Compare selected schemes
export const compareSchemes = async (schemeIds) => {
  const response = await api.post("/schemes/compare", {
    scheme_ids: schemeIds,
  });

  return response.data;
};

// What-if simulation
export const simulateSchemes = async (payload) => {
  const response = await api.post("/schemes/simulate", payload);
  return response.data;
};