import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail || error?.message || "Request failed.";
    return Promise.reject(new Error(message));
  }
);

export async function fetchOpenRequests({ token, lat, lng }) {
  const response = await client.get("/requests/open", {
    params: {
      volunteer_lat: lat,
      volunteer_lng: lng,
    },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}

export async function claimRequest({ token, requestId }) {
  const response = await client.post(
    `/requests/${requestId}/claim`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

// NOTE: To swap Leaflet for Google Maps, keep API utilities like this intact.
// Only the presentation layer in components would change to use Google Maps
// SDK widgets while reusing the same network calls above.

export async function geocodeAddress(address) {
  const params = new URLSearchParams({
    format: "json",
    q: address,
    limit: "1",
  });

  const response = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`, {
    headers: {
      "Accept-Language": "en",
    },
  });

  if (!response.ok) {
    throw new Error("Geocoding service unavailable.");
  }

  const data = await response.json();
  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const [first] = data;
  return {
    lat: parseFloat(first.lat),
    lng: parseFloat(first.lon),
  };
}

