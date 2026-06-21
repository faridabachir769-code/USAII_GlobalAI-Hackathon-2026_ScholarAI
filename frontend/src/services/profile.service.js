import api from "../lib/axios";

export const createProfile = async (data) => {
  const response = await api.post(
    "/profile",
    data
  );

  return response.data;
};

export const getProfile = async () => {
  const response = await api.get("/profile");

  return response.data;
};

export const updateProfile = async (
  data
) => {
  const response = await api.put(
    "/profile",
    data
  );

  return response.data;
};