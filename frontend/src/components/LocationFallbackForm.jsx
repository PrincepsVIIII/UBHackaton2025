import { useState } from "react";
import PropTypes from "prop-types";

import { geocodeAddress } from "../api/requests.js";

function LocationFallbackForm({ onLocationResolved, defaultLat, defaultLng, onError }) {
  const [address, setAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [manualLat, setManualLat] = useState(defaultLat);
  const [manualLng, setManualLng] = useState(defaultLng);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!address.trim()) {
      onError("Please enter an address.");
      return;
    }

    setIsLoading(true);
    try {
      const coords = await geocodeAddress(address);
      if (!coords) {
        onError("Unable to locate that address. Please try again or adjust input.");
        return;
      }
      onLocationResolved(coords);
      onError(null);
    } catch (err) {
      onError(err.message || "Unable to geocode address.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualSubmit = (event) => {
    event.preventDefault();
    if (!Number.isFinite(manualLat) || !Number.isFinite(manualLng)) {
      onError("Enter both latitude and longitude.");
      return;
    }
    onLocationResolved({ lat: manualLat, lng: manualLng });
    onError(null);
  };

  return (
    <div className="fallback-form-wrapper">
      <h3>Location needed</h3>
      <p className="fallback-instructions">
        We couldn&apos;t detect your position. Enter your address or coordinates to center the map.
      </p>

      <form onSubmit={handleSubmit} className="fallback-form fallback-form--address">
        <label>
          Address
          <input
            type="text"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            placeholder="123 Main St, Buffalo NY"
          />
        </label>
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Locating…" : "Use Address"}
        </button>
      </form>

      <form onSubmit={handleManualSubmit} className="fallback-form fallback-form--coords">
        <label>
          Latitude
          <input
            type="number"
            step="0.0001"
            value={manualLat}
            onChange={(event) => setManualLat(parseFloat(event.target.value))}
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            step="0.0001"
            value={manualLng}
            onChange={(event) => setManualLng(parseFloat(event.target.value))}
          />
        </label>
        <button type="submit">Use Coordinates</button>
      </form>
    </div>
  );
}

LocationFallbackForm.propTypes = {
  onLocationResolved: PropTypes.func.isRequired,
  defaultLat: PropTypes.number.isRequired,
  defaultLng: PropTypes.number.isRequired,
  onError: PropTypes.func.isRequired,
};

export default LocationFallbackForm;

