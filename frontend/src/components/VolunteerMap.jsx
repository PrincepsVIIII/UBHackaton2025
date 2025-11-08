import { useEffect, useMemo, useState, useCallback } from "react";
import PropTypes from "prop-types";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";

import { fetchOpenRequests, claimRequest } from "../api/requests.js";
import RequestPopup from "./RequestPopup.jsx";
import ScoreLegend from "./ScoreLegend.jsx";
import LocationFallbackForm from "./LocationFallbackForm.jsx";

const SCORE_THRESHOLDS = {
  high: 1.0,
  medium: 0.5,
};

const DEFAULT_POSITION = {
  lat: 42.8864, // Buffalo, NY
  lng: -78.8784,
};

const AUTH_TOKEN_KEY = "volunteerAuthToken";

function createMarkerIcon(score) {
  let level = "low";
  if (score >= SCORE_THRESHOLDS.high) {
    level = "high";
  } else if (score >= SCORE_THRESHOLDS.medium) {
    level = "medium";
  }

  return L.divIcon({
    className: `request-marker request-marker--${level}`,
    html: `<span></span>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function useVolunteerLocation(setGeoError) {
  const [position, setPosition] = useState(null);
  const [isGeolocating, setIsGeolocating] = useState(true);

  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setGeoError("Geolocation is not supported by this browser.");
      setIsGeolocating(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
        setIsGeolocating(false);
        setGeoError(null);
      },
      (err) => {
        console.warn("Geolocation fallback used:", err);
        setGeoError("Unable to retrieve location automatically. Please enter it manually.");
        setIsGeolocating(false);
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 },
    );
  }, [setGeoError]);

  return { position, setPosition, isGeolocating };
}

function calculateDistanceKm(origin, destination) {
  if (!origin || !destination) return null;
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371;

  const dLat = toRad(destination.lat - origin.lat);
  const dLon = toRad(destination.lng - origin.lng);

  const lat1 = toRad(origin.lat);
  const lat2 = toRad(destination.lat);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

function MapViewUpdater({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
}

MapViewUpdater.propTypes = {
  center: PropTypes.shape({
    lat: PropTypes.number.isRequired,
    lng: PropTypes.number.isRequired,
  }),
};

function VolunteerMap() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState(null);
  const [claimErrors, setClaimErrors] = useState({});
  const [inFlightClaims, setInFlightClaims] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [manualLocation, setManualLocation] = useState(DEFAULT_POSITION);
  const [manualDraft, setManualDraft] = useState(DEFAULT_POSITION);
  const [isClaiming, setIsClaiming] = useState(false);
  const [geoError, setGeoError] = useState(null);
  const { position, setPosition, isGeolocating } = useVolunteerLocation(setGeoError);

  const token = useMemo(() => {
    // Replace this with a more secure storage strategy before production.
    return localStorage.getItem(AUTH_TOKEN_KEY) ?? "";
  }, []);

  useEffect(() => {
    if (position) {
      setManualDraft({
        lat: position.lat,
        lng: position.lng,
      });
    }
  }, [position]);

  const currentCenter = position ?? manualLocation;

  const loadRequests = useCallback(
    async (coords) => {
      if (!coords) return;
      setIsLoading(true);
      try {
        const data = await fetchOpenRequests({
          token,
          lat: coords.lat,
          lng: coords.lng,
        });

        const enriched = data.map((entry) => ({
          ...entry,
          distanceKm: calculateDistanceKm(coords, {
            lat: entry.request.lat,
            lng: entry.request.lng,
          }),
        }));
        setRequests(enriched);
        setError(null);
        setClaimErrors({});
      } catch (err) {
        console.error(err);
        setError(err.message || "Unable to load requests.");
      } finally {
        setIsLoading(false);
      }
    },
    [token],
  );

  useEffect(() => {
    if (!token) {
      setError("Missing volunteer token. Please authenticate.");
      return;
    }

    const fetchLatest = () => {
      const coords = position ?? manualLocation;
      loadRequests(coords);
    };

    fetchLatest();

    const intervalId = setInterval(fetchLatest, 30000);

    return () => clearInterval(intervalId);
  }, [loadRequests, manualLocation, position, token]);

  const handleManualLocationSubmit = (event) => {
    event.preventDefault();
    if (!Number.isFinite(manualDraft.lat) || !Number.isFinite(manualDraft.lng)) {
      setError("Please provide both latitude and longitude.");
      return;
    }
    const nextLocation = {
      lat: manualDraft.lat,
      lng: manualDraft.lng,
    };
    setManualLocation(nextLocation);
    setPosition(nextLocation);
    setError(null);
  };

  const handleClaim = async (requestId) => {
    if (!token) return;

    const target = requests.find((entry) => entry.request.id === requestId);
    if (!target) {
      return;
    }

    setRequests((prev) => prev.filter((entry) => entry.request.id !== requestId));
    setInFlightClaims((prev) => [...prev, requestId]);
    setIsClaiming(true);

    try {
      await claimRequest({ token, requestId });
      setClaimErrors((prev) => {
        const { [requestId]: _discarded, ...rest } = prev;
        return rest;
      });
    } catch (err) {
      setRequests((prev) => [target, ...prev]);
      setClaimErrors((prev) => ({
        ...prev,
        [requestId]: err.message || "Unable to claim request.",
      }));
    } finally {
      setInFlightClaims((prev) => prev.filter((id) => id !== requestId));
      setIsClaiming(false);
    }
  };

  return (
    <div className="map-layout">
      <section className="location-panel">
        <h2>Your location</h2>
        {isGeolocating && <p>Detecting your location…</p>}
        {!isGeolocating && position && (
          <>
            <p>
              Current center: {currentCenter.lat.toFixed(4)}, {currentCenter.lng.toFixed(4)}
            </p>
            <p className="location-note">
              Drag the map or adjust coordinates below to fine-tune your search radius.
            </p>
            <form onSubmit={handleManualLocationSubmit} className="location-form">
              <label>
                Latitude
                <input
                  type="number"
                  step="0.0001"
                  value={manualDraft.lat}
                  onChange={(e) =>
                    setManualDraft((prev) => ({
                      ...prev,
                      lat: parseFloat(e.target.value),
                    }))
                  }
                />
              </label>
              <label>
                Longitude
                <input
                  type="number"
                  step="0.0001"
                  value={manualDraft.lng}
                  onChange={(e) =>
                    setManualDraft((prev) => ({
                      ...prev,
                      lng: parseFloat(e.target.value),
                    }))
                  }
                />
              </label>
              <button type="submit">Update Location</button>
            </form>
          </>
        )}
        {geoError && <p className="error-text">{geoError}</p>}
        {error && <p className="error-text">{error}</p>}
        {geoError && !position && (
          <LocationFallbackForm
            onLocationResolved={(coords) => {
              setManualLocation(coords);
              setManualDraft(coords);
              setPosition(coords);
              setGeoError(null);
              setError(null);
            }}
            defaultLat={manualDraft.lat}
            defaultLng={manualDraft.lng}
            onError={setError}
          />
        )}
      </section>

      <section className="map-section">
        {/* Swap MapContainer with Google Maps SDK components here if needed later. */}
        <MapContainer center={currentCenter} zoom={13} scrollWheelZoom className="map-container">
          <MapViewUpdater center={currentCenter} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {requests.map(({ request, score, distanceKm }) => (
            <Marker
              key={request.id}
              position={[request.lat, request.lng]}
              icon={createMarkerIcon(score)}
            >
              <Popup>
                <RequestPopup
                  request={request}
                  score={score}
                  distanceKm={distanceKm}
                  onClaim={() => handleClaim(request.id)}
                  isClaiming={inFlightClaims.includes(request.id) || isClaiming}
                  errorMessage={claimErrors[request.id]}
                />
              </Popup>
            </Marker>
          ))}
        </MapContainer>
        <ScoreLegend />
        {isLoading && (
          <div className="loading-overlay" role="status" aria-live="polite">
            <span className="spinner" aria-hidden="true" />
            Refreshing requests…
          </div>
        )}
      </section>
    </div>
  );
}

export default VolunteerMap;

